# MarketLens

**A global-markets research terminal — live prices, desk-grade analysis, and honest strategy backtesting.**

MarketLens pulls live market data for equity indices, commodities and FX, then runs the
quantitative analysis a research desk actually uses — returns, volatility, drawdown,
correlation, volatility-regime detection and macro event studies — and lets you backtest
rule-based strategies against a buy-and-hold benchmark. It is built for **students and
self-learners** who want to move from raw prices to a defensible, data-driven read of a
market or strategy, without writing code themselves.

> **It is a research and learning tool — not an autonomous trading system, and it does not
> predict prices.** Every figure is computed from historical market data.

<sub>Built with Python · pandas · NumPy · SciPy · Streamlit · Plotly · yfinance · pytest</sub>

---

## Features

MarketLens is organised as six parallel research modules:

| Module | What it does |
| --- | --- |
| **Market Overview** | Cross-asset KPIs — returns, volatility, trend and regime at a glance, plus normalised comparative performance. |
| **Asset Analysis** | Single-instrument breakdown: price structure, moving averages, momentum (RSI/MACD), Bollinger bands and drawdowns. |
| **Cross-Market** | Correlation matrix, rolling correlation between any two instruments, and comparative cumulative returns. |
| **Macro Events** | Event studies measuring average market behaviour in a **T−5 … T+5** window around economic releases. |
| **Strategy Lab** | Backtests moving-average-crossover and RSI mean-reversion strategies vs. buy-and-hold, with costs and an out-of-sample split. |
| **Research Summary** | An automatically generated, metrics-only market write-up. |

**Analytical highlights**

- **Cost-aware, out-of-sample backtesting** — transaction costs and slippage are modelled in
  basis points, and strategies are evaluated on a held-out period they were never fit on,
  a deliberate guard against the classic overfitting trap.
- **Volatility-percentile regime detection** — classifies the current market as low / normal
  / high volatility from a rolling percentile.
- **Local caching** — prices are cached to disk with a configurable TTL, so repeat runs are
  fast and the app degrades gracefully when live data is unavailable.

---

## Coverage

| Asset class | Instruments |
| --- | --- |
| Equity Index | S&P 500 (SPX), Nasdaq-100 (NDX), NIFTY 50 |
| Commodity | Gold (XAU), Crude Oil — WTI |
| FX | USD/INR |

Prices are sourced from **Yahoo Finance** via [`yfinance`](https://github.com/ranaroussi/yfinance).

---

## Getting started

**Prerequisites:** Python 3.11+

```bash
# 1. Clone
git clone https://github.com/C0SM0X-KC/marketlens.git
cd marketlens

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) configure environment
cp .env.example .env        # then edit if needed

# 5. Run
streamlit run app/streamlit_app.py
```

The app opens at `http://localhost:8501`.

---

## Configuration

Copy `.env.example` to `.env`. All settings are optional — the core app runs without any:

| Variable | Purpose | Default |
| --- | --- | --- |
| `MARKETLENS_CACHE_TTL_HOURS` | How long downloaded price data is cached before refetching. | `12` |
| `NEWS_API_KEY` | API key for an optional news/sentiment provider. The core app works fully without it. | _(empty)_ |

All tunable parameters — assets, analysis assumptions, strategy defaults and the cost model —
live in one place: [`src/config.py`](src/config.py).

---

## Project structure

```
marketlens/
├── app/                      # Streamlit UI
│   ├── streamlit_app.py      # entrypoint + st.navigation router + home page
│   ├── components/           # theme (Phosphor), Plotly chart builders, shared widgets
│   └── pages/                # the six analysis pages
├── src/                      # analytics engine (framework-agnostic, tested)
│   ├── config.py             # central configuration & asset metadata
│   ├── data/                 # loading, caching, cleaning
│   ├── analysis/             # returns, volatility, drawdown, correlation, trend, regime, summary
│   ├── technical/            # moving averages, momentum, volatility indicators
│   ├── strategies/           # rule-based strategy definitions
│   ├── backtesting/          # engine, metrics, transaction-cost model
│   └── macro/                # macro events + event-study analysis
├── tests/                    # pytest suite for the analytics engine
├── data/                     # macro_events.csv + local price cache (gitignored)
└── requirements.txt
```

The analytics in `src/` are deliberately kept independent of the UI, so they can be tested
and reused on their own.

---

## Testing

```bash
pytest
```

The suite covers returns, volatility, drawdown, correlation, technical indicators, strategies
and the backtest engine.

---

## Disclaimer

MarketLens is an **educational research tool**. Nothing in it is investment advice, a
recommendation, or a guarantee of future performance. All figures are computed from historical
market data sourced from Yahoo Finance. Do your own research.
