# Done Checklist (from the brief) and how to verify

| Item | How to verify | Automated |
|---|---|---|
| 200+ row CSV, no crash | Sample CSV has 220 rows; click Analyse | `test_full_pipeline_all_fields_valid` |
| All 6 fields, allowed values | Reviews tab; no blanks | same test |
| Tamil/Tanglish → English summary | Real LLM: check R-1043 and the Tamil rows | mock only checks language detection |
| Report numbers match table | Compare report vs Dashboard metrics | `test_report_numbers_come_from_pandas`, `test_hallucinated_ids_ignored` |
| HIGH filter + Excel CSV | Toggle filter; download; open in Excel | `test_csv_export_has_bom_and_tamil` |
| Key from `.env` | `grep -r "sk-" .` finds nothing; `.env` is git-ignored | n/a |
| Invalid value retried | n/a | `test_retry_then_needs_review` |
| Sidebar lists only openai/groq/openrouter/mock | Open the app sidebar | `test_provider_status_marks_ready_and_active` |
| Loading overlay on Analyse | Click Analyse; overlay shows progress, then a toast | manual |

## Manual real-LLM check (needs an API key)
1. `LLM_PROVIDER=openai` (or groq/openrouter/anthropic/gemini) + key in `.env`.
2. Pick or upload `sample_data/reviews_tiny.csv` → R-1042 negative / delivery / high.
3. Upload the 220-row sample → completes; `needs_review` count near 0.
4. Test with your own CSV, not just the bundled sample (brief requirement).
