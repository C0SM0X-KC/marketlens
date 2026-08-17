# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are **students and self-learners** studying financial markets and
quantitative methods. They come to explore and understand — running returns,
risk, correlation, event-study, and backtesting analysis hands-on to build
intuition — rather than to execute trades or manage real money. They are
comfortable with a data-dense, desk-style interface but are still learning the
concepts the tool surfaces.

## Product Purpose

MarketLens is a global financial-markets research terminal. It pulls live prices
for a set of equity indices, commodities, and FX pairs, then runs the analysis a
research desk actually uses — returns, volatility, drawdown, correlation, macro
event studies, and rule-based strategy backtests measured against a
buy-and-hold benchmark. Success is a learner being able to move from raw market
data to a defensible, data-driven read of an asset or strategy without writing
code themselves.

It is explicitly a research and learning tool, **not** an autonomous trading
system, and it does not predict prices.

## Positioning

The differentiating mechanism is desk-grade analytical rigor applied to an
educational tool: real live data, honest out-of-sample backtesting with
transaction-cost and slippage modeling, and analysis primitives named and
structured the way a working research desk uses them — while staying transparent
that it forecasts nothing. It sits between a toy stock-charting demo (which it
out-analyzes) and a professional trading terminal (whose execution and
prediction claims it deliberately refuses to make).

## Operating Context

- Delivered as a Streamlit multipage web app; run locally via
  `streamlit run app/streamlit_app.py`.
- Workspace is organized as parallel research modules, not a linear flow:
  Market Overview, Asset Analysis, Cross-Market, Macro Events, Strategy Lab, and
  Research Snapshot.
- Users choose assets and date ranges from a per-page sidebar.
- Data is fetched on demand from Yahoo Finance and cached locally to disk.

## Capabilities and Constraints

- **Coverage (current, not locked):** six instruments across three asset
  classes — S&P 500 (SPX), Nasdaq-100 (NDX), NIFTY 50, Gold (XAU), Crude Oil WTI,
  USD/INR. The set may grow; nothing fixes it at six.
- **Data source (current, not locked):** live prices from Yahoo Finance via
  `yfinance`, cached locally with a configurable TTL. Not contractually fixed,
  but the only source wired today.
- **Analysis:** returns, rolling/annualized volatility, drawdown, trend
  classification, volatility-percentile regime detection, correlation (static and
  rolling), macro event studies over a T−5…T+5 window, and an auto-generated
  research summary.
- **Backtesting:** MA-crossover and RSI mean-reversion strategies against a
  buy-and-hold benchmark, with transaction-cost and slippage modeling and a
  dev / out-of-sample split.
- **Optional:** a news/sentiment module gated on `NEWS_API_KEY`; the core app
  works fully without it.
- Tunable parameters, asset metadata, and analysis assumptions are centralized in
  `src/config.py` rather than scattered.
- Terminology in the UI uses desk shorthand (e.g. desk codes SPX/NDX/XAU/WTI, ρ
  for correlation, T−5…T+5 windows).

## Evidence on Hand

- Real, working analysis and backtesting code under `src/` with a substantial
  passing test suite under `tests/`.
- Live market data (no synthetic/seed prices), sourced from Yahoo Finance.
- `data/macro_events.csv` supplies the macro event calendar.
- **No** testimonials, user counts, customer logos, benchmarks-vs-competitors,
  pricing, or press exist yet — future work must not fabricate any of these.

## Product Principles

- **Rigor over reassurance.** Show honest, out-of-sample, cost-aware results even
  when they are unflattering; never imply certainty the data does not support.
- **Teach by transparency.** Name and structure analysis the way a real desk does
  so learners absorb the mental model, not just an output number.
- **Research, never prediction.** Every surface stays inside the "analyze the
  past, don't forecast the future" boundary; keep the educational, not-advice
  framing present and truthful.
- **Density with legibility.** Serve users who want data-dense, desk-style views
  without sacrificing scanability and comprehension for people still learning.

## Accessibility & Inclusion

No product-specific accessibility standard has been established as binding.
Apply strong general accessibility craft as a default; record a formal standard
here if one is later required.
