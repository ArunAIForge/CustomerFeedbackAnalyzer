"""Look and feel: gradients, shadows and hover effects (pure CSS, no extra packages).

All user text is HTML-escaped before it is placed inside markup.
"""
from __future__ import annotations

from html import escape

CSS = """
<style>
:root {
  --g-hero: linear-gradient(120deg, #4f46e5 0%, #7c3aed 45%, #ec4899 100%);
  --g-blue: linear-gradient(135deg, #3b82f6, #06b6d4);
  --g-green: linear-gradient(135deg, #10b981, #84cc16);
  --g-red: linear-gradient(135deg, #f43f5e, #f97316);
  --g-amber: linear-gradient(135deg, #f59e0b, #ef4444);
  --g-violet: linear-gradient(135deg, #8b5cf6, #ec4899);
  --shadow: 0 6px 18px rgba(0,0,0,.18);
  --shadow-hover: 0 16px 34px rgba(79,70,229,.35);
}
.block-container { padding-top: 1.6rem; max-width: 1250px; }
header[data-testid="stHeader"] { background: transparent; }

/* ---------- hero ---------- */
.hero {
  background: var(--g-hero); background-size: 200% 200%;
  animation: shift 10s ease infinite;
  border-radius: 20px; padding: 28px 34px; color: #fff;
  box-shadow: 0 14px 40px rgba(124,58,237,.38); margin-bottom: 22px;
  transition: transform .3s ease, box-shadow .3s ease;
}
.hero:hover { transform: translateY(-3px); box-shadow: 0 20px 50px rgba(124,58,237,.5); }
.hero h1 { margin: 0; font-size: 2.1rem; color: #fff; }
.hero p { margin: 6px 0 0; opacity: .92; font-size: 1.02rem; }
@keyframes shift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }

/* ---------- metric cards ---------- */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin: 6px 0 22px; }
.mcard {
  border-radius: 18px; padding: 18px 20px; color: #fff; position: relative; overflow: hidden;
  box-shadow: var(--shadow); cursor: default;
  transition: transform .25s ease, box-shadow .25s ease, filter .25s ease;
}
.mcard:hover { transform: translateY(-7px) scale(1.03); box-shadow: var(--shadow-hover); filter: brightness(1.08); }
.mcard::after {
  content: ""; position: absolute; width: 120px; height: 120px; right: -30px; top: -40px;
  background: rgba(255,255,255,.18); border-radius: 50%; transition: transform .4s ease;
}
.mcard:hover::after { transform: scale(1.6); }
.mcard .lbl { font-size: .82rem; letter-spacing: .06em; text-transform: uppercase; opacity: .9; }
.mcard .val { font-size: 2.2rem; font-weight: 800; line-height: 1.15; }
.mcard .sub { font-size: .8rem; opacity: .85; }

/* ---------- buttons, tabs, uploader ---------- */
div.stButton > button, div.stDownloadButton > button {
  border-radius: 12px; border: none; font-weight: 600; padding: .6rem 1.3rem;
  box-shadow: 0 4px 12px rgba(0,0,0,.18);
  transition: transform .2s ease, box-shadow .2s ease, filter .2s ease;
}
div.stButton > button[kind="primary"] { background: var(--g-hero); color: #fff; }
div.stButton > button:hover, div.stDownloadButton > button:hover {
  transform: translateY(-3px) scale(1.03); box-shadow: 0 10px 24px rgba(124,58,237,.45); filter: brightness(1.1);
}
div.stButton > button:active { transform: translateY(0) scale(.98); }
button[data-baseweb="tab"] { border-radius: 12px 12px 0 0; transition: background .2s ease, transform .2s ease; font-weight: 600; }
button[data-baseweb="tab"]:hover { background: rgba(124,58,237,.14); transform: translateY(-2px); }
[data-testid="stFileUploader"] section {
  border: 2px dashed #8b5cf6; border-radius: 16px; background: rgba(139,92,246,.06);
  transition: all .25s ease;
}
[data-testid="stFileUploader"] section:hover {
  background: rgba(139,92,246,.16); box-shadow: 0 0 0 4px rgba(139,92,246,.18), var(--shadow); transform: scale(1.01);
}
[data-testid="stDataFrame"], [data-testid="stVegaLiteChart"] {
  border-radius: 14px; box-shadow: var(--shadow); padding: 6px; transition: box-shadow .25s ease, transform .25s ease;
}
[data-testid="stDataFrame"]:hover, [data-testid="stVegaLiteChart"]:hover { box-shadow: var(--shadow-hover); transform: translateY(-3px); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(79,70,229,.14), rgba(236,72,153,.10)); }

/* ---------- model list (sidebar) ---------- */
.mlist { display: flex; flex-direction: column; gap: 8px; margin: 6px 0 4px; }
.mrow { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 14px;
  background: rgba(128,128,128,.10); border: 1px solid rgba(128,128,128,.18); box-shadow: 0 2px 8px rgba(0,0,0,.10);
  transition: transform .2s ease, box-shadow .2s ease, background .2s ease; }
.mrow:hover { transform: translateX(5px); box-shadow: var(--shadow-hover); background: rgba(139,92,246,.16); }
.mrow.active { background: linear-gradient(135deg, rgba(16,185,129,.22), rgba(132,204,22,.16));
  border-color: rgba(16,185,129,.7); }
.mdot { width: 14px; height: 14px; border-radius: 50%; flex: none; background: #94a3b8; }
.mdot.on { background: radial-gradient(circle at 35% 30%, #86efac, #10b981 60%, #047857);
  box-shadow: 0 0 0 0 rgba(16,185,129,.6); animation: glow 2s infinite; }
@keyframes glow { 0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.55)} 50%{box-shadow:0 0 0 7px rgba(16,185,129,0)} }
.mname { font-weight: 700; font-size: .92rem; line-height: 1.15; }
.mmodel { font-size: .72rem; opacity: .7; word-break: break-all; }
.mtag { margin-left: auto; font-size: .62rem; font-weight: 800; padding: 2px 8px; border-radius: 999px;
  color: #fff; background: var(--g-green); letter-spacing: .05em; }
.mtag.off { background: #94a3b8; }

/* ---------- section titles ---------- */
.sec { font-size: 1.25rem; font-weight: 700; margin: 8px 0 6px;
  background: var(--g-hero); -webkit-background-clip: text; background-clip: text; color: transparent; }

/* ---------- review cards ---------- */
.rcard {
  border-radius: 16px; padding: 14px 18px; margin: 12px 0; background: rgba(128,128,128,.09);
  border-left: 6px solid #94a3b8; box-shadow: var(--shadow);
  transition: transform .22s ease, box-shadow .22s ease, background .22s ease;
}
.rcard:hover { transform: translateX(6px) translateY(-3px); box-shadow: var(--shadow-hover); background: rgba(139,92,246,.14); }
.rcard.positive { border-left-color: #10b981; } .rcard.neutral { border-left-color: #f59e0b; }
.rcard.negative { border-left-color: #f43f5e; } .rcard.high { box-shadow: 0 0 0 2px rgba(244,63,94,.55), var(--shadow); }
.rcard .top { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 6px; }
.rcard .meta { font-size: .78rem; opacity: .7; margin-left: auto; }
.rcard .txt { font-size: 1rem; margin: 4px 0; }
.rcard .sum { font-size: .9rem; opacity: .85; font-style: italic; }
.rcard details { margin-top: 8px; } .rcard summary { cursor: pointer; font-weight: 600; color: #8b5cf6; }
.rcard summary:hover { text-decoration: underline; }
.badge { display: inline-block; padding: 2px 11px; border-radius: 999px; font-size: .74rem; font-weight: 700;
  color: #fff; transition: transform .15s ease; }
.badge:hover { transform: scale(1.12); }
.b-positive { background: var(--g-green); } .b-neutral { background: var(--g-amber); }
.b-negative { background: var(--g-red); } .b-cat { background: var(--g-blue); }
.b-high { background: var(--g-red); animation: pulse 1.6s infinite; } .b-medium { background: var(--g-amber); }
.b-low { background: var(--g-green); } .b-lang { background: var(--g-violet); } .b-flag { background: #64748b; }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 0 rgba(244,63,94,.55)} 50%{box-shadow:0 0 0 8px rgba(244,63,94,0)} }

/* ---------- report ---------- */
.report {
  border-radius: 18px; padding: 24px 28px; white-space: pre-wrap; font-family: ui-monospace, Consolas, monospace;
  background: linear-gradient(rgba(128,128,128,.10), rgba(128,128,128,.10)) padding-box, var(--g-hero) border-box;
  border: 3px solid transparent; box-shadow: var(--shadow); line-height: 1.55;
  transition: box-shadow .3s ease, transform .3s ease;
}
.report:hover { box-shadow: var(--shadow-hover); transform: translateY(-3px); }

/* ---------- loading overlay ---------- */
.ldr-back { position: fixed; inset: 0; z-index: 999990; display: flex; align-items: center; justify-content: center;
  background: rgba(15,23,42,.62); backdrop-filter: blur(6px); }
.ldr-card { width: min(420px, 90vw); border-radius: 22px; padding: 32px 30px; text-align: center; color: #fff;
  background: linear-gradient(135deg,#4f46e5,#7c3aed,#db2777); box-shadow: 0 24px 60px rgba(0,0,0,.45); }
.ldr-ring { width: 64px; height: 64px; margin: 0 auto 18px; border-radius: 50%;
  border: 6px solid rgba(255,255,255,.28); border-top-color: #fff; animation: ldrspin 0.9s linear infinite; }
.ldr-title { font-size: 1.25rem; font-weight: 700; } .ldr-sub { opacity: .85; margin: 6px 0 18px; font-size: .95rem; }
.ldr-track { height: 10px; border-radius: 99px; background: rgba(255,255,255,.25); overflow: hidden; }
.ldr-fill { height: 100%; border-radius: 99px; background: #fff; transition: width .25s ease; }
.ldr-pct { margin-top: 8px; font-size: .85rem; opacity: .9; }
@keyframes ldrspin { to { transform: rotate(360deg); } }
</style>
"""


def hero(title: str, subtitle: str) -> str:
    return f'<div class="hero"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>'


def metric_cards(items: list[tuple[str, str, str, str]]) -> str:
    """items: (label, value, sub-text, gradient-name: blue|green|red|amber|violet)."""
    cards = "".join(
        f'<div class="mcard" style="background:var(--g-{g})"><div class="lbl">{escape(l)}</div>'
        f'<div class="val">{escape(str(v))}</div><div class="sub">{escape(s)}</div></div>'
        for l, v, s, g in items
    )
    return f'<div class="cards">{cards}</div>'


def section(title: str) -> str:
    return f'<div class="sec">{escape(title)}</div>'


def review_card(r) -> str:
    """r: a row (namedtuple/Series-like) of the enriched dataframe."""
    flag = '<span class="badge b-flag">needs review</span>' if getattr(r, "needs_review", False) else ""
    date = "" if str(r.date) in ("NaT", "nan") else str(r.date)[:10]
    reply = (
        f"<details><summary>Suggested reply</summary><div>{escape(r.suggested_reply)}</div></details>"
        if r.suggested_reply else ""
    )
    return (
        f'<div class="rcard {escape(r.sentiment)} {"high" if r.urgency == "high" else ""}">'
        f'<div class="top"><span class="badge b-{escape(r.sentiment)}">{escape(r.sentiment)}</span>'
        f'<span class="badge b-cat">{escape(r.category.replace("_", " "))}</span>'
        f'<span class="badge b-{escape(r.urgency)}">{escape(r.urgency)} urgency</span>'
        f'<span class="badge b-lang">{escape(r.language)}</span>{flag}'
        f'<span class="meta">{escape(str(r.review_id))} · {escape(r.platform)} · {escape(date)} · '
        f'{escape(str(getattr(r, "source_file", "")))}</span></div>'
        f'<div class="txt">{escape(r.review_text)}</div><div class="sum">{escape(r.summary)}</div>{reply}</div>'
    )


def loading_overlay(title: str, sub: str, pct: float) -> str:
    """Full-screen blurred overlay with spinner + progress bar. pct in 0..1."""
    p = max(0, min(100, round(pct * 100)))
    return (
        f'<div class="ldr-back"><div class="ldr-card"><div class="ldr-ring"></div>'
        f'<div class="ldr-title">{escape(title)}</div><div class="ldr-sub">{escape(sub)}</div>'
        f'<div class="ldr-track"><div class="ldr-fill" style="width:{p}%"></div></div>'
        f'<div class="ldr-pct">{p}%</div></div></div>'
    )


def report_box(text: str) -> str:
    return f'<pre class="report">{escape(text)}</pre>'


def model_list(rows: list[dict]) -> str:
    """rows from chains.provider_status(): green glowing dot = ready (key set), grey = no key."""
    out = []
    for r in rows:
        tag = ('<span class="mtag">ACTIVE</span>' if r["active"]
               else ('' if r["ready"] else '<span class="mtag off">NO KEY</span>'))
        out.append(
            f'<div class="mrow{" active" if r["active"] else ""}"><span class="mdot{" on" if r["ready"] else ""}"></span>'
            f'<div><div class="mname">{escape(r["label"])}</div><div class="mmodel">{escape(r["model"])}</div></div>{tag}</div>'
        )
    return f'<div class="mlist">{"".join(out)}</div>'
