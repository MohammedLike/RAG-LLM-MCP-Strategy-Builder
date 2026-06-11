# Quant AI Agent

Institutional-grade AI agent for Indian derivatives markets (Nifty / BankNifty). Fine-tuned LLM reasoning, MCP tool orchestration, RAG-augmented strategy retrieval, live market data, and backtesting — all in one system.

## Architecture

```
Layer 1 │ React Web App      — Chat + Market Dashboard + Strategy Explorer + Backtest Panel
Layer 2 │ MCP Server          — fetch_market, query_strategy, run_backtest, analyse_greeks
Layer 3 │ LLM Agent           — Fine-tuned Mistral 7B + RAG (Qdrant) + LangGraph orchestration
Layer 4 │ Training Pipeline   — QLoRA fine-tuning + BGE-M3 embeddings
Layer 5 │ Data Infrastructure — PostgreSQL/TimescaleDB + Redis + Qdrant + Docker Compose
```

## Quick Start

### Prerequisites
- Docker Desktop (Windows/Mac/Linux)
- Python 3.11+
- Node.js 20+
- Ollama (optional — can run in Docker)

### 1. Clone and configure
```bash
git clone <this-repo>
cd "LLM Model"
cp .env.example .env
# Edit .env with your settings
```

### 2. Start infrastructure
```bash
docker compose up -d postgres redis qdrant ollama
```

### 3. Pull the base model
```bash
ollama pull deepseek-r1:14b
```

### 4. Start the backend
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 5. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 6. Open the app
Navigate to `http://localhost:5173`

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, Zustand, TailwindCSS v4, Recharts |
| Backend | FastAPI, Python 3.11 |
| Agent | LangGraph + LangChain |
| LLM | Mistral 7B (fine-tuned via QLoRA) |
| Model serving | Ollama (dev), vLLM (prod) |
| Vector store | Qdrant |
| Embeddings | BGE-M3 (1024 dim) |
| Time-series DB | PostgreSQL + TimescaleDB |
| Cache | Redis 7 |
| Backtesting | VectorBT |
| Market data | yfinance, NSE API |
| Infrastructure | Docker Compose |

## Project Structure

```
├── backend/          # FastAPI + MCP server + LLM agent
│   ├── app/
│   │   ├── api/      # REST + WebSocket endpoints
│   │   ├── mcp/      # MCP tool definitions
│   │   ├── agent/    # LangGraph agent
│   │   ├── rag/      # RAG retrieval layer
│   │   ├── market/   # Market data providers
│   │   ├── backtest/ # VectorBT wrapper
│   │   └── db/       # Database models
│   └── scripts/      # Utility scripts
├── frontend/         # React web app
├── training/         # Fine-tuning pipeline
│   ├── notebooks/    # Colab notebooks
│   ├── data/         # Strategy JSONs + QA pairs
│   └── configs/      # Training configs
├── infra/            # Infrastructure configs
└── docker-compose.yml
```

## License

Private — not for redistribution.
