# CLAUDE.md: CustFeedbackSpy

Context for AI coding assistants working on this repo.

## What this is
Streamlit + LangChain app: CSV of customer reviews → per-review structured analysis → pandas stats →
LLM-written weekly report → dashboard + CSV export. Brief: use case 01.

## Commands
- Run: `streamlit run app.py`
- Test: `python -m pytest -q` (offline, uses mock chain)
- Regenerate sample: `python sample_data/generate_sample.py`

## Architecture rules (do not break)
1. **Numbers come from pandas, never the LLM.** The report chain returns themes + review ids; code counts them.
2. **Structured output only**: `prompt | llm.with_structured_output(PydanticModel)`. No regex parsing of LLM text.
3. **Vendor isolation**: only `chains.py` imports a provider package. Everything else takes a `Runnable`.
4. Allowed values live in `schemas.py` (`Literal` types). Add a category there first, then update the prompt.
5. A failed review is retried, then flagged `needs_review`. The app never crashes on one bad review.
6. Secrets only in `.env` (git-ignored). Never hard-code keys.
7. Tests must stay offline: use `mock_llm.py` or `RunnableLambda`.

## Style
Python 3.11+, type hints, small modules (<150 lines), pydantic v2, no global state outside Streamlit session_state.
