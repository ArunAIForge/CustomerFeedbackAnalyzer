"""Step 4: every number in the app comes from pandas, never from the LLM."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .schemas import CATEGORIES, SENTIMENTS, URGENCIES


@dataclass
class Stats:
    total: int
    sentiment_counts: dict[str, int]
    sentiment_pct: dict[str, int]
    category_counts: dict[str, int]
    urgency_counts: dict[str, int]
    urgent_count: int
    needs_review_count: int
    date_from: pd.Timestamp | None
    date_to: pd.Timestamp | None


def _counts(series: pd.Series, order: tuple[str, ...]) -> dict[str, int]:
    vc = series.value_counts()
    return {k: int(vc.get(k, 0)) for k in order}


def compute_stats(df: pd.DataFrame) -> Stats:
    total = len(df)
    sent = _counts(df["sentiment"], SENTIMENTS)
    pct = {k: round(100 * v / total) if total else 0 for k, v in sent.items()}
    urg = _counts(df["urgency"], URGENCIES)
    dates = df["date"].dropna()
    return Stats(
        total=total,
        sentiment_counts=sent,
        sentiment_pct=pct,
        category_counts=_counts(df["category"], CATEGORIES),
        urgency_counts=urg,
        urgent_count=urg["high"],
        needs_review_count=int(df["needs_review"].sum()) if "needs_review" in df else 0,
        date_from=dates.min() if len(dates) else None,
        date_to=dates.max() if len(dates) else None,
    )
