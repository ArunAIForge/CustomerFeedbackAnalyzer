# Architecture

```
CSV ──► validation.py ──► classifier.py ──► aggregate.py ──► report.py ──► app.py (UI + CSV)
                              │                                  │
                      analysis chain (map)               report chain (reduce)
                      prompt | llm.with_structured_output(ReviewAnalysis)
                                                         prompt | llm.with_structured_output(ReportNarrative)
                              └──────── chains.py picks the vendor (openai | groq | openrouter | xai | anthropic | gemini | mock) ────────┘
```

## Key design decisions
| Decision | Reason |
|---|---|
| `with_structured_output(Pydantic)` | Typed, validated JSON every time; no brittle parsing |
| `Literal` allowed values | Out-of-list values fail validation → retry → `needs_review` |
| `chain.batch(max_concurrency)` in chunks of 20 | Speed + rate-limit safety + progress bar |
| Map then reduce | 500 reviews don't fit one prompt; summaries are compact |
| LLM returns themes + ids, code counts | LLMs miscount; ids are verified against the table |
| Vendor imports only in `chains.py` | Swap models without touching the pipeline |
| Mock chain with the same Runnable interface | Offline demo and free tests |
| CSV `utf-8-sig` | Tamil displays correctly in Excel |
| Batching (`REVIEWS_PER_CALL`) + on-disk cache (`.cache/`) | Fewer LLM calls; re-runs are instant |
| Loading overlay driven by the classifier's `progress` callback | UI stays decoupled from the pipeline (`ui.loading_overlay`) |

## Data flow fields
`review_id, date, platform, rating, review_text` → `+ sentiment, category, urgency, language, summary, suggested_reply, needs_review`.

## Extending
- New category: add to `schemas.Category` + `CATEGORIES`, mention in `prompts.ANALYSIS_SYSTEM`.
- New provider: add a branch in `chains._chat_model`, defaults in `config.DEFAULT_MODELS`, a label in `chains.LABELS`;
  add it to `chains.SIDEBAR_PROVIDERS` to show it in the sidebar (currently openai, groq, openrouter, mock).
- Trend arrows: run `compute_stats` on last week's CSV and diff the two `Stats`.
