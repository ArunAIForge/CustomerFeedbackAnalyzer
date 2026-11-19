"""Build the two LCEL chains. Only this file knows which LLM vendor is used."""
from __future__ import annotations

import os

from langchain_core.runnables import Runnable

from .config import Settings
from .mock_llm import mock_analysis_chain, mock_report_chain
from .prompts import analysis_prompt, batch_prompt, report_prompt
from .schemas import BatchAnalysis, ReportNarrative, ReviewAnalysis

_KEY_VARS = {
    "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY", "xai": "XAI_API_KEY", "groq": "GROQ_API_KEY",
}
# OpenAI-compatible services: same client, different base URL + key.
_BASE_URLS = {"openrouter": "https://openrouter.ai/api/v1", "xai": "https://api.x.ai/v1",
              "groq": "https://api.groq.com/openai/v1"}


def _chat_model(s: Settings):
    key_var = _KEY_VARS[s.provider]
    if not os.getenv(key_var):
        raise RuntimeError(f"{key_var} is not set. Add it to your .env file (see .env.example).")
    if s.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=s.model, temperature=s.temperature)
    if s.provider in _BASE_URLS:
        from langchain_openai import ChatOpenAI

        extra = {"reasoning_effort": "low"} if "gpt-oss" in s.model else {}  # reasoning tokens eat rate limits
        return ChatOpenAI(model=s.model, temperature=s.temperature, base_url=_BASE_URLS[s.provider],
                          api_key=os.environ[key_var], max_retries=4, **extra)
    if s.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=s.model, temperature=s.temperature)
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=s.model, temperature=s.temperature)


def _structured(s: Settings, schema):
    llm = _chat_model(s)
    if s.provider in _BASE_URLS:  # non-OpenAI backends: be explicit about how to get structured output
        return llm.with_structured_output(schema, method=s.structured_method)
    return llm.with_structured_output(schema)


def build_analysis_chain(s: Settings) -> Runnable:
    """{platform, rating, review_text} -> ReviewAnalysis"""
    if s.provider == "mock":
        return mock_analysis_chain()
    return analysis_prompt | _structured(s, ReviewAnalysis)


def build_batch_chain(s: Settings) -> Runnable | None:
    """{reviews: 'id | platform | stars | text' lines} -> BatchAnalysis. None when batching is off/unneeded."""
    if s.provider == "mock" or s.reviews_per_call <= 1:
        return None
    return batch_prompt | _structured(s, BatchAnalysis)


def build_report_chain(s: Settings) -> Runnable:
    """{urgent_count, review_lines} -> ReportNarrative"""
    if s.provider == "mock":
        return mock_report_chain()
    return report_prompt | _structured(s, ReportNarrative)


LABELS = {"mock": "Mock (offline)", "openrouter": "OpenRouter", "groq": "Groq", "xai": "Grok (xAI)",
          "openai": "OpenAI", "anthropic": "Claude (Anthropic)", "gemini": "Gemini (Google)"}


SIDEBAR_PROVIDERS = ("openai", "groq", "openrouter", "mock")  # shown in the sidebar list


def provider_status(active_provider: str, active_model: str) -> list[dict]:
    """One row per supported model: is its API key present, and is it the active one?"""
    from .config import DEFAULT_MODELS

    rows = []
    for prov, default_model in DEFAULT_MODELS.items():
        if prov not in SIDEBAR_PROVIDERS:
            continue
        key_var = _KEY_VARS.get(prov)
        rows.append({
            "provider": prov, "label": LABELS[prov],
            "model": active_model if prov == active_provider else default_model,
            "ready": key_var is None or bool(os.getenv(key_var)),  # mock needs no key
            "active": prov == active_provider,
        })
    return rows
