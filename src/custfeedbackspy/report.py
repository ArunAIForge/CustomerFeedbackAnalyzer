"""Step 5 (reduce): one report chain writes the narrative; code supplies all the numbers."""
from __future__ import annotations

import pandas as pd
from langchain_core.runnables import Runnable

from .aggregate import Stats, compute_stats
from .schemas import ReportNarrative, Theme


def _review_lines(df: pd.DataFrame, cap: int) -> str:
    """Compact one-line-per-review view. If too many, keep urgent and negative first."""
    rank = {"high": 0, "medium": 1, "low": 2}
    d = df.assign(_r=df["urgency"].map(rank), _neg=(df["sentiment"] != "negative"))
    d = d.sort_values(["_r", "_neg"]).head(cap)
    return "\n".join(
        f"{r.review_id} | {r.platform} | {r.sentiment} | {r.category} | {r.urgency} | {r.summary}"
        for r in d.itertuples()
    )


def build_narrative(df: pd.DataFrame, chain: Runnable, stats: Stats, cap: int = 400) -> ReportNarrative:
    ok = df[~df["needs_review"]] if "needs_review" in df else df
    return chain.invoke({"urgent_count": stats.urgent_count, "review_lines": _review_lines(ok, cap)})


def _verified(theme: Theme, df: pd.DataFrame) -> tuple[int, str]:
    """Count only ids that really exist: protects against hallucinated ids."""
    sub = df[df["review_id"].isin(set(theme.review_ids))]
    platforms = sub["platform"].value_counts()
    where = ""
    if len(sub) and platforms.iloc[0] / len(sub) > 0.5:
        where = f"  (mostly {platforms.index[0]})"
    return len(sub), where


def _fmt_date(ts: pd.Timestamp | None, with_year: bool) -> str:
    if ts is None or pd.isna(ts):
        return "?"
    return f"{ts.day} {ts.strftime('%b')}" + (f" {ts.year}" if with_year else "")


def render_report(df: pd.DataFrame, stats: Stats, narrative: ReportNarrative) -> str:
    period = f"{_fmt_date(stats.date_from, False)} to {_fmt_date(stats.date_to, True)}"
    p = stats.sentiment_pct
    lines = [
        f"WEEKLY FEEDBACK REPORT  |  {period}",
        f"Total reviews: {stats.total}   Positive {p['positive']}%   "
        f"Neutral {p['neutral']}%   Negative {p['negative']}%",
        "",
        "TOP 3 COMPLAINTS",
    ]
    rows = [(t, *_verified(t, df)) for t in narrative.top_complaints]
    rows = sorted([r for r in rows if r[1] > 0], key=lambda r: r[1], reverse=True)[:3]
    for i, (t, n, where) in enumerate(rows, 1):
        lines.append(f"  {i}. {t.label} ... {n} reviews{where}")
    if not rows:
        lines.append("  No recurring complaints found.")
    lines += ["", "TOP PRAISE"]
    praise = [(t, *_verified(t, df)) for t in narrative.top_praises]
    praise = sorted([r for r in praise if r[1] > 0], key=lambda r: r[1], reverse=True)[:3]
    lines.append("  " + (", ".join(f"{t.label} ({n} mentions)" for t, n, _ in praise) or "None"))
    lines += ["", f"URGENT: {stats.urgent_count} reviews need a reply within 24 hours"]
    if stats.needs_review_count:
        lines.append(f"NOTE: {stats.needs_review_count} review(s) could not be analysed and need manual review")
    lines += ["", "ACTION ITEMS"]
    lines += [f"  {i}. {a}" for i, a in enumerate(narrative.action_items[:3], 1)]
    return "\n".join(lines)


def generate_report(df: pd.DataFrame, chain: Runnable, cap: int = 400) -> tuple[str, Stats]:
    stats = compute_stats(df)
    narrative = build_narrative(df, chain, stats, cap)
    return render_report(df, stats, narrative), stats
