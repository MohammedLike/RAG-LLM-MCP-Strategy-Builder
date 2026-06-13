# Quant AI Agent Platform — Project Report

**Prepared by:** [Your Name]
**Date:** June 2026
**Project:** Streak AI Quant — Intelligent Algorithmic Trading & Backtesting Platform
**Status:** ✅ Active / Running

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [How I Built It — Step by Step](#5-how-i-built-it--step-by-step)
6. [Data Pipeline](#6-data-pipeline)
7. [Database Design](#7-database-design)
8. [Backend — API & Services](#8-backend--api--services)
9. [AI Agent & LLM Integration](#9-ai-agent--llm-integration)
10. [Backtesting Engine](#10-backtesting-engine)
11. [RAG — Knowledge Base](#11-rag--knowledge-base)
12. [MCP — Tool Protocol](#12-mcp--tool-protocol)
13. [Frontend UI](#13-frontend-ui)
14. [Strategy Library](#14-strategy-library)
15. [Running the Platform](#15-running-the-platform)
16. [Key Results & Metrics](#16-key-results--metrics)
17. [Challenges & Solutions](#17-challenges--solutions)

---

## 1. Executive Summary

This project is a **full-stack AI-powered quantitative trading platform** built from scratch for the Indian stock market (NSE/BSE). It combines a local Large Language Model (LLM), a high-performance backtesting engine, a real-time market data pipeline, a vector database for strategy retrieval, and a professional React dashboard — all running **100% locally** without any paid cloud APIs.

The platform allows a user to:
- Type natural language like *"backtest NIFTY when RSI crosses below 30"* and instantly get a full backtest report
- Build multi-condition strategies visually using 40+ technical indicators
- Run options backtests (Straddle, Strangle, Iron Condor) on NIFTY/BANKNIFTY
- View equity curves, drawdown charts, monthly return heatmaps, and trade logs
- Compare multiple strategies side-by-side
- Use an AI chat panel powered by a local DeepSeek model

---

## 2. Project Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUANT AI AGENT PLATFORM                      │
│                                                                 │
│   "Talk to your trading strategy in plain English"              │
│                                                                 │
│   Indian Markets (NSE / BSE)  ·  Local LLM  ·  No Cloud APIs  │
└─────────────────────────────────────────────────────────────────┘
```

| Dimension        | Detail                                                  |
|------------------|---------------------------------------------------------|
| Domain           | Quantitative Trading / Financial AI                    |
| Market Focus     | NSE & BSE (Indian Stock Market)                        |
| LLM Provider     | Ollama (local) — DeepSeek R1 8B / 14B                  |
| Backend          | Python · FastAPI · LangGraph · VectorBT                |
| Frontend         | React 19 · TypeScript · Vite · Tailwind CSS v4         |
| Database         | PostgreSQL (TimescaleDB) + Redis + Qdrant              |
| Instruments      | Equity, Options (CE/PE/Straddle/Strangle)              |

---

## 3. System Architecture

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                │
│                    React 19 + TypeScript + Vite                          │
│   ┌─────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│   │  AI Chat    │  │ Strategy Builder │  │   Backtest Dashboard     │   │
│   │  Panel      │  │  (Visual Rules)  │  │  (Charts + Trade Log)    │   │
│   └──────┬──────┘  └────────┬─────────┘  └───────────┬──────────────┘   │
└──────────┼──────────────────┼────────────────────────┼──────────────────┘
           │                  │                        │
           ▼                  ▼                        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend  :8001                           │
│   /api/chat    /api/backtest    /api/market    /api/strategies           │
│                        /api/mcp                                          │
└──────┬─────────────────┬──────────────────┬──────────────────────────────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌────────────┐  ┌────────────────┐  ┌─────────────────────────────────┐
│  LangGraph │  │  MCP Server    │  │       Market Data Layer         │
│  AI Agent  │  │  Tool Router   │  │  YFinance / NSE / DB First      │
│            │  │                │  └────────────────┬────────────────┘
│ ┌────────┐ │  │ ┌────────────┐ │                   │
│ │Reason  │ │  │ │run_backtest│ │                   ▼
│ │  Node  │ │  │ │fetch_market│ │  ┌────────────────────────────────┐
│ └───┬────┘ │  │ │analyse_    │ │  │         PostgreSQL             │
│     │      │  │ │  greeks    │ │  │   (TimescaleDB)  :5432         │
│ ┌───▼────┐ │  │ │query_      │ │  │  Tables: ohlcv, options_chain  │
│ │Tool    │ │  │ │  strategy  │ │  │          strategies             │
│ │Call    │ │  │ └────────────┘ │  └────────────────────────────────┘
│ └───┬────┘ │  └────────────────┘
│     │      │                      ┌────────────────────────────────┐
│ ┌───▼────┐ │                      │      Qdrant Vector DB  :6333   │
│ │RAG     │ │◄─────────────────────│  Strategy embeddings (1024-dim)│
│ │Retrieve│ │                      │  mxbai-embed-large model       │
│ └───┬────┘ │                      └────────────────────────────────┘
│     │      │
│ ┌───▼────┐ │                      ┌────────────────────────────────┐
│ │Synth   │ │                      │        Redis Cache  :6379      │
│ │Node    │ │                      │   Backtest result TTL cache    │
│ └────────┘ │                      └────────────────────────────────┘
└────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│              Ollama LLM Server  :11434                 │
│         DeepSeek R1 8B  +  mxbai-embed-large           │
└────────────────────────────────────────────────────────┘
```

### Request Flow — Natural Language to Backtest

```
User types: "Backtest NIFTY RSI below 30 exit above 70"
        │
        ▼
  ┌─────────────┐     regex match      ┌──────────────────┐
  │  NL Parser  │──────────────────────►  Structured Spec  │
  └─────────────┘                      └────────┬─────────┘
        │ (no match)                            │
        ▼                                       │
  ┌─────────────┐     Ollama LLM call           │
  │  Reason Node│──────────────────────────────►│
  └─────────────┘                               │
                                                ▼
                                   ┌────────────────────────┐
                                   │  BacktestEngine.run()  │
                                   │  VectorBT Portfolio    │
                                   └────────────┬───────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │   Metrics + Equity     │
                                   │   Curve + Trade Log    │
                                   └────────────┬───────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │  React Dashboard       │
                                   │  Charts + KPIs render  │
                                   └────────────────────────┘
```

---

## 4. Technology Stack

### Backend

| Package              | Version    | Purpose                                    |
|----------------------|------------|--------------------------------------------|
| Python               | 3.11+      | Core language                              |
| FastAPI              | ≥0.111.0   | REST API framework                         |
| Uvicorn              | ≥0.30.1    | ASGI server                                |
| Pydantic v2          | ≥2.7.4     | Data validation & settings                 |
| SQLAlchemy 2         | ≥2.0.30    | Async ORM                                  |
| asyncpg              | ≥0.29.0    | Async PostgreSQL driver                    |
| VectorBT             | ≥0.25.6    | Vectorized backtesting engine              |
| LangChain            | ≥0.2.5     | LLM chain abstractions                     |
| LangGraph            | ≥0.0.66    | Agent state machine (DAG-based)            |
| Ollama               | ≥0.2.1     | Local LLM client                           |
| sentence-transformers| ≥3.0.1     | Embedding model support                    |
| qdrant-client        | ≥1.9.1     | Vector DB client                           |
| redis                | ≥5.0.6     | Async caching layer                        |
| yfinance             | ≥0.2.40    | Market data (YFinance fallback)            |
| pandas               | ≥2.2.2     | Data manipulation                          |
| numpy                | ≥1.26.4    | Numerical computing                        |
| scipy                | ≥1.13.1    | Options pricing (Black-Scholes)            |
| py-vollib            | ≥1.0.1     | Options greeks calculation                 |
| TA-Lib               | ≥0.4.32    | Technical analysis (optional native)       |
| mcp                  | ≥1.0.0     | Model Context Protocol                     |

### Frontend

| Package          | Version    | Purpose                              |
|------------------|------------|--------------------------------------|
| React            | 19.2.x     | UI framework                         |
| TypeScript       | ~6.0.2     | Type safety                          |
| Vite             | 8.x        | Build tool & dev server              |
| Tailwind CSS     | v4.3.0     | Utility-first styling                |
| Zustand          | 5.x        | Global state management              |
| Recharts         | 3.x        | Equity curves & chart components     |
| Axios            | 1.x        | HTTP client                          |
| Lucide React     | 1.x        | Icon system                          |

### Infrastructure

| Service      | Image / Tool          | Port  | Purpose                         |
|--------------|-----------------------|-------|---------------------------------|
| PostgreSQL   | TimescaleDB extension | 5432  | Time-series OHLCV data store    |
| Redis        | redis:alpine          | 6379  | Backtest result cache (TTL 1h)  |
| Qdrant       | qdrant/qdrant         | 6333  | Vector embeddings for RAG       |
| Ollama       | ollama/ollama         | 11434 | Local LLM + embedding server    |

---

## 5. How I Built It — Step by Step

### Phase 1 — Infrastructure Setup

```
Step 1: Set up Docker services
        └── PostgreSQL (TimescaleDB) for OHLCV time-series
        └── Redis for caching backtest results
        └── Qdrant for vector similarity search
        └── Ollama for running LLMs locally

Step 2: Pull LLM models via Ollama
        └── ollama pull deepseek-r1:8b
        └── ollama pull mxbai-embed-large

Step 3: Configure environment (.env)
        └── DATABASE_URL, REDIS_URL, QDRANT_URL
        └── OLLAMA_BASE_URL, LLM_MODEL_NAME
        └── MARKET_DATA_PROVIDER=yfinance
```

### Phase 2 — Database & Data Pipeline

```
Step 4: Design SQLAlchemy models
        └── OHLCV (time, symbol, resolution, OHLCV columns)
        └── OptionsChain (time, symbol, expiry, strike, CE/PE)
        └── Strategy (entry/exit rules as JSONB)

Step 5: Write ingestion scripts
        └── scripts/ingest_historical.py
            → Fetch 10-14 years of daily OHLCV via YFinance
            → Upsert into PostgreSQL with ON CONFLICT DO UPDATE
        └── scripts/ingest_all_nse.py
            → Bulk ingest 1800+ NSE-listed stocks
        └── scripts/ingest_options_chain.py
            → Ingest NSE options chain snapshots

Step 6: Write data read logic in YFinanceProvider
        └── DB-first: always check PostgreSQL first
        └── YFinance fallback if not in DB
        └── Parquet file cache (12hr TTL) for frequently used symbols
```

### Phase 3 — Backend API

```
Step 7: Build FastAPI application (main.py)
        └── CORS middleware (allow all origins for dev)
        └── Lifespan: init Qdrant collection on startup
        └── Global exception handler → JSON error responses
        └── Single api_router at /api prefix

Step 8: Build route modules
        └── routes_backtest.py  → POST /backtest, GET /indicators
        └── routes_chat.py      → POST /chat (AI agent interface)
        └── routes_market.py    → GET /market/{symbol}/quote
        └── routes_strategy.py  → GET/POST /strategies
        └── routes_mcp.py       → GET /mcp/tools, POST /mcp/execute
```

### Phase 4 — Backtesting Engine

```
Step 9: Build IndicatorManager (40+ indicators)
        └── Pure numpy/pandas implementations
        └── SMA, EMA, RSI, MACD, BBANDS, ATR, ADX, CCI, Stoch...
        └── Crossover detection (crosses_above / crosses_below)
        └── Optional TA-Lib native binding

Step 10: Build BacktestEngine using VectorBT
        └── evaluate_condition() — LHS vs RHS comparisons
        └── evaluate_rules() — AND/OR multi-condition logic
        └── vbt.Portfolio.from_signals() — vectorized simulation
        └── Extract: equity curve, drawdown, trades, all metrics

Step 11: Build OptionsEngine
        └── Black-Scholes pricing for CE/PE
        └── Strike resolution: ATM, OTM+1/+2, ITM-1/-2
        └── Straddle = CE + PE combined payoff
        └── Stop-loss & take-profit on premium percentage
```

### Phase 5 — AI Agent

```
Step 12: Build NL Parser (regex-first, fast path)
        └── Regex patterns for RSI, SMA crossover, options
        └── Heuristic fallback for other natural language
        └── Returns structured strategy_spec JSON

Step 13: Build LangGraph Agent (4 nodes)
        └── reason_node    → parse intent, plan tool calls
        └── tool_call_node → execute MCP tools
        └── rag_retrieve   → vector search in Qdrant
        └── synthesize     → final response generation

Step 14: Build MCP Server (Model Context Protocol)
        └── run_backtest       → runs BacktestEngine
        └── fetch_market_data  → gets live quotes
        └── analyse_greeks     → options greek calculations
        └── query_strategy     → searches strategy knowledge base
```

### Phase 6 — RAG Knowledge Base

```
Step 15: Build RAG pipeline
        └── chunker.py   → chunk strategy JSON into text segments
        └── embedder.py  → call mxbai-embed-large via Ollama API
        └── indexer.py   → batch upsert to Qdrant collection
        └── qdrant_client.py → search top-K similar strategies

Step 16: Seed strategies
        └── scripts/index_strategies.py → index all strategy JSONs
        └── seed_strategies.py → seed 7 template strategies to DB
        └── scripts/seed_auto_strategies.py → auto-generate variants
```

### Phase 7 — Frontend

```
Step 17: Scaffold React + Vite + TypeScript project
        └── Tailwind CSS v4 with @tailwindcss/vite plugin
        └── Zustand stores: backtestStore, chatStore, marketStore
        └── Axios api.ts service layer pointing to :8001

Step 18: Build UI components
        └── BacktestDashboard.tsx  → results display
        └── StrategyBuilder.tsx    → visual rule builder
        └── PredefinedStrategies.tsx → strategy gallery
        └── BacktestComparison.tsx → multi-strategy compare
        └── MonthlyReturnsHeatmap.tsx → calendar heatmap
        └── RollingMetricsChart.tsx   → rolling Sharpe/DD
        └── MonteCarloSimulation.tsx  → Monte Carlo paths
        └── TradeDistribution.tsx     → win/loss histogram
        └── ParameterOptimizer.tsx    → param sweep grid
        └── ChatPanel.tsx + ChatDrawer.tsx → AI chat
```

---

## 6. Data Pipeline

### Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA INGESTION PIPELINE                    │
│                                                                 │
│  NSE Website / YFinance API                                     │
│         │                                                       │
│         ▼                                                       │
│  scripts/ingest_historical.py                                   │
│    ├── YFinanceProvider.get_ohlcv()                            │
│    ├── Symbol mapping: NIFTY → ^NSEI, BANKNIFTY → ^NSEBANK     │
│    ├── Fetch: 10-14 years daily OHLCV                          │
│    └── Upsert → PostgreSQL ohlcv table                        │
│                                                                 │
│  scripts/ingest_all_nse.py                                      │
│    └── 1800+ NSE stocks via company_profiles.csv               │
│                                                                 │
│  scripts/ingest_options_chain.py                                │
│    └── NSE options chain snapshots → options_chain table       │
│                                                                 │
│  READ PATH (priority order):                                    │
│    1. PostgreSQL DB (fastest, if data exists)                  │
│    2. Parquet file cache (12hr TTL, local disk)                │
│    3. YFinance live API (fallback, slowest)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Symbol Mapping

| User Input  | YFinance Ticker | Exchange |
|-------------|-----------------|----------|
| NIFTY       | ^NSEI           | NSE      |
| BANKNIFTY   | ^NSEBANK        | NSE      |
| FINNIFTY    | CNXFIN.NS       | NSE      |
| SENSEX      | ^BSESN          | BSE      |
| RELIANCE    | RELIANCE.NS     | NSE      |
| TCS         | TCS.NS          | NSE      |
| HDFCBANK    | HDFCBANK.NS     | NSE      |

---

## 7. Database Design

### Schema

```
┌─────────────────────────────────────────────────────┐
│  TABLE: ohlcv  (TimescaleDB hypertable)             │
├────────────┬──────────────┬─────────────────────────┤
│ time       │ DateTime(TZ) │ PRIMARY KEY             │
│ symbol     │ String       │ PRIMARY KEY             │
│ resolution │ String       │ PRIMARY KEY ('1d','1m') │
│ open       │ Float        │                         │
│ high       │ Float        │                         │
│ low        │ Float        │                         │
│ close      │ Float        │                         │
│ volume     │ BigInteger   │                         │
└────────────┴──────────────┴─────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  TABLE: options_chain                               │
├────────────┬──────────────┬─────────────────────────┤
│ time       │ DateTime(TZ) │ PRIMARY KEY             │
│ symbol     │ String       │ PRIMARY KEY             │
│ expiry     │ Date         │ PRIMARY KEY             │
│ strike     │ Float        │ PRIMARY KEY             │
│ option_type│ String       │ PRIMARY KEY ('CE','PE') │
│ oi         │ BigInteger   │ Open Interest           │
│ volume     │ BigInteger   │                         │
│ iv         │ Float        │ Implied Volatility      │
│ ltp        │ Float        │ Last Traded Price       │
│ greeks_json│ JSONB        │ Delta, Gamma, Theta...  │
└────────────┴──────────────┴─────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  TABLE: strategies                                  │
├─────────────────┬──────────────────────────────────-┤
│ id              │ UUID (PK)                         │
│ name            │ String                            │
│ slug            │ String (unique)                   │
│ category        │ String                            │
│ hypothesis      │ Text                              │
│ entry_rules     │ JSONB                             │
│ exit_rules      │ JSONB                             │
│ risk_params     │ JSONB                             │
│ backtest_results│ JSONB                             │
│ created_at      │ DateTime                          │
└─────────────────┴───────────────────────────────────┘
```

### Caching Layer

```
┌────────────────────────────────────────────────────────┐
│                    CACHING STRATEGY                    │
│                                                        │
│  BacktestCache (backtest/cache.py)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Key: backtest:{symbol}:{period}:{strategy_md5}  │  │
│  │  TTL: 3600 seconds (1 hour)                      │  │
│  │                                                  │  │
│  │  L1: Redis (distributed, survives restarts)      │  │
│  │  L2: In-memory dict (fallback if Redis down)     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  YFinance Parquet Cache (market/provider_yfinance.py)  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Path: data/ohlcv_cache/{ticker}_{period}.parquet│  │
│  │  TTL: 12 hours                                   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 8. Backend — API & Services

### API Endpoints

```
BASE: http://localhost:8001/api

BACKTEST
  POST  /backtest                → Run synchronous backtest
  POST  /backtest/async          → Run async batch backtest
  GET   /backtest/async/{id}     → Poll async result
  GET   /backtest/latest         → Get last backtest result
  GET   /indicators              → List all available indicators

CHAT / AI AGENT
  POST  /chat                    → Send message to LangGraph agent

MARKET DATA
  GET   /market/{symbol}/quote   → Live quote for symbol
  GET   /market/companies        → List of all NSE companies

STRATEGIES
  GET   /strategies              → List all saved strategies
  POST  /strategies              → Save new strategy

MCP TOOLS
  GET   /mcp/tools               → List available MCP tools
  POST  /mcp/execute             → Execute a specific MCP tool
```

### Backtest Request Format

```json
POST /api/backtest
{
  "symbol": "NIFTY",
  "period": "2y",
  "strategy_spec": {
    "entry": {
      "conditions": [
        {
          "indicator": "RSI",
          "params": { "timeperiod": 14 },
          "operator": "<",
          "value": 30
        }
      ],
      "logical_operator": "AND"
    },
    "exit": {
      "conditions": [
        {
          "indicator": "RSI",
          "params": { "timeperiod": 14 },
          "operator": ">",
          "value": 70
        }
      ],
      "logical_operator": "AND"
    },
    "fees": 0.001,
    "slippage": 0.001
  }
}
```

### Backtest Response Format

```json
{
  "symbol": "NIFTY",
  "period": "2y",
  "total_return": 12.45,
  "benchmark_return": 8.21,
  "cagr": 6.10,
  "calmar": 0.85,
  "sharpe": 1.24,
  "sortino": 1.87,
  "max_drawdown": -7.18,
  "win_rate": 62.5,
  "profit_factor": 1.45,
  "expectancy": 230.5,
  "total_trades": 8,
  "equity_curve": [
    { "date": "2024-01-02", "value": 10000.0 }, "..."
  ],
  "drawdown": [
    { "date": "2024-01-02", "value": 0.0 }, "..."
  ],
  "trades": [
    {
      "id": 0,
      "entry_date": "2024-01-15",
      "exit_date": "2024-02-10",
      "direction": "Long",
      "entry_price": 21450.5,
      "exit_price": 22100.0,
      "pnl": 649.5,
      "pnl_pct": 3.03,
      "size": 1.0,
      "duration_days": "26 days"
    }
  ]
}
```

---

## 9. AI Agent & LLM Integration

### LangGraph Agent — 4-Node State Machine

```
                    ┌─────────────────────────────────┐
                    │      AgentState (TypedDict)      │
                    │  messages: list[BaseMessage]     │
                    │  tool_calls: list[dict]          │
                    │  tool_results: list[dict]        │
                    │  retrieved_context: list[str]    │
                    └─────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │   ENTRY POINT    │
                          │   reason_node    │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │  has tool_calls?                │
                    │                                 │
              YES ──┘                        NO ──────┘
              │                                       │
              ▼                                       ▼
     ┌─────────────────┐                   ┌──────────────────┐
     │  tool_call_node │                   │  rag_retrieve    │
     │                 │                   │  (always runs)   │
     │  Executes MCP   │                   │                  │
     │  tools via      │                   │  Embed query →   │
     │  MCPServer      │                   │  Qdrant search   │
     └────────┬────────┘                   └────────┬─────────┘
              │                                     │
              └──────────────┬──────────────────────┘
                             │
                             ▼
                   ┌──────────────────────┐
                   │    synthesize_node   │
                   │                     │
                   │  Combines:          │
                   │  · Tool results     │
                   │  · RAG context      │
                   │  · LLM final answer │
                   └──────────┬──────────┘
                              │
                              ▼
                           ── END ──
```

### LLM Models Used

| Model                | Role              | Provider | Size  |
|----------------------|-------------------|----------|-------|
| deepseek-r1:8b       | Reasoning & chat  | Ollama   | ~5GB  |
| mxbai-embed-large    | Text embeddings   | Ollama   | ~670MB|

### NL Parser — Fast Path (before LLM)

The system first tries regex patterns before calling the LLM, making common queries instant:

```
Input: "backtest NIFTY RSI below 30"
         │
         ▼
   NLParser.parse()
         │
   ┌─────┴──────────────────────────────────┐
   │  Pattern: rsi_mean_reversion           │
   │  regex match → build strategy_spec    │
   │  → skip LLM entirely (fast path)      │
   └────────────────────────────────────────┘
         │
         ▼
   BacktestEngine.run() immediately
```

Patterns handled by regex (no LLM needed):
- RSI mean reversion (RSI < X / RSI > Y)
- SMA/EMA crossover (SMA 20 crosses above SMA 50)
- Options strategies (ATM Straddle, OTM Strangle, Iron Condor)

---

## 10. Backtesting Engine

### Equity Backtest Flow

```
strategy_spec JSON
        │
        ▼
BacktestEngine.run(df, strategy_spec)
        │
        ├── evaluate_rules(df, entry_spec)
        │     └── evaluate_condition() for each condition
        │           ├── Compute LHS indicator (RSI, SMA, etc.)
        │           ├── Compute RHS (scalar or indicator)
        │           └── Apply operator (<, >, crosses_above...)
        │
        ├── evaluate_rules(df, exit_spec)
        │
        ├── vbt.Portfolio.from_signals(
        │       close, entries, exits,
        │       sl_stop, tp_stop, fees, slippage, freq='D')
        │
        └── Extract metrics:
              ├── Total Return, CAGR, Calmar
              ├── Sharpe, Sortino
              ├── Max Drawdown, Win Rate
              ├── Profit Factor, Expectancy
              ├── Equity Curve (list of {date, value})
              ├── Drawdown Curve (list of {date, value})
              └── Trade Records (entry/exit/pnl per trade)
```

### Options Engine — Black-Scholes Pricing

```
OptionsEngine.run(df, strategy_spec)
        │
        ├── Resolve strike price from spec
        │     ATM → round(close / interval) × interval
        │     OTM+1 → ATM + 1 × interval
        │     ITM-1 → ATM - 1 × interval
        │
        ├── _estimate_option_price() using Black-Scholes
        │     sigma = annualized realized vol (from close pct_change)
        │     r = 6.5% (RBI rate)
        │     t = 7 days / 365 (weekly expiry)
        │     CE price = S·N(d1) - K·e^{-rt}·N(d2)
        │
        ├── Bar-by-bar simulation loop
        │     Entry signal → record entry premium
        │     Each bar → mark-to-market P&L
        │     Stop loss / Take profit → close position
        │
        └── Return same metrics dict as equity engine
```

### Supported Indicators (40+)

| Category   | Indicators                                              |
|------------|---------------------------------------------------------|
| Trend      | SMA, EMA, WMA, DEMA, TEMA, TRIMA, KAMA, SAR            |
| Momentum   | RSI, MACD, CCI, ADX, Stochastic, Williams %R, MFI, MOM, ROC |
| Volatility | Bollinger Bands, ATR, NATR                              |
| Volume     | OBV, AD, ADOSC, VWAP                                   |
| Price      | CLOSE, OPEN, HIGH, LOW, VOLUME, TYPPRICE, AVGPRICE     |
| Stats      | STDDEV, LINEARREG, TSF, MIDPOINT                       |
| Options    | DELTA, GAMMA, THETA, VEGA, IV                          |
| Patterns   | CDLDOJI, CDLHAMMER, CDLENGULFING, + more               |

---

## 11. RAG — Knowledge Base

```
INDEXING (one-time setup)
        │
scripts/index_strategies.py
        │
        ├── Load strategy JSON files
        ├── chunker.py → split into text chunks
        │     e.g. "RSI mean reversion: buy when RSI < 30..."
        ├── embedder.py → POST to Ollama /api/embed
        │     model: mxbai-embed-large → 1024-dim vectors
        └── qdrant_client.py → upsert to Qdrant collection
              collection: "strategies"

RETRIEVAL (at query time)
        │
User query → embed_texts_async() → 1024-dim vector
        │
        └── Qdrant.search(vector, top_k=3)
              └── Returns most similar strategy descriptions
                    → Injected as context into LLM prompt
```

---

## 12. MCP — Tool Protocol

The Model Context Protocol (MCP) exposes backend capabilities as callable tools that the LLM can invoke:

```
┌────────────────────────────────────────────────────────────┐
│                    MCP TOOL REGISTRY                       │
├──────────────────────┬─────────────────────────────────────┤
│ run_backtest         │ Execute equity/options backtest      │
│ fetch_market_data    │ Get live quote / OHLCV              │
│ analyse_greeks       │ Calculate options greeks (D/G/T/V)  │
│ query_strategy       │ Search strategy knowledge base      │
└──────────────────────┴─────────────────────────────────────┘

LLM sees tools as JSON schemas → decides which to call
MCPServer.execute_tool() → validates input → runs function → returns result
```

---

## 13. Frontend UI

### Component Tree

```
App.tsx
├── Sidebar.tsx              (navigation)
├── TopHeader.tsx            (top bar)
│
├── BacktestDashboard.tsx    (main backtest view)
│   ├── StrategyMetricsKPI.tsx       (6 KPI cards)
│   ├── [Equity / Drawdown Chart]    (Recharts AreaChart)
│   ├── MonthlyReturnsHeatmap.tsx    (calendar grid)
│   ├── RollingMetricsChart.tsx      (rolling Sharpe/DD)
│   ├── MonteCarloSimulation.tsx     (1000 path simulation)
│   ├── TradeDistribution.tsx        (win/loss histogram)
│   ├── ParameterOptimizer.tsx       (param sweep grid)
│   └── BacktestComparison.tsx       (multi-strategy)
│
├── StrategyBuilder.tsx      (visual condition builder)
│   ├── Condition rows (indicator + operator + value/indicator)
│   ├── Entry AND/OR logic
│   ├── Exit AND/OR logic
│   └── Symbol search (1800+ NSE stocks)
│
├── PredefinedStrategies.tsx (strategy gallery)
│   └── Load strategy → populates StrategyBuilder
│
├── ChatPanel.tsx / ChatDrawer.tsx  (AI chat)
│
└── BacktestPanel.tsx        (simplified quick-run panel)
```

### State Management (Zustand)

```
backtestStore
├── latestBacktest: BacktestResult | null
├── indicators: Record<string, Indicator>
├── loading: boolean
├── error: string | null
├── runBacktest(symbol, strategySpec, period)
├── fetchLatestBacktest()
└── fetchIndicators()

chatStore
└── messages, sendMessage(), sessionId

marketStore
└── quotes, fetchQuote(), companies
```

---

## 14. Strategy Library

Seven pre-built strategies seeded to the database:

| Strategy             | Category        | Instrument | Logic                               |
|----------------------|-----------------|------------|-------------------------------------|
| SMA Crossover        | Trend Following | Equity     | SMA 20 crosses above SMA 50         |
| RSI Mean Reversion   | Mean Reversion  | Equity     | Buy RSI < 30, Sell RSI > 70         |
| Bollinger Breakout   | Volatility      | Equity     | Close crosses above Upper BB        |
| MACD Momentum        | Momentum        | Equity     | MACD crosses above Signal line      |
| Momentum Equity      | Momentum        | Equity     | Close > SMA 50 AND RSI > 50         |
| Short Strangle       | Options Selling | Option     | Sell OTM+1 CE + PE, BankNifty weekly|
| ATM Straddle         | Options Buying  | Option     | Buy ATM CE + PE for event play      |

---

## 15. Running the Platform

### Start Services

```bash
# 1. Start infrastructure (Docker)
docker-compose up -d postgres redis qdrant

# 2. Start Ollama + pull models
ollama pull deepseek-r1:8b
ollama pull mxbai-embed-large

# 3. Ingest historical data
cd backend
python scripts/ingest_historical.py

# 4. Seed strategies to DB
python seed_strategies.py

# 5. Index strategies into Qdrant
python scripts/index_strategies.py

# 6. Start backend API
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 7. Start frontend
cd ../frontend
npm run dev
```

### URLs

| Service      | URL                          |
|--------------|------------------------------|
| Frontend UI  | http://localhost:5075        |
| Backend API  | http://localhost:8001        |
| API Docs     | http://localhost:8001/docs   |
| Qdrant UI    | http://localhost:6333/dashboard |

---

## 16. Key Results & Metrics

### Verified Live Test Results (NIFTY, RSI < 30 / > 70, 1Y)

| Metric             | Value          |
|--------------------|----------------|
| Data rows loaded   | 245 (daily)    |
| Trades executed    | 4              |
| Engine response    | < 2 seconds    |
| Equity curve points| 245            |
| Cache hit          | < 10ms (Redis) |
| Backtest (no cache)| ~1.5–3 seconds |

### Platform Capabilities

| Feature                        | Status  |
|--------------------------------|---------|
| Equity backtesting (40+ inds)  | ✅ Done |
| Options backtesting (BS model) | ✅ Done |
| Natural language → strategy    | ✅ Done |
| AI Chat with LangGraph agent   | ✅ Done |
| RAG strategy knowledge base    | ✅ Done |
| MCP tool protocol              | ✅ Done |
| Multi-condition AND/OR logic   | ✅ Done |
| Indicator vs indicator compare | ✅ Done |
| Equity curve visualization     | ✅ Done |
| Drawdown chart                 | ✅ Done |
| Monthly returns heatmap        | ✅ Done |
| Monte Carlo simulation         | ✅ Done |
| Parameter optimization grid    | ✅ Done |
| Multi-strategy comparison      | ✅ Done |
| Redis result caching           | ✅ Done |
| 1800+ NSE stock search         | ✅ Done |
| DB-first data architecture     | ✅ Done |

---

## 17. Challenges & Solutions

| Challenge                                          | Solution                                                       |
|----------------------------------------------------|----------------------------------------------------------------|
| YFinance rate limits & slow downloads              | DB-first read + Parquet cache layer (12hr TTL)                |
| LLM hallucinating wrong indicator names            | Regex NL parser as fast path before LLM call                 |
| VectorBT NaN/Inf in sparse signal data             | `ffill().fillna(0.0)` on all indicator series before compare  |
| NSE symbol format mismatch (NIFTY vs ^NSEI)        | SYMBOL_MAP in YFinanceProvider + `.NS` auto-suffix            |
| Options pricing without live data                  | Black-Scholes model with realized volatility from OHLCV       |
| Redis unavailable in dev                           | In-memory dict fallback in BacktestCache                      |
| Trade log field names mismatch (UI vs backend)     | Backend standardized to snake_case (entry_date, pnl_pct)     |
| LangGraph async in FastAPI event loop              | nest-asyncio + asyncio.to_thread() for blocking calls         |
| Qdrant cold start (collection not initialized)     | init_collection() called in FastAPI lifespan startup          |

---

*This document covers the complete architecture, implementation steps, data pipeline, AI integration, and all technical decisions made during the development of the Quant AI Agent Platform.*

*Backend running on:* `http://localhost:8001` | *Frontend running on:* `http://localhost:5075`
