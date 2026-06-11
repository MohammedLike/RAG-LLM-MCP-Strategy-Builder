# Quant AI Agent — Build Progress

## Phase 1: Infrastructure Foundation
- [/] `.gitignore`
- [/] `.env.example` + `.env`
- [/] `docker-compose.yml`
- [/] `infra/postgres/init.sql`
- [/] `infra/redis/redis.conf`
- [/] `infra/qdrant/config.yaml`
- [ ] `infra/nginx/nginx.conf`
- [/] `README.md`

## Phase 2: Data Layer + Backend Foundation
- [ ] `backend/pyproject.toml`
- [ ] `backend/Dockerfile`
- [ ] `backend/app/__init__.py`
- [ ] `backend/app/config.py`
- [ ] `backend/app/db/models.py`
- [ ] `backend/app/db/session.py`
- [ ] `backend/app/market/provider_base.py`
- [ ] `backend/app/market/provider_yfinance.py`
- [ ] `backend/app/market/provider_nse.py`
- [ ] `backend/app/market/cache.py`
- [ ] `backend/app/market/greeks.py`
- [ ] `backend/scripts/ingest_historical.py`

## Phase 3: Strategy Knowledge Base + RAG
- [ ] `training/data/strategies/_schema.json`
- [ ] `training/data/strategies/short_strangle.json`
- [ ] `training/data/strategies/iron_condor.json`
- [ ] `training/data/strategies/bull_put_spread.json`
- [ ] `training/data/strategies/straddle_earnings.json`
- [ ] `training/scripts/generate_qa_pairs.py`
- [ ] `backend/app/rag/chunker.py`
- [ ] `backend/app/rag/embedder.py`
- [ ] `backend/app/rag/qdrant_client.py`
- [ ] `backend/app/rag/indexer.py`
- [ ] `backend/scripts/index_strategies.py`

## Phase 4: MCP Server + Agent
- [ ] `backend/app/mcp/server.py`
- [ ] `backend/app/mcp/tool_fetch_market.py`
- [ ] `backend/app/mcp/tool_query_strategy.py`
- [ ] `backend/app/mcp/tool_run_backtest.py`
- [ ] `backend/app/mcp/tool_analyse_greeks.py`
- [ ] `backend/app/backtest/engine.py`
- [ ] `backend/app/backtest/metrics.py`
- [ ] `backend/app/agent/state.py`
- [ ] `backend/app/agent/prompts.py`
- [ ] `backend/app/agent/nodes.py`
- [ ] `backend/app/agent/graph.py`
- [ ] `backend/app/agent/memory.py`
- [ ] `backend/app/main.py`
- [ ] `backend/app/api/routes_chat.py`
- [ ] `backend/app/api/routes_market.py`
- [ ] `backend/app/api/routes_strategy.py`
- [ ] `backend/app/api/routes_backtest.py`

## Phase 5: React Frontend
- [ ] Initialize Vite + React + TypeScript
- [ ] `frontend/src/index.css`
- [ ] `frontend/src/App.tsx`
- [ ] Zustand stores (chat, market, strategy, backtest)
- [ ] Chat components (panel, bubble, input, streaming)
- [ ] Market components (dashboard, price card, options table)
- [ ] Strategy components (explorer, card, detail)
- [ ] Backtest components (panel, equity curve, KPI grid)
- [ ] Hooks (useWebSocket, useChat, useMarketData)
- [ ] API services

## Phase 6: Training Pipeline
- [ ] `training/configs/qlora_config.yaml`
- [ ] `training/configs/embedding_config.yaml`
- [ ] `training/notebooks/01_prepare_dataset.ipynb`
- [ ] `training/notebooks/02_finetune_qlora.ipynb`
- [ ] `training/notebooks/03_merge_export.ipynb`
- [ ] `training/notebooks/04_embed_index.ipynb`
