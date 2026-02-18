# Meridian — Smart Money Intelligence Platform

> Where smart money signals converge.

Meridian tracks and analyzes institutional investment signals across **US, CN, and HK markets** — fusing Congress trades, ARK Invest flows, dark pool anomalies, and 13F filings into a single cross-signal intelligence engine.

---

## ✨ Features

### US Market Intelligence
- **Congress Trading** — Track House & Senate stock trades with performance attribution
- **ARK Invest** — Real-time ARK ETF trade monitoring and conviction analysis
- **Dark Pool** — Off-exchange volume anomaly detection with Z-score signals
- **Institutions (13F)** — Quarterly institutional holdings from top hedge funds
- **Cross-Signal Engine** — Multi-source confluence scoring with conviction ranking

### Asia Markets
- **HK VMQ Signals** — Value-Momentum-Quality stock picks for Hong Kong market
- **CN Trend Filter** — A-share market regime detection (bull/bear)
- **CN 12×30 Strategy** — Quantitative momentum strategy with backtesting

### Research & Screening
- **Ticker Deep Dive** — Aggregate all signals for any ticker
- **Dividend Screener** — Cross-market dividend stock screening (US/HK/CN)
- **Fundamental Research** — AI-powered stock analysis reports

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12) |
| **Frontend** | SvelteKit 5 + Tailwind CSS |
| **Data** | DuckDB + JSON cache |
| **Charts** | Lightweight Charts (TradingView) + ECharts |
| **Data Sources** | Quiver Quant API, SEC EDGAR, ARK Invest |
| **Infra** | Docker Compose, GitHub Actions CI/CD |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/your-org/meridian.git
cd meridian

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
docker compose up --build -d

# Access
# API:      http://localhost:8501
# Frontend: http://localhost:3000
# API Docs: http://localhost:8501/docs
```

---

## 📁 Architecture

```
meridian/
├── api/                    # FastAPI backend
│   ├── routers/            # API endpoints (us, cn, hk, ticker, dividend)
│   ├── modules/            # Business logic (cross-signal engine, scorer, cache)
│   ├── collectors/         # Data collectors (ark, congress, darkpool, institutions)
│   ├── cron/               # Scheduled data refresh jobs
│   ├── main.py             # App entry point
│   └── config.py           # All configuration
├── frontend/
│   └── sveltekit/          # SvelteKit frontend
│       ├── src/routes/     # Page routes
│       └── src/lib/        # Components, stores, types, utils
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── docker-compose.yml      # Production deployment
├── Dockerfile              # API container build
└── .env.example            # Environment template
```

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/congress/trades` | Congress stock trades |
| `GET /api/ark/trades` | ARK Invest trades |
| `GET /api/ark/holdings` | ARK ETF holdings |
| `GET /api/darkpool/analytics` | Dark pool anomalies |
| `GET /api/institutions/filings` | 13F institutional filings |
| `GET /api/signals/confluence` | Cross-signal confluence |
| `GET /api/signals/smart-money` | Smart money composite signals |
| `GET /api/ticker/{symbol}` | Ticker aggregate deep dive |
| `GET /api/hk/signals` | HK VMQ stock picks |
| `GET /api/cn/trend` | CN market trend signal |
| `GET /api/cn/8x30/*` | CN 12×30 strategy endpoints |
| `GET /api/dividend-screener` | Multi-market dividend screen |

All endpoints support `Accept: text/markdown` for agent-friendly Markdown responses.

---

## ⚙️ Configuration

See `.env.example` for all required environment variables. Key settings:

- `QUIVER_API_KEY` — Quiver Quant API key for US market data
- `SIGNALS_DIR` — Path to signal data files
- `ARK_DATA_DIR` — Path to ARK trade data
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — Optional alert notifications

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -q

# Lint
ruff check api/ tests/
```

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

*Built with conviction tracking in mind. Not financial advice.*
