"""Streamlit UI. Run with:  streamlit run app.py"""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from custfeedbackspy import (  # noqa: E402
    CsvValidationError, build_analysis_chain, build_batch_chain, build_report_chain, classify_reviews,
    generate_report, load_many, load_settings, to_csv_bytes,
)
from custfeedbackspy import ui  # noqa: E402
from custfeedbackspy.cache import AnalysisCache  # noqa: E402
from custfeedbackspy.chains import provider_status  # noqa: E402

SAMPLE_DIR = Path(__file__).parent / "sample_data"
SENT_COLORS = {"positive": "#10b981", "neutral": "#f59e0b", "negative": "#f43f5e"}
SENT_ORDER = list(SENT_COLORS)

APP_TITLE = "Customer Feedback Analyzer"
ICON = Path(__file__).parent / "assets" / "favicon.png"


def _brand_static_page(title: str = APP_TITLE) -> None:
    """Streamlit's static index.html shows its own title + favicon until the script runs (visible on reload).
    Rewrite them once so the tab shows our name/icon immediately. Takes effect on the next browser reload."""
    try:
        static = Path(st.__file__).parent / "static"
        html = (static / "index.html").read_text(encoding="utf-8")
        new = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", html, count=1)
        if new != html:
            (static / "index.html").write_text(new, encoding="utf-8")
        if ICON.exists() and ICON.read_bytes() != (static / "favicon.png").read_bytes():
            shutil.copyfile(ICON, static / "favicon.png")
    except OSError:
        pass  # read-only install: Streamlit's default title/icon just flash briefly


_brand_static_page()
st.set_page_config(page_title=APP_TITLE, page_icon=str(ICON), layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.hero("🔍 Customer Feedback Analyzer",
                    "Drop in one or many review files. Get tagged reviews, urgent alerts and a weekly report."),
            unsafe_allow_html=True)

try:
    settings = load_settings()
except ValueError as e:
    st.error(str(e))
    st.stop()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("🤖 Models")
    st.markdown(ui.model_list(provider_status(settings.provider, settings.model)), unsafe_allow_html=True)
    st.caption("🟢 green = API key found, ready to use. Grey = no key in .env.")
    if settings.provider == "mock":
        st.warning("Mock mode: offline keyword rules, NOT a real LLM. Set LLM_PROVIDER in .env for real results.")
    st.caption("Change these in the .env file, then restart the app.")
    st.divider()
    st.subheader("📁 Bundled samples")
    bundled = sorted(p.name for p in SAMPLE_DIR.glob("*.csv"))
    picked = st.multiselect("Add sample files", bundled, help="Mix with your own uploads.")

# ---------------------------------------------------------------- input
uploads = st.file_uploader("Upload one or more review CSVs", type="csv", accept_multiple_files=True,
                           help="Columns: review_id, date, platform, rating, review_text")
sources = [(p, SAMPLE_DIR / p) for p in picked] + [(u.name, u) for u in uploads]

if not sources:
    st.info("Upload CSV files (you can select several at once) or pick bundled samples in the sidebar.")
    st.stop()

try:
    df, warnings = load_many(sources)
except CsvValidationError as e:
    st.error(str(e))
    st.stop()
for w in warnings:
    st.warning(w)

per_file = df.groupby("source_file").size().rename("reviews").reset_index()
st.markdown(ui.metric_cards([
    ("Files loaded", len(per_file), ", ".join(per_file["source_file"])[:60], "blue"),
    ("Valid reviews", len(df), "ready to analyse", "violet"),
]), unsafe_allow_html=True)
with st.expander("Preview loaded data"):
    st.dataframe(df.head(15), width="stretch")

sig = "|".join(f"{n}:{len(df)}" for n, _ in sources) + f"-{settings.provider}-{settings.model}"

if st.button("🚀 Analyse reviews", type="primary"):
    try:
        a_chain = build_analysis_chain(settings)
        r_chain = build_report_chain(settings)
        b_chain = build_batch_chain(settings)
    except RuntimeError as e:
        st.error(str(e))
        st.stop()
    overlay = st.empty()
    overlay.markdown(ui.loading_overlay("Analysing reviews", "Warming up the model...", 0.0), unsafe_allow_html=True)
    cache = AnalysisCache(f"{settings.provider}|{settings.model}") if settings.use_cache and settings.provider != "mock" else None
    enriched = classify_reviews(
        df, a_chain, batch_chain=b_chain, reviews_per_call=settings.reviews_per_call, cache=cache,
        max_concurrency=settings.max_concurrency,
        max_retries=settings.max_retries, batch_size=settings.batch_size,
        progress=lambda done, total: overlay.markdown(
            ui.loading_overlay("Analysing reviews", f"Classified {done} of {total} reviews", 0.9 * done / total),
            unsafe_allow_html=True),
    )
    overlay.markdown(ui.loading_overlay("Writing weekly report", "Summarising themes and urgent issues...", 0.95),
                     unsafe_allow_html=True)
    try:
        report_text, stats = generate_report(enriched, r_chain, settings.max_report_reviews)
    except Exception as e:  # noqa: BLE001
        overlay.empty()
        st.error(f"Report generation failed: {e}")
        st.stop()
    overlay.empty()
    st.session_state["result"] = (sig, enriched, report_text, stats)
    st.toast("Analysis complete", icon="✅")

result = st.session_state.get("result")
if not (result and result[0] == sig):
    st.stop()
_, enriched, report_text, stats = result


def hover_bar(data: pd.DataFrame, x: str, y: str, color, title: str) -> alt.Chart:
    hover = alt.selection_point(on="pointerover", clear="pointerout", fields=[x], empty=False)
    return (
        alt.Chart(data, title=title)
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
        .encode(
            y=alt.Y(f"{x}:N", sort="-x", title=None),
            x=alt.X(f"{y}:Q", title="reviews"),
            color=color,
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.7)),
            tooltip=[x, y],
        )
        .add_params(hover)
        .properties(height=260)
    )


tab_dash, tab_reviews, tab_report = st.tabs(["📊 Dashboard", "🗂️ Reviews", "📝 Weekly report"])

# ---------------------------------------------------------------- dashboard
with tab_dash:
    p = stats.sentiment_pct
    st.markdown(ui.metric_cards([
        ("Total reviews", stats.total, f"{len(per_file)} file(s)", "blue"),
        ("Positive", f"{p['positive']}%", f"{stats.sentiment_counts['positive']} reviews", "green"),
        ("Neutral", f"{p['neutral']}%", f"{stats.sentiment_counts['neutral']} reviews", "amber"),
        ("Negative", f"{p['negative']}%", f"{stats.sentiment_counts['negative']} reviews", "red"),
        ("Urgent (HIGH)", stats.urgent_count, "reply within 24h", "violet"),
    ]), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        sd = pd.DataFrame({"sentiment": SENT_ORDER, "reviews": [stats.sentiment_counts[s] for s in SENT_ORDER]})
        hov = alt.selection_point(on="pointerover", clear="pointerout", fields=["sentiment"], empty=False)
        donut = (
            alt.Chart(sd, title="Sentiment split")
            .mark_arc(innerRadius=60, stroke="#fff", strokeWidth=2)
            .encode(
                theta="reviews:Q",
                color=alt.Color("sentiment:N", scale=alt.Scale(domain=SENT_ORDER, range=list(SENT_COLORS.values()))),
                opacity=alt.condition(hov, alt.value(1.0), alt.value(0.72)),
                tooltip=["sentiment", "reviews"],
            )
            .add_params(hov).properties(height=260)
        )
        st.altair_chart(donut, width="stretch")
    with right:
        cd = pd.DataFrame({"category": list(stats.category_counts), "reviews": list(stats.category_counts.values())})
        st.altair_chart(hover_bar(cd, "category", "reviews",
                                  alt.Color("category:N", legend=None, scale=alt.Scale(scheme="tableau10")),
                                  "Reviews by category"), width="stretch")

    left2, right2 = st.columns(2)
    with left2:
        fs = enriched.groupby(["source_file", "sentiment"]).size().rename("reviews").reset_index()
        st.altair_chart(
            alt.Chart(fs, title="Sentiment by file")
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(x=alt.X("source_file:N", title=None, axis=alt.Axis(labelAngle=-20)), y="reviews:Q",
                    color=alt.Color("sentiment:N", scale=alt.Scale(domain=SENT_ORDER, range=list(SENT_COLORS.values()))),
                    tooltip=["source_file", "sentiment", "reviews"])
            .properties(height=260), width="stretch")
    with right2:
        pl = enriched.groupby(["platform", "urgency"]).size().rename("reviews").reset_index()
        st.altair_chart(
            alt.Chart(pl, title="Urgency by platform")
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(x=alt.X("platform:N", title=None), y="reviews:Q",
                    color=alt.Color("urgency:N", scale=alt.Scale(domain=["low", "medium", "high"],
                                                                 range=["#10b981", "#f59e0b", "#f43f5e"])),
                    tooltip=["platform", "urgency", "reviews"])
            .properties(height=260), width="stretch")

# ---------------------------------------------------------------- reviews
with tab_reviews:
    st.markdown(ui.section("Filter reviews"), unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    sel_sent = f1.multiselect("Sentiment", SENT_ORDER)
    sel_cat = f2.multiselect("Category", sorted(enriched["category"].unique()))
    sel_urg = f3.multiselect("Urgency", ["high", "medium", "low"])
    sel_file = f4.multiselect("File", sorted(enriched["source_file"].unique()))
    g1, g2, g3 = st.columns([3, 1, 1])
    query = g1.text_input("Search text", placeholder="e.g. refund, biryani, late")
    only_high = g2.toggle("Only HIGH urgency")
    view_mode = g3.radio("View", ["Cards", "Table"], horizontal=True)

    view = enriched
    if sel_sent: view = view[view["sentiment"].isin(sel_sent)]
    if sel_cat: view = view[view["category"].isin(sel_cat)]
    if sel_urg: view = view[view["urgency"].isin(sel_urg)]
    if sel_file: view = view[view["source_file"].isin(sel_file)]
    if only_high: view = view[view["urgency"] == "high"]
    if query:
        mask = view["review_text"].str.contains(query, case=False, regex=False) | \
               view["summary"].str.contains(query, case=False, regex=False)
        view = view[mask]
    st.caption(f"Showing {len(view)} of {len(enriched)} reviews")

    if view_mode == "Table":
        st.dataframe(view, width="stretch")
    else:
        limit = st.slider("Cards to show", 5, 100, 25, step=5)
        html = "".join(ui.review_card(r) for r in view.head(limit).itertuples())
        st.markdown(html or "<i>No reviews match the filters.</i>", unsafe_allow_html=True)
        if len(view) > limit:
            st.caption(f"{len(view) - limit} more not shown. Raise the slider or use Table view.")
    st.download_button("⬇️ Download filtered CSV (Excel-ready)", to_csv_bytes(view),
                       file_name="reviews_enriched.csv", mime="text/csv")

# ---------------------------------------------------------------- report
with tab_report:
    st.markdown(ui.report_box(report_text), unsafe_allow_html=True)
    st.write("")
    st.download_button("⬇️ Download report (.txt)", report_text.encode("utf-8"),
                       file_name="weekly_report.txt", mime="text/plain")
