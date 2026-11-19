"""Step 2: validate and clean the uploaded CSV."""
from __future__ import annotations

import io

import pandas as pd

from .schemas import REQUIRED_COLUMNS


class CsvValidationError(ValueError):
    """Raised when the file cannot be used at all."""


def load_and_validate(source) -> tuple[pd.DataFrame, list[str]]:
    """Return (clean dataframe, human-readable warnings). `source` is a path or file-like object."""
    try:
        if hasattr(source, "read"):
            if hasattr(source, "seek"):
                source.seek(0)
            raw = source.read()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8-sig")
            df = pd.read_csv(io.StringIO(raw), dtype=str, keep_default_na=False)
        else:
            df = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except Exception as exc:  # noqa: BLE001 - surface any parse problem as one clear error
        raise CsvValidationError(f"Could not read the CSV: {exc}") from exc

    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CsvValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected: {', '.join(REQUIRED_COLUMNS)}."
        )

    warnings: list[str] = []
    df = df[list(REQUIRED_COLUMNS)].copy()
    for col in df.columns:
        df[col] = df[col].str.strip()

    before = len(df)
    df = df[df["review_text"] != ""]
    if before - len(df):
        warnings.append(f"Dropped {before - len(df)} row(s) with empty review_text.")

    before = len(df)
    df = df[df["review_id"] != ""]
    df = df.drop_duplicates(subset="review_id", keep="first")
    if before - len(df):
        warnings.append(f"Dropped {before - len(df)} row(s) with missing or duplicate review_id.")

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    bad_rating = int(df["rating"].isna().sum())
    if bad_rating:
        warnings.append(f"{bad_rating} row(s) have a non-numeric rating (kept, rating left blank).")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_date = int(df["date"].isna().sum())
    if bad_date:
        warnings.append(f"{bad_date} row(s) have an unreadable date (kept).")

    if df.empty:
        raise CsvValidationError("No usable rows left after cleaning.")
    return df.reset_index(drop=True), warnings


def load_many(sources: list[tuple[str, object]]) -> tuple[pd.DataFrame, list[str]]:
    """Load several CSVs (label, path-or-file) into ONE dataframe with a `source_file` column.

    A file that fails validation is skipped with a warning; if every file fails, raise.
    A review_id that appears in more than one file is kept once (first file wins).
    """
    frames: list[pd.DataFrame] = []
    warnings: list[str] = []
    for label, src in sources:
        try:
            df, warns = load_and_validate(src)
        except CsvValidationError as exc:
            warnings.append(f"{label}: skipped. {exc}")
            continue
        df.insert(0, "source_file", label)
        frames.append(df)
        warnings.extend(f"{label}: {w}" for w in warns)
    if not frames:
        raise CsvValidationError("None of the files could be used. " + " ".join(warnings))

    merged = pd.concat(frames, ignore_index=True)
    dupes = int(merged.duplicated(subset="review_id", keep="first").sum())
    if dupes:
        merged = merged.drop_duplicates(subset="review_id", keep="first")
        warnings.append(f"{dupes} review(s) repeated the same review_id across files; kept the first.")
    return merged.reset_index(drop=True), warnings
