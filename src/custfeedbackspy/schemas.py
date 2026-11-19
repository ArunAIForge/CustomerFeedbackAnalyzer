"""Typed contracts shared by every part of the app."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]
Category = Literal["food_quality", "delivery", "price", "staff", "packaging", "app"]
Urgency = Literal["low", "medium", "high"]

SENTIMENTS: tuple[str, ...] = ("positive", "neutral", "negative")
CATEGORIES: tuple[str, ...] = ("food_quality", "delivery", "price", "staff", "packaging", "app")
URGENCIES: tuple[str, ...] = ("low", "medium", "high")

REQUIRED_COLUMNS: tuple[str, ...] = ("review_id", "date", "platform", "rating", "review_text")


class ReviewAnalysis(BaseModel):
    """What the per-review chain must return (the 'map' step)."""

    sentiment: Sentiment = Field(description="Overall customer mood.")
    category: Category = Field(description="Which department must act on this review.")
    urgency: Urgency = Field(
        description="high = reply today (health, refund, abuse, wrong order); "
        "medium = clear complaint; low = praise or minor remark."
    )
    language: str = Field(description="Language of the review: English, Tamil, Tanglish or Other.")
    summary: str = Field(description="ONE English sentence, even for Tamil/Tanglish reviews.")
    suggested_reply: str = Field(description="Polite, ready-to-post reply (2-3 sentences, English).")


class BatchItem(ReviewAnalysis):
    review_id: str = Field(description="The review id, copied EXACTLY from the input line.")


class BatchAnalysis(BaseModel):
    """Several reviews analysed in ONE call (cheaper and faster than one call each)."""

    results: list[BatchItem] = Field(description="Exactly one item per input review, in the same order.")


class Theme(BaseModel):
    label: str = Field(description="Short theme name, e.g. 'Late delivery'.")
    review_ids: list[str] = Field(description="IDs (copied exactly from the input) of reviews in this theme.")


class ReportNarrative(BaseModel):
    """What the report chain must return (the 'reduce' step). Counts are NOT asked of the LLM."""

    top_complaints: list[Theme] = Field(description="Up to 3 most common complaint themes.")
    top_praises: list[Theme] = Field(description="Up to 3 most common praise themes.")
    action_items: list[str] = Field(description="Exactly 3 concrete, practical action items.")


class AnalysedReview(ReviewAnalysis):
    """A review row after analysis (6 fields + id + provenance)."""

    review_id: str
    needs_review: bool = False
