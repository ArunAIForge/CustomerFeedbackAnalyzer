"""Offline keyword 'LLM' so the whole app runs with no API key (demo / tests).

It is deliberately simple. It implements the same Runnable interface as the real chains,
which is the point of LCEL: swap the model without changing the pipeline.
"""
from __future__ import annotations

import re
from collections import defaultdict

from langchain_core.runnables import Runnable, RunnableLambda

from .schemas import ReportNarrative, ReviewAnalysis, Theme

_HIGH = ["food poison", "vomit", "sick", "refund", "rude", "abuse", "wrong order", "wrong item",
         "hair in", "insect", "cockroach", "stale", "fungus", "allergic", "thittu", "mosam"]
_NEG = ["late", "cold", "bad", "worst", "poor", "extra charge", "small", "less", "rude", "wrong",
        "never", "disappoint", "costly", "expensive", "overpriced", "crash", "not good", "pottanga",
        "romba late", "tasteless", "stale", "refund"]
_POS = ["amazing", "great", "good", "tasty", "love", "excellent", "nice", "super", "best", "neat",
        "nalla", "semma", "fresh", "friendly", "fast", "will order again"]
_CATS = [
    ("delivery", ["deliver", "late", "rider", "came at", "arrived", "cold", "wait", "time"]),
    ("price", ["price", "charge", "bill", "costly", "expensive", "overpriced", "rate", "cash", "extra"]),
    ("staff", ["staff", "rude", "waiter", "behaviour", "behavior", "manager", "service", "attitude"]),
    ("packaging", ["packing", "packaging", "package", "spill", "leak", "box", "container"]),
    ("app", ["app", "crash", "login", "payment failed", "website", "offer code", "coupon"]),
]
_TAMIL_SCRIPT = re.compile(r"[஀-௿]")
_TANGLISH = ["irundhuchu", "illa", "romba", "nalla", "pottanga", "saapadu", "sappadu", "innum",
             "vandhuchu", "la ", "pannunga", "semma", "mosam", "ruchi"]


def _language(text: str) -> str:
    if _TAMIL_SCRIPT.search(text):
        return "Tamil"
    low = text.lower()
    return "Tanglish" if any(w in low for w in _TANGLISH) else "English"


def _analyse(inp: dict) -> ReviewAnalysis:
    text = str(inp["review_text"])
    low = text.lower()
    try:
        rating = float(inp.get("rating", 3))
    except (TypeError, ValueError):
        rating = 3.0
    neg = sum(k in low for k in _NEG)
    pos = sum(k in low for k in _POS)
    if rating <= 2 or (neg > pos and rating < 4):
        sentiment = "negative"
    elif rating >= 4 and pos >= neg:
        sentiment = "positive"
    else:
        sentiment = "neutral"
    category = "food_quality"
    best = 0
    for cat, keys in _CATS:
        hits = sum(k in low for k in keys)
        if hits > best:
            best, category = hits, cat
    high = any(k in low for k in _HIGH)
    urgency = "high" if high else ("medium" if sentiment == "negative" else "low")
    lang = _language(text)
    snippet = re.sub(r"\s+", " ", text).strip()
    snippet = snippet if len(snippet) <= 110 else snippet[:107] + "..."
    summary = f"Customer feedback ({sentiment}, {category.replace('_', ' ')}): {snippet}"
    if sentiment == "negative":
        reply = ("We are really sorry about your experience. We have shared this with the team. "
                 "Please message us your order details so we can make it right.")
    else:
        reply = "Thank you so much for your kind words! We look forward to serving you again."
    return ReviewAnalysis(sentiment=sentiment, category=category, urgency=urgency,
                          language=lang, summary=summary, suggested_reply=reply)


def _narrative(inp: dict) -> ReportNarrative:
    neg_groups: dict[str, list[str]] = defaultdict(list)
    pos_groups: dict[str, list[str]] = defaultdict(list)
    for line in str(inp["review_lines"]).splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        rid, _plat, sent, cat = parts[0], parts[1], parts[2], parts[3]
        if sent == "negative":
            neg_groups[cat].append(rid)
        elif sent == "positive":
            pos_groups[cat].append(rid)

    def top(groups: dict[str, list[str]], suffix: str) -> list[Theme]:
        ranked = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)[:3]
        return [Theme(label=f"{c.replace('_', ' ').capitalize()} {suffix}", review_ids=ids)
                for c, ids in ranked]

    complaints = top(neg_groups, "issues")
    praises = top(pos_groups, "praise")
    actions = []
    for t in complaints[:2]:
        actions.append(f"Investigate and fix: {t.label.lower()}.")
    while len(actions) < 2:
        actions.append("Keep monitoring customer feedback for new issues.")
    actions.append(f"Reply to all {inp['urgent_count']} urgent reviews today using the suggested replies.")
    return ReportNarrative(top_complaints=complaints, top_praises=praises, action_items=actions)


def mock_analysis_chain() -> Runnable:
    return RunnableLambda(_analyse)


def mock_report_chain() -> Runnable:
    return RunnableLambda(_narrative)
