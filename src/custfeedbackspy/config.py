"""Settings loaded from environment / .env. API keys are never hard-coded."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-5-5",
    "gemini": "gemini-2.5-flash",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",  # ':free' = no cost (rate-limited); names change, see openrouter.ai/models
    "groq": "openai/gpt-oss-120b",  # Groq (not Grok); free tier, fast. Model list: console.groq.com/docs/models
    "xai": "grok-3-mini",  # Grok via xAI; override with LLM_MODEL
    "mock": "keyword-heuristics",
}


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    temperature: float
    max_concurrency: int
    max_retries: int
    batch_size: int
    max_report_reviews: int
    structured_method: str = "function_calling"
    reviews_per_call: int = 8
    use_cache: bool = True


def load_settings() -> Settings:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"LLM_PROVIDER must be one of {sorted(DEFAULT_MODELS)}, got '{provider}'")
    model = os.getenv("LLM_MODEL", "").strip() or DEFAULT_MODELS[provider]
    # Groq's gpt-oss supports strict schema-constrained output: far fewer malformed-JSON failures
    default_method = "json_schema" if provider == "groq" and "gpt-oss" in model else "function_calling"
    return Settings(
        provider=provider,
        model=model,
        temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        max_concurrency=int(os.getenv("MAX_CONCURRENCY", "") or (2 if provider in ("groq", "openrouter") else 5)),  # free tiers rate-limit hard
        max_retries=int(os.getenv("MAX_RETRIES", "2")),
        batch_size=int(os.getenv("BATCH_SIZE", "20")),
        max_report_reviews=int(os.getenv("MAX_REPORT_REVIEWS", "400")),
        structured_method=os.getenv("STRUCTURED_METHOD", "").strip() or default_method,
        reviews_per_call=max(1, int(os.getenv("REVIEWS_PER_CALL", "8"))),
        use_cache=os.getenv("USE_CACHE", "true").strip().lower() not in ("0", "false", "no"),
    )
