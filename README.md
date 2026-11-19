# Customer Feedback Analyzer

Turn hundreds of raw customer reviews (English, Tamil, Tanglish) into tagged, prioritised insights
and a weekly report a manager can read in five minutes. Project 1 (Gen AI / LangChain) of an
AI Academy intermediate track.

## What it does

1. Upload a CSV (`review_id, date, platform, rating, review_text`).
2. **Validate**: check columns, drop empty / duplicate rows.
3. **Classify (map)**: a LangChain LCEL chain (`prompt | llm.with_structured_output(ReviewAnalysis)`)
   returns `sentiment, category, urgency, language, summary, suggested_reply` for every review,
   run with `chain.batch(max_concurrency=...)`. Invalid output is retried, then flagged `needs_review`.
4. **Aggregate**: all counts and percentages are computed in **pandas**, never by the LLM.
5. **Report (reduce)**: a second chain names complaint/praise themes and 3 action items; the code
   counts the reviews behind each theme (hallucinated ids are ignored).
6. **Show + export**: interactive Streamlit dashboard, filters, HIGH-urgency toggle, Excel-friendly CSV download.

**Multiple files:** upload several CSVs at once (and/or pick bundled samples in the sidebar). They are merged
into one analysis; each row keeps a `source_file` column. A bad file is skipped with a warning. If the same
`review_id` appears in two files, the first one is kept (use unique ids per file).

**UI:** gradient hero and metric cards with hover-lift and shadows, hover-highlight charts (donut, category,
sentiment-by-file, urgency-by-platform), filterable review cards (sentiment / category / urgency / file / text
search) with a Cards or Table view, and a gradient-framed weekly report. While analysing, a full-screen loading overlay shows live progress
("Classified 12 of 40 reviews"). Styling lives in `src/custfeedbackspy/ui.py`; the tab title and icon come from
`app.py` + `assets/favicon.png`.

## Quick start (Windows): one command, from any folder

```powershell
powershell -ExecutionPolicy Bypass -File ./run.ps1
```
It creates/uses a Python 3.12 environment, installs requirements on first run, and starts the app.
`Error: File does not exist: app.py` means your terminal is not inside `CustFeedbackSpy`: `cd` into it first.

## Run it locally (Windows PowerShell; macOS/Linux commands in brackets)

Requirements: **Python 3.11 or 3.12** (tested on 3.12; 3.14 hit blocked-binary problems on a locked-down PC).

```powershell
cd CustFeedbackSpy
py -3.12 -m venv .venv                # [python3.12 -m venv .venv]
.\.venv\Scripts\Activate.ps1          # [source .venv/bin/activate]
pip install -r requirements.txt
copy .env.example .env                # [cp .env.example .env]
streamlit run app.py
```

Open http://localhost:8501, pick a file under **Bundled samples** in the sidebar (or upload your own), click **Analyse reviews**.

### Choose the LLM (edit `.env`)

The sidebar **Models** list shows OpenAI, Groq, OpenRouter and Mock (green dot = API key found). Other
providers (xAI, Anthropic, Gemini) still work via `.env` but are not listed.

| Goal | `.env` |
|---|---|
| Try it with no key (offline keyword rules, not a real LLM) | `LLM_PROVIDER=mock` (default) |
| Groq (free tier, fast) | `LLM_PROVIDER=groq` and `GROQ_API_KEY=gsk_...` (default `openai/gpt-oss-120b`; get a key at console.groq.com) |
| OpenRouter (has free models) | `LLM_PROVIDER=openrouter` and `OPENROUTER_API_KEY=sk-or-...` (default model is a `:free` one; set `LLM_MODEL` to change) |
| Grok (xAI) | `LLM_PROVIDER=xai` and `XAI_API_KEY=xai-...` (default `grok-3-mini`) |
| OpenAI | `LLM_PROVIDER=openai` and `OPENAI_API_KEY=sk-...` |
| Claude | `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...` |
| Gemini | `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY=...` |

Optionally set `LLM_MODEL` to override the default model. Restart Streamlit after editing `.env`.
Free-tier note: OpenRouter `:free` models cost nothing but are rate-limited, so lower `MAX_CONCURRENCY` to 1-2 and
`BATCH_SIZE` to ~10 if you see 429 errors; some free models don't support tool calls, so try another `:free` model or
set `STRUCTURED_METHOD=json_mode`. Grok normally needs credits on your xAI account. The `mock` provider is always free.
Swapping providers changes nothing else: only `chains.py` knows the vendor.

### Run the tests

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```
Tests use the offline mock chain, so they need no API key and cost nothing.

### Sample CSVs (`sample_data/`)
| File | Rows | Use |
|---|---|---|
| `reviews_tiny.csv` | 3 | The brief's example; quick smoke test |
| `reviews_mixed_30.csv` | 30 | Hand-written: English, Tamil, Tanglish, urgent cases (food poisoning, insect, wrong order, refund); best for judging a real LLM |
| `reviews_week40.csv` | 220 | Volume test (includes one empty row to show validation) |

### Use your own data
Provide a CSV with exactly these headers: `review_id,date,platform,rating,review_text`
(UTF-8). `sample_data/generate_sample.py` regenerates the 220-row sample; `reviews_tiny.csv`
holds the 3 rows from the brief.

## Sample output

One analysed review:
```json
{"review_id": "R-1042", "sentiment": "negative", "category": "delivery", "urgency": "high",
 "language": "English", "summary": "Order arrived 70 minutes late and the food was cold.",
 "suggested_reply": "We are really sorry your order reached late and cold. ..."}
```
Weekly report:
```
WEEKLY FEEDBACK REPORT  |  29 Sep to 5 Oct 2026
Total reviews: 248   Positive 61%   Neutral 14%   Negative 25%

TOP 3 COMPLAINTS
  1. Late delivery ... 34 reviews  (mostly Swiggy)
...
URGENT: 9 reviews need a reply within 24 hours
```

## Project layout

```
CustFeedbackSpy/
├── app.py                      Streamlit UI
├── src/custfeedbackspy/        schemas, config, prompts, chains, validation,
│                               classifier, aggregate, report, export, mock_llm
├── tests/                      pytest (offline)
├── sample_data/                sample CSVs + generator
├── assets/                     favicon
├── .streamlit/config.toml      production server/theme settings
├── docs/                       ARCHITECTURE.md, TESTING_CHECKLIST.md
├── CLAUDE.md                   AI-assistant context
├── requirements.txt            runtime deps  (requirements-dev.txt adds pytest)
└── .env.example
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `OPENAI_API_KEY is not set` | Add the key to `.env`, restart the app |
| Tamil text garbled in Excel | Use the app's download; it is UTF-8 with BOM |
| `DLL load failed ... Application Control policy has blocked this file` | Your PC's policy blocks that compiled package. Use Python 3.12 (not 3.14); `requirements.txt` pins `xxhash<4` for this reason. If another package is blocked, try a different version of it or ask IT |
| `pytest` fails loading plugin `pytest11` (langsmith) | Run `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` before `python -m pytest -q` |
| Slow analysis | Real LLMs: reviews are sent 8 per call (`REVIEWS_PER_CALL`) and results are cached in `.cache/` so re-runs are instant (`USE_CACHE=false` to disable). Free tiers (Groq 8k tokens/min) are the limit |
| Rate-limit errors | Lower `MAX_CONCURRENCY` in `.env`; lower `REVIEWS_PER_CALL` if a model drops reviews from batches |
| Many `needs_review` rows | Use a stronger model, or raise `MAX_RETRIES` |

## Done checklist (from the brief)
See `docs/TESTING_CHECKLIST.md`.
