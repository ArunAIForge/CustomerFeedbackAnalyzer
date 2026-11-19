"""Step 6: Excel-friendly CSV export."""
from __future__ import annotations

import pandas as pd

EXPORT_COLUMNS = [
    "source_file",
    "review_id", "date", "platform", "rating", "review_text", "sentiment", "category",
    "urgency", "language", "summary", "suggested_reply", "needs_review",
]


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """UTF-8 with BOM so Excel shows Tamil text correctly."""
    out = df[[c for c in EXPORT_COLUMNS if c in df.columns]].copy()
    if "date" in out:
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False).encode("utf-8-sig")
