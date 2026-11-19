"""Step 3 (map): classify every review fast, retry invalid ones, never crash.

Speed levers (in order of impact):
  1. cache     - a review already analysed with this model/prompt is not sent again;
  2. batching  - several reviews per LLM call (fixed prompt cost paid once, far fewer requests);
  3. concurrency - groups run in parallel up to `max_concurrency`.
Anything the batch call gets wrong (missing id, invalid value, API error) falls back to the
single-review chain with retries, then to a `needs_review` row.
"""
from __future__ import annotations

import logging
from typing import Callable

import pandas as pd
from langchain_core.runnables import Runnable

from .cache import AnalysisCache
from .schemas import AnalysedReview, BatchAnalysis, ReviewAnalysis

log = logging.getLogger(__name__)

ProgressFn = Callable[[int, int], None]


def _inputs(df: pd.DataFrame) -> list[dict]:
    return [
        {
            "platform": r.platform,
            "rating": "n/a" if pd.isna(r.rating) else r.rating,
            "review_text": " ".join(str(r.review_text).split()),
        }
        for r in df.itertuples()
    ]


def _fallback(review_id: str) -> AnalysedReview:
    """Used only after all retries failed: flagged so a human looks at it."""
    return AnalysedReview(
        review_id=review_id, sentiment="neutral", category="food_quality", urgency="medium",
        language="Other", summary="Needs manual review: automatic analysis failed.",
        suggested_reply="", needs_review=True,
    )


def _wrap(review_id: str, result: ReviewAnalysis) -> AnalysedReview:
    return AnalysedReview(review_id=review_id, **result.model_dump(exclude={"review_id"}))


def _single(chain: Runnable, inp: dict, review_id: str, max_retries: int, first=None) -> tuple[AnalysedReview, bool]:
    """Analyse ONE review with retries. Returns (row, succeeded)."""
    out = first
    for attempt in range(max_retries + 1):
        if out is None or attempt > 0:
            try:
                out = chain.invoke(inp)
            except Exception as exc:  # noqa: BLE001
                out = exc
        if isinstance(out, dict):  # some providers return a raw dict
            try:
                out = ReviewAnalysis.model_validate(out)
            except Exception as exc:  # noqa: BLE001
                out = exc
        if isinstance(out, ReviewAnalysis):
            return _wrap(review_id, out), True
        log.warning("Review %s attempt %d failed: %s", review_id, attempt + 1, out)
    return _fallback(review_id), False


def _batch_text(group: list[tuple[str, dict]]) -> str:
    return "\n".join(f"{rid} | {i['platform']} | {i['rating']} | {i['review_text']}" for rid, i in group)


def classify_reviews(
    df: pd.DataFrame,
    chain: Runnable,
    *,
    batch_chain: Runnable | None = None,
    reviews_per_call: int = 8,
    cache: AnalysisCache | None = None,
    max_concurrency: int = 5,
    max_retries: int = 2,
    batch_size: int = 20,
    progress: ProgressFn | None = None,
) -> pd.DataFrame:
    """Return df + the 6 analysis fields (+ needs_review flag)."""
    inputs = _inputs(df)
    ids = df["review_id"].tolist()
    total = len(df)
    results: dict[str, AnalysedReview] = {}

    # 1) cache
    todo: list[tuple[str, dict]] = []
    for rid, inp in zip(ids, inputs):
        hit = cache.get(inp) if cache else None
        if hit is not None:
            results[rid] = _wrap(rid, hit)
        else:
            todo.append((rid, inp))
    # 1b) identical reviews (same stars + text) are analysed once and the answer is shared
    groups_by_key: dict[tuple, list[tuple[str, dict]]] = {}
    for rid, inp in todo:
        groups_by_key.setdefault((str(inp["rating"]), inp["review_text"]), []).append((rid, inp))
    followers = {v[0][0]: [r for r, _ in v[1:]] for v in groups_by_key.values()}
    todo = [v[0] for v in groups_by_key.values()]
    done = len(results)
    if progress and done:
        progress(done, total)

    def record(rid: str, inp: dict, row: AnalysedReview, ok: bool) -> None:
        nonlocal done
        results[rid] = row
        for fid in followers.get(rid, []):
            results[fid] = row.model_copy(update={"review_id": fid})
            done += 1
        if ok and cache:
            cache.put(inp, ReviewAnalysis.model_validate(row.model_dump(exclude={"review_id", "needs_review"})))
        done += 1

    cfg = {"max_concurrency": max_concurrency}
    if batch_chain is not None and reviews_per_call > 1:
        # 2) batching: groups of N reviews per call, several groups in flight at once
        groups = [todo[i : i + reviews_per_call] for i in range(0, len(todo), reviews_per_call)]
        window = max(1, max_concurrency) * 2
        for w in range(0, len(groups), window):
            chunk = groups[w : w + window]
            outs = batch_chain.batch([{"reviews": _batch_text(g)} for g in chunk], config=cfg, return_exceptions=True)
            final = []
            retry_groups: list[list[tuple[str, dict]]] = []
            for group, out in zip(chunk, outs):
                if isinstance(out, BatchAnalysis) or len(group) < 2:
                    final.append((group, out))
                else:  # call failed outright (e.g. malformed JSON): retry once as two half-size batches
                    log.warning("Batch call failed (%s); retrying as two smaller batches.", out)
                    mid = len(group) // 2
                    retry_groups += [group[:mid], group[mid:]]
            if retry_groups:
                r_outs = batch_chain.batch([{"reviews": _batch_text(g)} for g in retry_groups],
                                           config=cfg, return_exceptions=True)
                final += list(zip(retry_groups, r_outs))
            for group, out in final:
                by_id = {it.review_id.strip(): it for it in out.results} if isinstance(out, BatchAnalysis) else {}
                for rid, inp in group:
                    item = by_id.get(rid)
                    if item is not None:
                        record(rid, inp, _wrap(rid, item), True)
                    else:  # missing from the batch answer -> single-review path
                        row, ok = _single(chain, inp, rid, max_retries)
                        record(rid, inp, row, ok)
            if progress:
                progress(min(done, total), total)
    else:
        for start in range(0, len(todo), batch_size):
            chunk = todo[start : start + batch_size]
            outs = chain.batch([i for _, i in chunk], config=cfg, return_exceptions=True)
            for (rid, inp), out in zip(chunk, outs):
                row, ok = _single(chain, inp, rid, max_retries, first=out)
                record(rid, inp, row, ok)
            if progress:
                progress(min(done, total), total)

    if cache:
        cache.save()
    analysed = pd.DataFrame([results[r].model_dump() for r in ids])
    return df.merge(analysed, on="review_id", how="left")
