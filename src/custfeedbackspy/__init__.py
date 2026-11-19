"""CustFeedbackSpy (ReviewLens): turn raw customer reviews into tagged insights."""
from .aggregate import compute_stats
from .chains import build_analysis_chain, build_batch_chain, build_report_chain
from .classifier import classify_reviews
from .config import load_settings
from .export import to_csv_bytes
from .report import generate_report
from .validation import CsvValidationError, load_and_validate, load_many

__all__ = [
    "compute_stats", "build_analysis_chain", "build_batch_chain", "build_report_chain", "classify_reviews",
    "load_settings", "to_csv_bytes", "generate_report", "CsvValidationError", "load_and_validate", "load_many",
]
