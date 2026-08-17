"""Shared UI theming, page setup, and value formatting helpers.

Design direction — "Phosphor": a professional trading-terminal identity in the
CRT-phosphor lineage (warm near-black ink, phosphor paper-white text, a single
cyan-blue phosphor accent). Green/red are reserved strictly for P&L direction.
Type is a deliberate trio — Space Grotesk (display), JetBrains Mono (data/eyebrows/
the market tape), IBM Plex Sans (body) — not the generic Inter default.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when Streamlit runs a page as a script.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import math

import streamlit as st

# Palette follows the data-viz method for chart *identity* (CVD-validated
# `series`), while the UI accent is the cyan-blue phosphor signature. up/down are
# reserved P&L status hues and never appear in `series`.
PALETTE = {
    "bg": "#0a0b0d",
    "panel": "#121316",
    "panel_2": "#16181d",
    "grid": "#22242c",           # hairline, one step off surface, recessive
    "axis": "#2e313c",
    "text": "#e8e6df",           # phosphor paper-white
    "text_strong": "#fbfaf6",
    "muted": "#8a8b84",
    "accent": "#48a7e6",         # cyan-blue phosphor — UI + single-accent chart lines
    "up": "#3fb68b",             # status: gain (reserved)
    "down": "#e5484d",           # status: loss (reserved)
    "neutral": "#e3b341",        # warm counter-hue (MACD signal, BB middle) vs blue accent
    # Categorical identity order (blue, orange, aqua, yellow, magenta, violet)
    "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"],
    # Diverging pole/mid for correlation (−1 red · 0 gray · +1 blue)
    "div_neg": "#e5484d",
    "div_mid": "#33343a",
    "div_pos": "#3987e5",
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #0a0b0d;
  --panel: #121316;
  --panel-2: #16181d;
  --line: #22242c;
  --line-soft: #1a1c22;
  --paper: #e8e6df;
  --paper-strong: #fbfaf6;
  --dim: #8a8b84;
  --dim-2: #5f6058;
  --accent: #48a7e6;
  --accent-dim: rgba(72,167,230,0.14);
  --up: #3fb68b;
  --down: #e5484d;
  --font-display: 'Space Grotesk', 'Segoe UI', sans-serif;
  --font-ui: 'IBM Plex Sans', -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace;
}

/* ---- base ------------------------------------------------------------- */
html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--ink); color: var(--paper);
  font-family: var(--font-ui); -webkit-font-smoothing: antialiased;
}
[data-testid="stAppViewContainer"] { background:
  radial-gradient(1100px 520px at 88% -12%, rgba(72,167,230,0.05), transparent 62%),
  var(--ink); }
.block-container { padding-top: 1.4rem; padding-bottom: 4rem; max-width: 1340px; }

/* tabular figures only in vertical columns (tables); big numbers stay proportional */
.stDataFrame, table, .ml-mono { font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
[data-testid="stMetricValue"], .ml-kpi .val { font-variant-numeric: proportional-nums; }

/* ---- hide default Streamlit chrome ------------------------------------ */
/* Hide only the toolbar ACTIONS (deploy / main menu / status) — NOT the whole
   toolbar, because the sidebar reopen control lives inside it and must stay
   visible when the sidebar is collapsed. */
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
[data-testid="stMainMenuButton"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

/* ---- sidebar toggle: standard three-line (hamburger) icon, both states -- */
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
  font-size: 0 !important;  /* hide the default chevron ligature */
}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]::after,
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"]::after {
  content: "menu";  /* Material Symbols ligature for the hamburger */
  font-family: "Material Symbols Rounded", "Material Symbols Outlined";
  font-size: 22px; line-height: 1; color: var(--paper);
}
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"]::after { color: var(--dim); }
[data-testid="stExpandSidebarButton"]:hover [data-testid="stIconMaterial"]::after { color: var(--accent); }

/* ---- typography ------------------------------------------------------- */
h1, h2, h3, h4 { color: var(--paper-strong); font-family: var(--font-display); letter-spacing: -0.02em; }
h1 { font-weight: 700; }
h2 { font-weight: 600; font-size: 1.5rem; }
h3 { font-weight: 600; font-size: 1.18rem; }
[data-testid="stMarkdownContainer"] h4 {
  font-weight: 600; font-size: 1rem; color: var(--paper-strong);
  margin: 1.6rem 0 0.55rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--line-soft);
}
[data-testid="stMarkdownContainer"] p { color: var(--paper); }
a, a:visited { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }

/* ---- accessibility floor --------------------------------------------- */
*:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
}

/* ---- page header ------------------------------------------------------ */
.ml-page-header { margin: 0.1rem 0 1.4rem; }
.ml-eyebrow {
  font-size: 0.7rem; font-weight: 500; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--dim); font-family: var(--font-mono);
}
.ml-title {
  font-family: var(--font-display); font-size: 1.78rem; font-weight: 700;
  color: var(--paper-strong); margin: 0.3rem 0 0.3rem; letter-spacing: -0.025em; line-height: 1.08;
}
.ml-subtitle { color: var(--dim); font-size: 0.9rem; max-width: 72ch; line-height: 1.55; }
.ml-rule { height: 1px; margin-top: 1rem;
  background: linear-gradient(90deg, rgba(232,230,223,0.38) 0%, rgba(232,230,223,0.10) 34%, transparent 72%); }

/* ---- market tape (signature) ----------------------------------------- */
.ml-tape {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr));
  border: 1px solid var(--line); border-radius: 12px; overflow: hidden;
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
}
.ml-tape-item { padding: 13px 16px; border-right: 1px solid var(--line-soft); position: relative; }
.ml-tape-item:last-child { border-right: none; }
.ml-tape-item::before {
  content: ""; position: absolute; left: 0; top: 10px; bottom: 10px; width: 2px; background: transparent;
}
.ml-tape-item.up::before { background: var(--up); }
.ml-tape-item.down::before { background: var(--down); }
.ml-tape-code {
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
  color: var(--dim); text-transform: uppercase;
}
.ml-tape-last {
  font-family: var(--font-ui); font-size: 1.04rem; font-weight: 600; color: var(--paper-strong);
  margin: 4px 0 2px; font-variant-numeric: tabular-nums;
}
.ml-tape-chg { font-family: var(--font-ui); font-size: 0.8rem; font-weight: 500; font-variant-numeric: tabular-nums; }
@media (max-width: 900px) { .ml-tape { grid-template-columns: repeat(2, 1fr); }
  .ml-tape-item:nth-child(even) { border-right: none; } }
/* tape error state — the signature element says why it is empty, never blank */
.ml-tape-empty {
  display: flex; align-items: center; gap: 10px;
  border: 1px solid var(--line); border-radius: 12px; padding: 15px 18px;
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
  color: var(--dim); font-size: 0.86rem; line-height: 1.5;
}
.ml-tape-empty .dot {
  flex: none; width: 7px; height: 7px; border-radius: 999px;
  background: #e3b341; box-shadow: 0 0 0 3px rgba(227,179,65,0.14);
}

/* ---- hero (home) ------------------------------------------------------ */
.ml-hero { margin: 0.3rem 0 1.6rem; display: grid; grid-template-columns: 1fr; gap: 26px; align-items: center; }
/* On wide screens the live panel occupies the right so the hero fills the row. */
@media (min-width: 1000px) { .ml-hero { grid-template-columns: minmax(0, 1fr) 340px; } }
.ml-hero-eyebrow {
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.24em;
  text-transform: uppercase; color: var(--accent); margin-bottom: 0.9rem;
}
.ml-hero-title {
  font-family: var(--font-display); font-size: 3rem; font-weight: 700; letter-spacing: -0.035em;
  line-height: 1.02; color: var(--paper-strong); margin: 0 0 0.5rem; max-width: 20ch;
}
.ml-hero-tagline {
  font-family: var(--font-display); font-size: 1.5rem; font-weight: 600; letter-spacing: -0.02em;
  line-height: 1.15; color: var(--paper-strong); margin: 0 0 0.9rem; max-width: 24ch;
}
.ml-hero-tagline .hl { color: var(--accent); }
.ml-hero-sub { color: var(--dim); font-size: 1rem; line-height: 1.62; max-width: 60ch; }

/* live flagship panel — fills the hero's right column, echoes the tape's "alive" feel */
.ml-hero-panel {
  border: 1px solid var(--line); border-radius: 14px; padding: 18px 20px;
  background:
    radial-gradient(320px 120px at 82% 0%, rgba(72,167,230,0.08), transparent 70%),
    linear-gradient(180deg, var(--panel-2), var(--panel));
}
.ml-hero-panel-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.ml-hero-panel-code {
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.06em;
  color: var(--dim); text-transform: uppercase;
}
.ml-live {
  display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-mono);
  font-size: 0.64rem; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--up);
}
.ml-live-dot { width: 6px; height: 6px; border-radius: 999px; background: var(--up); box-shadow: 0 0 0 3px rgba(63,182,139,0.16); }
.ml-hero-panel-val {
  font-family: var(--font-ui); font-size: 1.74rem; font-weight: 600; color: var(--paper-strong);
  letter-spacing: -0.01em; font-variant-numeric: tabular-nums;
}
.ml-hero-panel-chg { font-family: var(--font-ui); font-size: 0.8rem; font-weight: 500; margin-top: 2px; font-variant-numeric: tabular-nums; }
.ml-spark { width: 100%; height: 58px; display: block; margin: 12px 0 8px; }
.ml-spark polyline { stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.ml-spark-up { stroke: var(--up); }
.ml-spark-down { stroke: var(--down); }
.ml-hero-panel-foot { font-family: var(--font-mono); font-size: 0.66rem; letter-spacing: 0.04em; color: var(--dim); }

/* ---- section label (home) -------------------------------------------- */
.ml-section-label {
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--dim);
  margin: 2.2rem 0 0.9rem; padding-bottom: 0.55rem; border-bottom: 1px solid var(--line-soft);
}
.ml-section-label .idx { color: var(--accent); margin-right: 10px; }

/* ---- card grid -------------------------------------------------------- */
.ml-grid { display: grid; gap: 14px; }
.ml-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
@media (max-width: 900px) { .ml-grid-3 { grid-template-columns: 1fr; } }
.ml-card {
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid var(--line); border-radius: 12px; padding: 17px 18px;
  transition: border-color .15s ease, transform .15s ease;
}
.ml-card:hover { border-color: #34363f; transform: translateY(-1px); }

/* Module cards are real links laid out as a column so the "Open" affordance
   anchors to the card's base and fills the height (no dead space), and they
   lift on hover/focus. Keyboard focus uses the global :focus-visible ring.
   The [data-testid] scope beats Streamlit's own markdown-link styling
   (underline + link color), which would otherwise bleed across the card. */
[data-testid="stMarkdownContainer"] a.ml-card-nav,
[data-testid="stMarkdownContainer"] a.ml-card-nav:hover,
[data-testid="stMarkdownContainer"] a.ml-card-nav:focus-visible {
  text-decoration: none; color: var(--paper);
}
.ml-card-nav { display: flex; flex-direction: column; height: 100%; cursor: pointer; }
.ml-card-nav:hover { border-color: var(--accent); }
.ml-card-nav:hover .ml-card-title { color: var(--accent); }
.ml-card-go {
  display: inline-flex; align-items: center; gap: 5px; margin-top: auto; padding-top: 16px;
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500;
  letter-spacing: 0.04em; color: var(--dim); transition: color .15s ease;
}
.ml-card-nav:hover .ml-card-go, .ml-card-nav:focus-visible .ml-card-go { color: var(--accent); }
.ml-card-go .arw { transition: transform .18s cubic-bezier(.2,.7,.3,1); }
.ml-card-nav:hover .ml-card-go .arw { transform: translateX(3px); }
.ml-card-code {
  font-family: var(--font-mono); font-size: 0.68rem; letter-spacing: 0.08em;
  color: var(--accent); margin-bottom: 9px; font-weight: 500;
}
.ml-card-title { font-family: var(--font-display); font-weight: 600; color: var(--paper-strong);
  font-size: 1.02rem; margin-bottom: 6px; }
.ml-card-desc { color: var(--dim); font-size: 0.85rem; line-height: 1.5; }
.ml-card-eyebrow {
  font-family: var(--font-mono); color: var(--dim); font-size: 0.68rem; text-transform: uppercase;
  letter-spacing: 0.1em; font-weight: 500; margin-bottom: 11px;
}
.ml-cov-list { list-style: none; padding: 0; margin: 0; }
.ml-cov-list li {
  color: var(--paper); font-size: 0.9rem; padding: 5px 0 5px 15px; position: relative;
  display: flex; align-items: baseline; gap: 8px;
}
.ml-cov-list li .mcode {
  font-family: var(--font-mono); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.06em;
  color: var(--accent); margin-left: auto;
}
.ml-cov-list li .tkr {
  font-family: var(--font-mono); font-size: 0.7rem; color: var(--dim);
}
.ml-cov-list li::before {
  content: ""; position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 5px; height: 5px; border-radius: 999px; background: var(--accent); opacity: 0.8;
}

/* ---- KPI cards -------------------------------------------------------- */
/* Responsive KPI grid: roomy 6-up on wide screens, wraps to 3 then 2 so the
   numbers never crowd or clip (the old fixed 6 st.columns squeezed them). */
.ml-kpi-grid {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px; margin-bottom: 6px;
}
@media (max-width: 1200px) { .ml-kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 640px) { .ml-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
.ml-kpi {
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid var(--line); border-radius: 12px; padding: 18px 18px 16px;
  height: 100%; position: relative; overflow: hidden;
  transition: border-color .15s ease, transform .15s ease;
}
.ml-kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--accent); opacity: 0; transition: opacity .15s ease; }
.ml-kpi:hover { border-color: #34363f; transform: translateY(-1px); }
.ml-kpi:hover::before { opacity: 0.6; }
.ml-kpi .lbl {
  font-family: var(--font-mono); color: var(--dim); font-size: 0.66rem; text-transform: uppercase;
  letter-spacing: 0.1em; margin-bottom: 11px; font-weight: 500; white-space: nowrap;
}
.ml-kpi .val { font-family: var(--font-ui); font-size: 1.46rem; font-weight: 600;
  line-height: 1.04; color: var(--paper-strong); letter-spacing: -0.02em; }
.ml-kpi .sub { font-size: 0.8rem; margin-top: 6px; font-weight: 500; font-family: var(--font-mono);
  font-variant-numeric: tabular-nums; }
.ml-kpi .sub .sep { color: var(--dim); }
.ml-up { color: var(--up); } .ml-down { color: var(--down); } .ml-flat { color: var(--dim); }

/* ---- st.metric as a card --------------------------------------------- */
[data-testid="stMetric"] {
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px 12px;
}
[data-testid="stMetricLabel"] p {
  font-family: var(--font-mono); color: var(--dim); font-size: 0.66rem !important;
  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500;
}
[data-testid="stMetricValue"] { font-family: var(--font-ui); font-size: 1.4rem; font-weight: 600;
  color: var(--paper-strong); letter-spacing: -0.02em; }
[data-testid="stMetricDelta"] { font-size: 0.8rem; font-weight: 500; font-family: var(--font-mono); }

/* ---- badges ----------------------------------------------------------- */
.ml-badge { display: inline-flex; align-items: center; gap: 6px; padding: 3px 11px; border-radius: 6px;
  font-family: var(--font-mono); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.04em;
  border: 1px solid transparent; text-transform: uppercase; }
.ml-badge::before { content: ""; width: 6px; height: 6px; border-radius: 999px; background: currentColor; }
.ml-badge-bull { background: rgba(63,182,139,0.12); color: var(--up); border-color: rgba(63,182,139,0.3); }
.ml-badge-bear { background: rgba(229,72,77,0.12); color: var(--down); border-color: rgba(229,72,77,0.3); }
.ml-badge-neutral { background: rgba(138,139,132,0.12); color: #b6b7af; border-color: rgba(138,139,132,0.28); }
.ml-badge-low { background: rgba(63,182,139,0.12); color: var(--up); border-color: rgba(63,182,139,0.3); }
.ml-badge-normal { background: var(--accent-dim); color: var(--accent); border-color: rgba(72,167,230,0.3); }
.ml-badge-high { background: rgba(229,72,77,0.12); color: var(--down); border-color: rgba(229,72,77,0.3); }
.ml-caption { color: var(--dim); font-size: 0.8rem; line-height: 1.55; }

/* ---- closing invitation (peak-end) ------------------------------------ */
[data-testid="stMarkdownContainer"] a.ml-cta,
[data-testid="stMarkdownContainer"] a.ml-cta:hover { text-decoration: none; }
.ml-cta {
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  margin: 2.4rem 0 0.4rem; padding: 20px 22px; border-radius: 14px;
  border: 1px solid var(--line); text-decoration: none;
  background:
    radial-gradient(420px 150px at 88% 50%, rgba(72,167,230,0.10), transparent 70%),
    linear-gradient(180deg, var(--panel-2), var(--panel));
  transition: border-color .15s ease, transform .15s ease;
}
.ml-cta:hover { border-color: var(--accent); transform: translateY(-1px); text-decoration: none; }
.ml-cta-text { display: flex; flex-direction: column; gap: 4px; }
.ml-cta-kicker {
  font-family: var(--font-mono); font-size: 0.68rem; font-weight: 500; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--accent);
}
.ml-cta-title {
  font-family: var(--font-display); font-size: 1.18rem; font-weight: 600;
  color: var(--paper-strong); letter-spacing: -0.02em;
}
.ml-cta-go {
  flex: none; display: inline-flex; align-items: center; gap: 7px;
  font-family: var(--font-mono); font-size: 0.82rem; font-weight: 500; color: var(--accent);
  white-space: nowrap;
}
.ml-cta-go .arw, .ml-card-go .arw { display: inline-block; }
.ml-cta:hover .ml-cta-go .arw { transform: translateX(3px); }
.ml-cta-go .arw { transition: transform .18s cubic-bezier(.2,.7,.3,1); }
@media (max-width: 640px) {
  .ml-cta { flex-direction: column; align-items: flex-start; gap: 14px; }
}

/* ---- footer ----------------------------------------------------------- */
.ml-footer { margin-top: 2.4rem; padding-top: 1.1rem; border-top: 1px solid var(--line-soft);
  color: var(--dim); font-size: 0.8rem; line-height: 1.6; max-width: 92ch; }
.ml-footer b { color: var(--paper); }

/* ---- sidebar ---------------------------------------------------------- */
[data-testid="stSidebar"] { background: #0d0e11; border-right: 1px solid var(--line-soft); }
[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }
[data-testid="stSidebarNav"] a { border-radius: 8px; margin: 1px 6px; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.035); }
/* Active page: a clean blue-tinted fill and accent-coloured label — no left bar. */
[data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--accent-dim); }
[data-testid="stSidebarNav"] a[aria-current="page"] span,
[data-testid="stSidebarNav"] a[aria-current="page"] p { color: var(--accent) !important; font-weight: 600; }
/* Keyboard focus on nav links stays visible but subtle (not a heavy outline box). */
[data-testid="stSidebarNav"] a:focus-visible {
  outline: none; background: var(--accent-dim); box-shadow: inset 0 0 0 1px rgba(72,167,230,0.45);
}
[data-testid="stSidebar"] h3 { font-family: var(--font-mono); font-size: 0.68rem !important;
  text-transform: uppercase; letter-spacing: 0.14em; color: var(--dim); font-weight: 500; margin-bottom: 0.3rem; }

/* Sidebar: a full-height flex chain so the brand footer anchors to the bottom
   instead of leaving the nav trailing into empty space. Driving it from the
   content container (flex:1 fills the space under the nav) avoids viewport-math
   guesses. Flexbox (not height:100%) sidesteps percentage-height issues through
   Streamlit's nested wrappers; `>` scoping leaves nested page column blocks alone. */
[data-testid="stSidebarContent"] { display: flex; flex-direction: column; }
[data-testid="stSidebarUserContent"] {
  flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;
  /* Streamlit ships ~96px of bottom padding here, which reads as dead space
     under the pinned footer — trim it so the footer hugs the sidebar bottom. */
  padding-bottom: 20px;
}
[data-testid="stSidebarUserContent"] > div {
  flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;
}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] { flex: 1 1 auto; }
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"]
  > [data-testid="stElementContainer"]:last-child { margin-top: auto; }
.ml-side-foot { padding-top: 18px; border-top: 1px solid var(--line-soft); }
.ml-side-brand {
  display: flex; align-items: center; gap: 8px; font-family: var(--font-display);
  font-weight: 600; font-size: 1rem; letter-spacing: -0.01em; color: var(--paper-strong);
}
.ml-side-brand .dmd { color: var(--accent); font-size: 0.8rem; }
.ml-side-tag {
  font-family: var(--font-mono); font-size: 0.6rem; font-weight: 500; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--accent); margin: 5px 0 11px;
}
.ml-side-note { font-size: 0.72rem; line-height: 1.55; color: var(--dim); }

/* ---- tabs ------------------------------------------------------------- */
[data-testid="stTabs"] [role="tablist"] { gap: 2px; border-bottom: 1px solid var(--line-soft); }
[data-testid="stTab"] { color: var(--dim); padding: 6px 14px; border-radius: 8px 8px 0 0; }
[data-testid="stTab"] p { font-family: var(--font-mono); font-weight: 500; font-size: 0.82rem;
  letter-spacing: 0.03em; color: var(--dim); }
[data-testid="stTab"]:hover { background: rgba(255,255,255,0.03); }
[data-testid="stTab"]:hover p { color: var(--paper); }
[data-testid="stTab"][aria-selected="true"] { box-shadow: inset 0 -2px 0 var(--accent); }
[data-testid="stTab"][aria-selected="true"] p { color: var(--paper-strong); }

/* ---- inputs / widgets ------------------------------------------------- */
[data-testid="stDateInput"] input, [data-testid="stNumberInput"] input,
[data-baseweb="select"] > div, [data-baseweb="input"] { border-radius: 8px !important; }
.stButton button { border-radius: 8px; border: 1px solid var(--line); font-weight: 500;
  background: var(--panel-2); color: var(--paper); font-family: var(--font-ui); }
.stButton button:hover { border-color: var(--accent); color: var(--paper-strong); }

/* ---- dataframe / expander -------------------------------------------- */
[data-testid="stDataFrame"] { border: 1px solid var(--line-soft); border-radius: 10px; }
[data-testid="stExpander"] { border: 1px solid var(--line-soft); border-radius: 10px; background: var(--panel); }

hr { border-color: var(--line-soft); }
[data-testid="stAlert"] { border-radius: 10px; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #2c2e36; border-radius: 8px; }
::-webkit-scrollbar-track { background: transparent; }
</style>
"""


def setup_page(title: str, icon: str = "◆") -> None:
    # Under the st.navigation router the entrypoint sets page config first, so a
    # page's own call is a duplicate — ignore that and still inject the theme CSS.
    try:
        st.set_page_config(page_title=f"MarketLens · {title}", page_icon=icon, layout="wide")
    except Exception:  # noqa: BLE001 - already configured this run by the router
        pass
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", section: str = "") -> None:
    """Branded page header: mono eyebrow, display title, accent rule."""
    eyebrow = "MARKETLENS" + (f" · {section.upper()}" if section else "")
    sub = f'<div class="ml-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="ml-page-header"><div class="ml-eyebrow">{eyebrow}</div>'
        f'<div class="ml-title">{title}</div>{sub}'
        f'<div class="ml-rule"></div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
def fmt_pct(x: float, digits: int = 2, signed: bool = False) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x * 100:+.{digits}f}%" if signed else f"{x * 100:.{digits}f}%"


def fmt_num(x: float, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"{x:,.{digits}f}"


def fmt_ratio(x: float, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, float) and math.isinf(x):
        return "∞"
    return f"{x:.{digits}f}"


def color_class(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "ml-flat"
    if x > 0:
        return "ml-up"
    if x < 0:
        return "ml-down"
    return "ml-flat"


def kpi_card(label: str, value: str, sub: str = "", sub_class: str = "ml-flat") -> str:
    sub_html = f'<div class="sub {sub_class}">{sub}</div>' if sub else ""
    return (
        f'<div class="ml-kpi"><div class="lbl">{label}</div>'
        f'<div class="val">{value}</div>{sub_html}</div>'
    )


def trend_badge(trend: str) -> str:
    cls = {"Bullish": "ml-badge-bull", "Bearish": "ml-badge-bear"}.get(trend, "ml-badge-neutral")
    return f'<span class="ml-badge {cls}">{trend}</span>'


def regime_badge(regime: str) -> str:
    cls = {"Low": "ml-badge-low", "Normal": "ml-badge-normal", "High": "ml-badge-high"}.get(
        regime, "ml-badge-neutral"
    )
    return f'<span class="ml-badge {cls}">{regime} volatility</span>'
