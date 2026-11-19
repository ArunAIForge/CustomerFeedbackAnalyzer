import io
import sys
from pathlib import Path

import pandas as pd
import pytest
from langchain_core.runnables import RunnableLambda

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from custfeedbackspy import (  # noqa: E402
    CsvValidationError, classify_reviews, compute_stats, generate_report, load_and_validate,
    to_csv_bytes,
)
from custfeedbackspy.mock_llm import mock_analysis_chain, mock_report_chain  # noqa: E402
from custfeedbackspy.schemas import CATEGORIES, SENTIMENTS, URGENCIES, ReviewAnalysis  # noqa: E402

SAMPLE = Path(__file__).parents[1] / "sample_data" / "reviews_week40.csv"


def test_validation_drops_empty_and_reports():
    df, warnings = load_and_validate(SAMPLE)
    assert len(df) == 220
    assert any("empty review_text" in w for w in warnings)


def test_missing_column_raises():
    with pytest.raises(CsvValidationError):
        load_and_validate(io.StringIO("review_id,date\nR1,2026-01-01\n"))


def test_full_pipeline_all_fields_valid():
    df, _ = load_and_validate(SAMPLE)
    out = classify_reviews(df, mock_analysis_chain(), batch_size=50)
    assert len(out) == 220
    assert out["sentiment"].isin(SENTIMENTS).all()
    assert out["category"].isin(CATEGORIES).all()
    assert out["urgency"].isin(URGENCIES).all()
    assert (out["summary"].str.len() > 0).all()
    assert not out["needs_review"].any()


def test_tamil_and_tanglish_language_detected():
    df, _ = load_and_validate(SAMPLE)
    out = classify_reviews(df, mock_analysis_chain())
    assert {"Tamil", "Tanglish", "English"} <= set(out["language"])


def test_retry_then_needs_review():
    df, _ = load_and_validate(io.StringIO(
        "review_id,date,platform,rating,review_text\nR1,2026-10-01,Google,5,great\nR2,2026-10-01,Google,1,bad\n"))
    calls = {"R2": 0}
    good = ReviewAnalysis(sentiment="positive", category="food_quality", urgency="low",
                          language="English", summary="ok", suggested_reply="thanks")

    def flaky(inp):
        if inp["review_text"] == "bad":
            calls["R2"] += 1
            raise ValueError("invalid category")
        return good

    out = classify_reviews(df, RunnableLambda(flaky), max_retries=2)
    assert out.loc[out.review_id == "R1", "needs_review"].item() is False or not out.loc[out.review_id == "R1", "needs_review"].item()
    assert bool(out.loc[out.review_id == "R2", "needs_review"].item())
    assert calls["R2"] == 3  # 1 batch attempt + 2 retries


def test_report_numbers_come_from_pandas():
    df, _ = load_and_validate(SAMPLE)
    out = classify_reviews(df, mock_analysis_chain())
    text, stats = generate_report(out, mock_report_chain())
    assert stats.total == 220
    assert sum(stats.sentiment_counts.values()) == 220
    assert f"Total reviews: {stats.total}" in text
    assert f"URGENT: {int((out.urgency == 'high').sum())} reviews" in text
    assert "ACTION ITEMS" in text


def test_hallucinated_ids_ignored():
    from custfeedbackspy.report import render_report
    from custfeedbackspy.schemas import ReportNarrative, Theme

    df, _ = load_and_validate(SAMPLE)
    out = classify_reviews(df, mock_analysis_chain())
    stats = compute_stats(out)
    nar = ReportNarrative(top_complaints=[Theme(label="Ghost", review_ids=["NOPE-1"])],
                          top_praises=[], action_items=["a", "b", "c"])
    assert "Ghost" not in render_report(out, stats, nar)


def test_csv_export_has_bom_and_tamil():
    df, _ = load_and_validate(SAMPLE)
    out = classify_reviews(df, mock_analysis_chain())
    raw = to_csv_bytes(out)
    assert raw.startswith(b"\xef\xbb\xbf")
    assert "சுவையான".encode("utf-8") in raw
    assert len(pd.read_csv(io.BytesIO(raw))) == 220


def test_load_many_combines_files_and_dedupes():
    from custfeedbackspy import load_many

    d = Path(__file__).parents[1] / "sample_data"
    df, warns = load_many([("tiny", d / "reviews_tiny.csv"), ("mixed", d / "reviews_mixed_30.csv"),
                           ("tiny_again", d / "reviews_tiny.csv")])
    assert set(df["source_file"]) == {"tiny", "mixed"}
    assert len(df) == 3 + 30
    assert any("same review_id across files" in w for w in warns)


def test_load_many_skips_bad_file_but_fails_if_all_bad():
    from custfeedbackspy import load_many

    good = Path(__file__).parents[1] / "sample_data" / "reviews_tiny.csv"
    df, warns = load_many([("bad", io.StringIO("a,b\n1,2\n")), ("good", good)])
    assert len(df) == 3 and any("bad: skipped" in w for w in warns)
    with pytest.raises(CsvValidationError):
        load_many([("bad", io.StringIO("a,b\n1,2\n"))])


def test_ui_escapes_html():
    from types import SimpleNamespace

    from custfeedbackspy import ui

    r = SimpleNamespace(sentiment="negative", category="food_quality", urgency="high", language="English",
                        review_id="X", platform="Z", date="2026-10-01", source_file="f.csv",
                        review_text="<script>alert(1)</script>", summary="s", suggested_reply="r", needs_review=False)
    html = ui.review_card(r)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "<script>" not in ui.report_box("<script>x</script>")


def test_provider_status_marks_ready_and_active(monkeypatch):
    from custfeedbackspy import ui
    from custfeedbackspy.chains import provider_status

    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    rows = {r["provider"]: r for r in provider_status("mock", "keyword-heuristics")}
    assert rows["mock"]["active"] and rows["mock"]["ready"]
    assert rows["openrouter"]["ready"]
    assert set(rows) == {"openai", "groq", "openrouter", "mock"}
    html = ui.model_list(list(rows.values()))
    assert html.count("mdot on") == sum(r["ready"] for r in rows.values())
    assert "ACTIVE" in html


def _unique_df(n):
    lines = ["review_id,date,platform,rating,review_text"]
    lines += [f"U{i},2026-10-01,Google,{1 + i % 5},unique review number {i} about food" for i in range(n)]
    return load_and_validate(io.StringIO(chr(10).join(lines) + chr(10)))[0]


def _fake_batch_chain(drop_ids=(), fail=False):
    from custfeedbackspy.schemas import BatchAnalysis, BatchItem

    calls = []

    def run(inp):
        calls.append(inp["reviews"])
        if fail:
            raise ValueError("boom")
        items = []
        for line in inp["reviews"].splitlines():
            rid = line.split(" | ")[0]
            if rid in drop_ids:
                continue
            items.append(BatchItem(review_id=rid, sentiment="positive", category="food_quality", urgency="low",
                                   language="English", summary="batched", suggested_reply="thanks"))
        return BatchAnalysis(results=items)

    return RunnableLambda(run), calls


def test_batching_uses_few_calls_and_falls_back_for_missing():
    df = _unique_df(20)
    single_calls = []
    single = RunnableLambda(lambda i: single_calls.append(1) or ReviewAnalysis(
        sentiment="neutral", category="app", urgency="low", language="English", summary="single", suggested_reply="r"))
    batch, calls = _fake_batch_chain(drop_ids={df.review_id[3]})
    out = classify_reviews(df, single, batch_chain=batch, reviews_per_call=8)
    assert len(calls) == 3                      # 20 reviews / 8 per call
    assert len(single_calls) == 1               # only the dropped review needed the single path
    assert (out["summary"] == "batched").sum() == 19 and not out["needs_review"].any()


def test_failed_batch_call_falls_back_to_single():
    df = _unique_df(5)
    out = classify_reviews(df, mock_analysis_chain(), batch_chain=_fake_batch_chain(fail=True)[0], reviews_per_call=8)
    assert len(out) == 5 and not out["needs_review"].any()


def test_cache_skips_second_run(tmp_path):
    from custfeedbackspy.cache import AnalysisCache

    df = _unique_df(10)
    path = tmp_path / "c.json"
    calls = []
    chain = RunnableLambda(lambda i: calls.append(1) or mock_analysis_chain().invoke(i))
    classify_reviews(df, chain, cache=AnalysisCache("t", path))
    first = len(calls)
    out = classify_reviews(df, chain, cache=AnalysisCache("t", path))
    assert first == 10 and len(calls) == 10 and len(out) == 10   # second run made zero new calls
    assert len(classify_reviews(df, chain, cache=AnalysisCache("other-model", path))) == 10 and len(calls) == 20


def test_failed_batch_retried_as_halves_before_single():
    from custfeedbackspy.schemas import BatchAnalysis, BatchItem

    df = _unique_df(8)
    sizes = []

    def run(inp):
        lines = inp["reviews"].splitlines()
        sizes.append(len(lines))
        if len(lines) == 8:
            raise ValueError("malformed tool JSON")
        return BatchAnalysis(results=[BatchItem(review_id=l.split(" | ")[0], sentiment="positive",
                                                category="app", urgency="low", language="English",
                                                summary="half", suggested_reply="r") for l in lines])

    single_calls = []
    single = RunnableLambda(lambda i: single_calls.append(1))
    out = classify_reviews(df, single, batch_chain=RunnableLambda(run), reviews_per_call=8)
    assert sizes == [8, 4, 4] and not single_calls
    assert (out["summary"] == "half").all()


def test_duplicate_reviews_analysed_once():
    df, _ = load_and_validate(io.StringIO(
        "review_id,date,platform,rating,review_text\n"
        "A,2026-10-01,Zomato,5,great food\nB,2026-10-02,Swiggy,5,great food\nC,2026-10-03,Google,1,cold and late\n"))
    calls = []
    chain = RunnableLambda(lambda i: calls.append(i["review_text"]) or mock_analysis_chain().invoke(i))
    out = classify_reviews(df, chain)
    assert len(calls) == 2 and len(out) == 3
    assert out.loc[out.review_id == "B", "sentiment"].item() == out.loc[out.review_id == "A", "sentiment"].item()
    assert list(out.review_id) == ["A", "B", "C"]
