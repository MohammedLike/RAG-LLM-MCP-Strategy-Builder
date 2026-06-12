# STRYKE X
### Institutional AI Quant & Backtesting Engine
> *Powered by the FinStocks.ai Unified Design System*

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![VectorBT](https://img.shields.io/badge/VectorBT-0.26+-FF6B35?style=flat-square)](https://vectorbt.dev)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.x-FDB515?style=flat-square&logo=postgresql)](https://timescale.com)
[![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?style=flat-square&logo=redis)](https://redis.io)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.9+-FF4B4B?style=flat-square)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)]()

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [System Architecture](#2-system-architecture)
   - 2.1 [Macro Architecture — Layer Decomposition](#21-macro-architecture--layer-decomposition)
   - 2.2 [Full System Data Flow](#22-full-system-data-flow)
   - 2.3 [Request Lifecycle — Backtest Execution Path](#23-request-lifecycle--backtest-execution-path)
   - 2.4 [LLM Cognitive Layer — MCP & RAG Pipeline](#24-llm-cognitive-layer--mcp--rag-pipeline)
3. [Technology Stack — Justified Selections](#3-technology-stack--justified-selections)
4. [Database Architecture & Schema Design](#4-database-architecture--schema-design)
   - 4.1 [TimescaleDB Hypertable Design](#41-timescaledb-hypertable-design)
   - 4.2 [Indexing Strategy & Query Planner Behaviour](#42-indexing-strategy--query-planner-behaviour)
   - 4.3 [Compression & Retention Policies](#43-compression--retention-policies)
5. [Dynamic Strategy Compilation Engine](#5-dynamic-strategy-compilation-engine)
   - 5.1 [Parsing Pipeline — AST Construction](#51-parsing-pipeline--ast-construction)
   - 5.2 [Operator Dispatch Table](#52-operator-dispatch-table)
   - 5.3 [Compiler State Machine](#53-compiler-state-machine)
6. [VectorBT Execution Engine](#6-vectorbt-execution-engine)
   - 6.1 [Signal Matrix Architecture](#61-signal-matrix-architecture)
   - 6.2 [Portfolio Simulation Parameters](#62-portfolio-simulation-parameters)
   - 6.3 [Performance Metrics Taxonomy](#63-performance-metrics-taxonomy)
7. [Caching Architecture](#7-caching-architecture)
8. [API Reference](#8-api-reference)
9. [Deployment & Infrastructure](#9-deployment--infrastructure)
   - 9.1 [Docker Compose Topology](#91-docker-compose-topology)
   - 9.2 [Service Dependency Graph](#92-service-dependency-graph)
10. [Quantitative Research Methodology](#10-quantitative-research-methodology)
    - 10.1 [Backtesting Integrity Framework](#101-backtesting-integrity-framework)
    - 10.2 [Statistical Validation Pipeline](#102-statistical-validation-pipeline)
11. [Performance Benchmarks & Complexity Analysis](#11-performance-benchmarks--complexity-analysis)
12. [Development Roadmap](#12-development-roadmap)
13. [Contributing & Standards](#13-contributing--standards)

---

## 1. Executive Overview

**Stryke X** is an institutional-grade, AI-agentic quantitative research and backtesting platform purpose-built for **Indian derivatives markets** — Nifty 50, Bank Nifty, FinNifty, MidcapNifty (NSE F&O). It is not a retail strategy builder; it is an infrastructure-layer research operating system.

The platform architecture integrates five horizontally decoupled subsystems:

| Subsystem | Role |
|---|---|
| **Cognitive Reasoning Layer** | DeepSeek-R1 / Mistral via Ollama/vLLM + RAG via Qdrant for strategy hypothesis synthesis |
| **Compilation Engine** | Natural-language condition  AST  vectorized boolean signal matrix |
| **Backtesting Engine** | VectorBT-powered NumPy/Pandas vectorized simulation with institutional-grade metrics |
| **Data Infrastructure** | TimescaleDB hypertables for tick/OHLCV/options chain; Redis for sub-millisecond state |
| **Presentation Layer** | High-DPI HTML5 Canvas charting, equity curve analytics, monthly return heatmaps |

**Design Philosophy:** Every architectural decision prioritises *reproducibility*, *statistical integrity*, and *computational efficiency* over feature breadth. No lookahead bias. No survivorship bias. Deterministic replays.

---

## 2. System Architecture

### 2.1 Macro Architecture — Layer Decomposition

```
                       STRYKE X — SYSTEM LAYERS                              

                    L5 — PRESENTATION LAYER                               
     index.html  Vanilla JS  High-DPI Canvas  Heatmap  Monaco IDE    
    
                                   REST / WebSocket (JSON)                  
    
                    L4 — API GATEWAY & ORCHESTRATION                      
         FastAPI (Python 3.12)  Async I/O  Pydantic Validation          
         MCP Server Router  DB Session Manager  Auth Middleware         
     
                  LLM Prompts                       Backtest Requests       
      
    L3a — COGNITIVE LAYER           L3b — ANALYTICS ENGINE              
    Ollama  DeepSeek-R1             VectorBT  TA-Lib  NumPy           
    vLLM (prod)  BGE-M3             Dynamic Rule Compiler               
    Qdrant (RAG)                     IndicatorManager                    
      
                                                                            
      
    L2 — CACHE LAYER                L2 — CACHE LAYER                    
    Redis 7 (KV State)              Parquet LocalCache                   
    TTL-based invalidation          yfinance fallback provider           
      
                                                                            
   
                      L1 — STORAGE LAYER                                   
     TimescaleDB (PostgreSQL 16)  ohlcv hypertable  ticks hypertable    
     options_chain hypertable    strategies relational table              
```

### 2.2 Full System Data Flow

```mermaid
flowchart TB
    subgraph Client [" Presentation Layer — FinStocks.ai UI"]
        direction TB
        UI[/"index.html  Vanilla JS Client"/]
        Canvas["High-DPI HTML5 Canvas\nEquity Curve  Drawdown Plot"]
        Heatmap["Monthly Return\nAnalytics Heatmap"]
        Editor["Monaco-like\nStrategy DSL Editor"]
        UI --> Canvas
        UI --> Heatmap
        UI --> Editor
    end

    subgraph Gateway [" API Gateway & Orchestration (Port 8001)"]
        direction TB
        FastAPI["FastAPI Async Gateway\nPydantic  OpenAPI 3.1"]
        Auth["JWT Auth Middleware"]
        MCPRouter["MCP Server Router\nTool Dispatch Table"]
        SessionMgr["DB Session Manager\nAsyncPG Connection Pool"]
        FastAPI --> Auth
        FastAPI --> MCPRouter
        FastAPI --> SessionMgr
    end

    subgraph LLM [" Cognitive Reasoning Layer"]
        direction TB
        Ollama["Ollama Server (Dev)\nPort 11434  DeepSeek-R1"]
        vLLM["vLLM (Production)\nTensorRT-optimized"]
        Qdrant["Qdrant Vector Store\nBGE-M3 1024-dim Embeddings"]
        StrategyRAG["Strategy RAG\nRetriever  Re-ranker"]
        Ollama -->|"Semantic Query"| Qdrant
        vLLM -->|"Semantic Query"| Qdrant
        Qdrant --> StrategyRAG
    end

    subgraph Analytics [" Backtesting & Analytics Engine"]
        direction TB
        VBT["VectorBT Engine\nvbt.Portfolio.from_signals()"]
        Compiler["Dynamic Rule Compiler\nAST Parser  Regex Splitter"]
        IndicatorMgr["Indicator Manager\nTA-Lib  NumPy  Pandas"]
        MetricsCalc["Metrics Calculator\nSharpe  Sortino  CAGR  MDD"]
        VBT --> Compiler
        Compiler --> IndicatorMgr
        VBT --> MetricsCalc
    end

    subgraph Cache [" Caching Layer"]
        Redis["Redis 7\nSub-ms KV Store\nTTL Invalidation"]
        ParquetCache["Parquet Local Cache\n~/.stryke/cache/"]
    end

    subgraph DataProviders [" External Data Providers"]
        YFinance["yfinance\nFallback OHLCV Provider"]
        NSEData["NSE / BSE Live\nOptions Chain  OI Data"]
    end

    subgraph Storage [" Storage Layer — TimescaleDB (Port 5432)"]
        direction LR
        PG[(TimescaleDB\nPostgreSQL 16)]
        OHLCV_T[("ohlcv\nHypertable\n30-day chunks")]
        Ticks_T[("ticks\nHypertable\n1-day chunks")]
        Options_T[("options_chain\nHypertable\nIV  OI  Greeks")]
        Strategies_T[("strategies\nRelational\nJSONB Rules")]
        PG --- OHLCV_T
        PG --- Ticks_T
        PG --- Options_T
        PG --- Strategies_T
    end

    %% Connections
    UI -->|"HTTP POST /api/backtest\nWS /ws/stream"| FastAPI
    FastAPI -->|"Strategy NL Prompt"| MCPRouter
    MCPRouter -->|"Context-Augmented Prompt"| Ollama
    MCPRouter -->|"Context-Augmented Prompt"| vLLM
    StrategyRAG -->|"Retrieved Strategy Contexts"| MCPRouter
    FastAPI -->|"BacktestRequest Pydantic Model"| VBT
    VBT -->|"Cache Check"| Redis
    Redis -->|"Cache Miss  DB Query"| SessionMgr
    SessionMgr -->|"SELECT ohlcv WHERE symbol, res, time"| PG
    VBT -->|"Cache Miss  Parquet"| ParquetCache
    ParquetCache -->|"Still Miss  External"| YFinance
    NSEData -->|"Streaming OI  IV"| Options_T
    MetricsCalc -->|"JSON Metrics Payload"| FastAPI
    FastAPI -->|"Equity Curve  Trades  Metrics"| UI
    UI -->|"Render Curves"| Canvas
    UI -->|"Populate Cells"| Heatmap
```

### 2.3 Request Lifecycle — Backtest Execution Path

```
Client                   FastAPI                 BacktestEngine              TimescaleDB / Redis
                                                                                  
    POST /api/backtest                                                             
    {strategy_spec,                                                                
     symbol, period}                                                               
                                                         
                              Pydantic Validation                                  
                              BacktestRequest model                                
                                                         
                                                        cache_key = hash(spec)     
                                                      
                                                                                   
                                                       HIT: JSON payload 
                                                            (< 1ms Redis read)     
                                                                                   
                                                        (MISS path):               
                                                      
                                                        SELECT ohlcv WHERE         
                                                        symbol=$1 AND res=$2       
                                                        ORDER BY time ASC          
                                                       DataFrame 
                                                                                   
                                                        compile_conditions()       
                                                           
                                                         AST Parse  Nodes       
                                                         IndicatorManager        
                                                         Boolean Signal Matrix   
                                                           
                                                                                   
                                                        vbt.Portfolio.from_signals 
                                                           
                                                         Vectorized Sim          
                                                         SL/TP/Fees/Slippage     
                                                         Metrics Extraction      
                                                           
                                                                                   
                                                        Redis SET cache_key 3600s  
                                                      
                             BacktestResponse                              
                                                         
    {sharpe, sortino,                                                              
     equity_curve, trades}                                                         
```

### 2.4 LLM Cognitive Layer — MCP & RAG Pipeline

```
User NL Strategy Input
        
              MCP Orchestration Router                 
                                                       
  Tool Dispatch Table:                                 
       
    Tool Name           Handler                    
        
    get_ohlcv           YFinanceProvider            
    run_backtest        BacktestEngine              
    query_strategy      StrategyRepository          
    compute_indicator   IndicatorManager            
    search_similar      QdrantRetriever             
       
            Qdrant Vector Store     
          Hybrid Search:            
           Dense (BGE-M3 1024-dim) 
           Sparse (BM25 tokens)    
          Top-K=5 strategy contexts 
        
                       Retrieved Contexts
        
           Context Augmentation     
          [System Prompt]           
          + [Top-K Strategies]      
          + [User Query]            
          + [Market Schema]         
        
                       Augmented Prompt
        
           DeepSeek-R1 (Reasoning)  
           Chain-of-Thought tokens  
           Structured JSON Output   
            strategy_spec JSONB    
        
                       Parsed strategy_spec
        
           Compiler Validation      
           Schema check  DB write  
           strategies table insert  
```

---

## 3. Technology Stack — Justified Selections

| Layer | Component | Version | Justification |
|---|---|---|---|
| **Language** | Python | 3.12+ | `asyncio` improvements, `typing` generics, faster CPython internals |
| **API Framework** | FastAPI | 0.115+ | Native async, Pydantic v2, auto OpenAPI 3.1 schema, ~50k RPS on `uvicorn` |
| **Vectorized Backtest** | VectorBT | 0.26+ | NumPy-native boolean signal matrices; orders-of-magnitude faster than event-driven Backtrader |
| **Technical Indicators** | TA-Lib | 0.4.x | C-wrapped FFTW3; ~100x faster than pure-Python pandas-ta for bulk indicator computation |
| **Time-Series DB** | TimescaleDB | 2.x | Hypertable chunk pruning; 40-90% storage compression; native time-bucket aggregations outperform vanilla PostgreSQL for OHLCV queries |
| **Cache** | Redis 7 | 7.x | Sub-millisecond serialized JSON payloads; Lua scripting for atomic metric updates; native sorted sets for leaderboard analytics |
| **Vector Store** | Qdrant | 1.9+ | HNSW index; hybrid dense+sparse retrieval; payload filtering; Rust core for zero-copy deserialization |
| **Embeddings** | BGE-M3 | 1024-dim | Multi-lingual, multi-granularity; outperforms OpenAI `text-embedding-3-small` on MTEB financial retrieval benchmarks |
| **LLM (Dev)** | Ollama + DeepSeek-R1 | R1-7B | On-prem; zero API cost; chain-of-thought reasoning tokens improve strategy hypothesis quality |
| **LLM (Prod)** | vLLM | 0.5+ | Continuous batching; PagedAttention KV cache; 24x throughput over naive Transformers inference |
| **Containerization** | Docker Compose | v2 | Service isolation; reproducible builds; volume mounts for persistent data |

---

## 4. Database Architecture & Schema Design

### 4.1 TimescaleDB Hypertable Design

```sql
-- 
--  SCHEMA: stryke_x
--  PURPOSE: Institutional time-series storage for Indian markets
--  STORAGE ENGINE: TimescaleDB 2.x on PostgreSQL 16
-- 

-- 
-- TABLE 1: ohlcv — OHLCV Price Bars (Hypertable)
-- Chunk interval: 30 days | Compression: columnar after 7 days
-- 
CREATE TABLE IF NOT EXISTS ohlcv (
    time        TIMESTAMPTZ      NOT NULL,
    symbol      TEXT             NOT NULL,  -- 'NIFTY', 'BANKNIFTY', 'RELIANCE'
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      BIGINT,
    resolution  TEXT             NOT NULL   -- '1m','5m','15m','1h','1d','1w'
);

SELECT create_hypertable(
    'ohlcv', 'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists       => TRUE
);

-- Composite index for the canonical query pattern:
-- WHERE symbol = $1 AND resolution = $2 AND time BETWEEN $3 AND $4
CREATE INDEX IF NOT EXISTS ix_ohlcv_symbol_res_time
    ON ohlcv (symbol, resolution, time DESC);

-- Columnar compression: reduce storage 60-90% for cold data
ALTER TABLE ohlcv SET (
    timescaledb.compress,
    timescaledb.compress_segmentby  = 'symbol, resolution',
    timescaledb.compress_orderby    = 'time DESC'
);

SELECT add_compression_policy('ohlcv', INTERVAL '7 days');
SELECT add_retention_policy('ohlcv', INTERVAL '10 years');

-- 
-- TABLE 2: ticks — Level-1 Tick Data (Hypertable)
-- Chunk interval: 1 day | High-frequency write path
-- 
CREATE TABLE IF NOT EXISTS ticks (
    time        TIMESTAMPTZ      NOT NULL,
    symbol      TEXT             NOT NULL,
    ltp         DOUBLE PRECISION NOT NULL,  -- Last Traded Price
    bid         DOUBLE PRECISION,
    ask         DOUBLE PRECISION,
    bid_qty     BIGINT,
    ask_qty     BIGINT,
    volume      BIGINT,
    oi          BIGINT,                     -- Open Interest (F&O ticks)
    exchange    TEXT             NOT NULL   -- 'NSE', 'BSE'
);

SELECT create_hypertable(
    'ticks', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists       => TRUE
);

CREATE INDEX IF NOT EXISTS ix_ticks_symbol_time
    ON ticks (symbol, time DESC);

-- 
-- TABLE 3: options_chain — Options Chain Snapshots (Hypertable)
-- Stores IV surface, OI distribution, and pre-computed Greeks
-- 
CREATE TABLE IF NOT EXISTS options_chain (
    time        TIMESTAMPTZ      NOT NULL,
    symbol      TEXT             NOT NULL,  -- Underlying: 'NIFTY', 'BANKNIFTY'
    expiry      DATE             NOT NULL,
    strike      DOUBLE PRECISION NOT NULL,
    option_type TEXT             NOT NULL   CHECK (option_type IN ('CE', 'PE')),
    oi          BIGINT,                     -- Open Interest (lots)
    oi_change   BIGINT,                     -- ΔOI from previous session
    volume      BIGINT,
    iv          DOUBLE PRECISION,           -- Implied Volatility (annualised %)
    ltp         DOUBLE PRECISION,           -- Last Traded Price
    bid         DOUBLE PRECISION,
    ask         DOUBLE PRECISION,
    greeks_json JSONB                       -- {delta, gamma, theta, vega, rho}
);

SELECT create_hypertable(
    'options_chain', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists       => TRUE
);

CREATE INDEX IF NOT EXISTS ix_options_chain_query
    ON options_chain (symbol, expiry, strike, option_type, time DESC);

-- GIN index for JSONB Greeks querying
CREATE INDEX IF NOT EXISTS ix_options_greeks_gin
    ON options_chain USING GIN (greeks_json);

-- 
-- TABLE 4: strategies — Strategy Registry (Relational)
-- Stores compiled rule ASTs, risk params, and backtest cache
-- 
CREATE TABLE IF NOT EXISTS strategies (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name         TEXT         NOT NULL,
    slug         TEXT         UNIQUE NOT NULL,
    category     TEXT         NOT NULL,   -- 'equity','futures','options','delta_neutral'
    hypothesis   TEXT,                    -- NL research hypothesis
    entry_rules  JSONB,                   -- Compiled condition ASTs
    exit_rules   JSONB,
    risk_params  JSONB,                   -- {sl_pct, tp_pct, trail_pct, max_pos_size}
    metadata     JSONB,                   -- Tags, author, version, performance summary
    created_at   TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_strategies_category ON strategies (category);
CREATE INDEX IF NOT EXISTS ix_strategies_metadata_gin ON strategies USING GIN (metadata);

-- 
-- TABLE 5: backtest_runs — Immutable Backtest Audit Log
-- Every simulation persisted for reproducibility & comparison
-- 
CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id  UUID         REFERENCES strategies(id) ON DELETE SET NULL,
    symbol       TEXT         NOT NULL,
    resolution   TEXT         NOT NULL,
    period_start DATE         NOT NULL,
    period_end   DATE         NOT NULL,
    sharpe       DOUBLE PRECISION,
    sortino      DOUBLE PRECISION,
    cagr         DOUBLE PRECISION,
    max_dd       DOUBLE PRECISION,
    win_rate     DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    total_trades INTEGER,
    params_hash  TEXT         NOT NULL,  -- SHA-256 of strategy_spec JSON
    equity_curve JSONB,                  -- [{date, value}] array
    run_at       TIMESTAMPTZ  DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_backtest_runs_strategy_id ON backtest_runs (strategy_id);
CREATE INDEX IF NOT EXISTS ix_backtest_runs_params_hash  ON backtest_runs (params_hash);
```

### 4.2 Indexing Strategy & Query Planner Behaviour

```
Query Pattern Analysis — ohlcv Table

Canonical Query:
  SELECT time, open, high, low, close, volume
  FROM ohlcv
  WHERE symbol = 'NIFTY'
    AND resolution = '1d'
    AND time BETWEEN '2020-01-01' AND '2025-01-01'
  ORDER BY time ASC;

Index: ix_ohlcv_symbol_res_time (symbol, resolution, time DESC)
                                                            
                            Equality               
                            Scan (fast)                        
                            Equality      
                            Scan (fast)
                            Range Scan     Chunk Pruning
                                          TimescaleDB only scans
                                          chunks overlapping time range

Estimated chunks scanned (5yr @ 30d/chunk): 61 chunks / 1826 total
Chunk prune ratio: ~97% of data excluded before page read
```

### 4.3 Compression & Retention Policies

```
TimescaleDB Compression Pipeline

Chunk Age      State              Storage Format          Access Latency

0  – 7 days    UNCOMPRESSED       Row-oriented (heap)     < 1ms
7  – 90 days   COMPRESSED         Columnar (native)       < 5ms
90 – 1 year    COMPRESSED         Columnar + dict enc     < 10ms
1+ years       TIERED (future)    S3 / object storage     100ms+

Compression Ratio (empirical, OHLCV daily data):
  Uncompressed: ~8 bytes  6 cols  5000 rows/chunk  240 KB/chunk
  Compressed:   ~15–25 KB/chunk (91% reduction)
```

---

## 5. Dynamic Strategy Compilation Engine

The **Dynamic Rule Compiler** (`backend/app/strategies/compiler.py`) is the intellectual core of Stryke X. It bridges natural-language strategy conditions and NumPy vectorized boolean arrays.

### 5.1 Parsing Pipeline — AST Construction

```
Input Condition String:
  "RSI(close, 14, 0) < 30 AND SMA(close, 5, 0) crosses_above SMA(close, 20, 0)"

STAGE 1 — TOKENIZATION

Token Stream:
  [RSI_CALL, LITERAL_30, AND_OP, SMA_CALL_5, CROSSABOVE_OP, SMA_CALL_20]

  Token patterns (regex):
   INDICATOR  : r'([A-Z_]+)\(([^)]+)\)'                      
   OPERATOR   : r'(crosses_above|crosses_below|>|<|>=|<=|==)'
   LITERAL    : r'(\d+\.?\d*)'                               
   LOGICAL    : r'(AND|OR)'                                  

STAGE 2 — AST NODE CONSTRUCTION

  ASTNode {
    node_type : "INDICATOR" | "LITERAL" | "EXPRESSION",
    name      : "RSI" | "SMA" | None,
    params    : { source: "close", period: 14, offset: 0 },
    operator  : "<" | "crosses_above" | "AND",
    left      : ASTNode | None,
    right     : ASTNode | None,
    value     : float | None
  }

  Tree Structure:
                        AND
                       /   \
                      /     \
                 EXPR_1    EXPR_2
                 /    \    /    \
              RSI(14)  30 SMA(5) SMA(20)
             [LHS]  [LT][LHS]  [XABOVE RHS]

STAGE 3 — INDICATOR RESOLUTION

  IndicatorManager.compute(node, df)  pd.Series

  Dispatch table:
   Name        TA-Lib Call                       Return Shape    
   SMA         talib.SMA(src, timeperiod=p)       Series [T]      
   EMA         talib.EMA(src, timeperiod=p)       Series [T]      
   RSI         talib.RSI(src, timeperiod=p)       Series [T]      
   BBANDS      talib.BBANDS(src, timeperiod=p)    3Series [T]    
   MACD        talib.MACD(src, f, s, sig)         3Series [T]    
   ATR         talib.ATR(h, l, c, timeperiod=p)   Series [T]      
   VWAP        custom: cumvolprice / cumvol      Series [T]      
   SUPERTREND  custom: ATR-based                  Series [T]      

STAGE 4 — BOOLEAN SIGNAL MATRIX GENERATION

  Operator  NumPy/Pandas vectorized evaluation:
  ">"            lhs.values > rhs.values
  "<"            lhs.values < rhs.values
  "crosses_above" 
      (lhs.values  > rhs.values) &
      (lhs.shift(1).values <= rhs.shift(1).values)
  "crosses_below" 
      (lhs.values  < rhs.values) &
      (lhs.shift(1).values >= rhs.shift(1).values)

  Logical AND  np.logical_and(signal_1, signal_2)
  Logical OR   np.logical_or(signal_1, signal_2)

  Output: entries np.ndarray[bool, T], exits np.ndarray[bool, T]
  Shape: (T,) where T = number of OHLCV bars in backtest period
```

### 5.2 Operator Dispatch Table

| Operator String | Mathematical Condition | Vectorized Implementation |
|---|---|---|
| `>` | `lhs > rhs` | `lhs.values > rhs_val` |
| `<` | `lhs < rhs` | `lhs.values < rhs_val` |
| `>=` | `lhs  rhs` | `lhs.values >= rhs_val` |
| `<=` | `lhs  rhs` | `lhs.values <= rhs_val` |
| `==` | `lhs = rhs` | `np.isclose(lhs.values, rhs_val)` |
| `crosses_above` | `lhs > rhs  lhs  rhs` | `(lhs > rhs) & (lhs.shift(1) <= rhs.shift(1))` |
| `crosses_below` | `lhs < rhs  lhs  rhs` | `(lhs < rhs) & (lhs.shift(1) >= rhs.shift(1))` |
| `AND` | `P  Q` | `np.logical_and(sig_a, sig_b)` |
| `OR` | `P  Q` | `np.logical_or(sig_a, sig_b)` |

### 5.3 Compiler State Machine

```
                      START   
                          input: condition_string
                      TOKENIZE  regex_split(condition_string)
                          token_stream
               NO  VALID         YES 
                    SYNTAX?             
      RAISE                      BUILD AST NODES 
      CompileError               (recursive)     
                                           ast_tree
                                  RESOLVE          
                                  INDICATORS       
                                  IndicatorManager 
                                           resolved_series_map
                                  EVALUATE         
                                  EXPRESSIONS      
                                  (vectorized ops) 
                                           boolean_array
                                   VALIDATE        
                                   Signal Density    assert min_signals > 0
                                   (sanity check)  
                                     COMPILED 
                                     SPEC     
```

---

## 6. VectorBT Execution Engine

### 6.1 Signal Matrix Architecture

```
OHLCV DataFrame [T  5]          Entry Conditions             Exit Conditions
                       
  time  open high  low  close      [entry_condition_1]           [exit_condition_1]
  t    ...  ...   ...  c                              AND   
  t    ...  ...   ...  c         bool_array_E                bool_array_X
  ...                               [entry_condition_2]           [exit_condition_2]
  t    ...  ...   ...  c                                AND   
                                    bool_array_E                bool_array_X
                                                                      
                                          logical_operator            logical_operator
                                            
                                  entries[T]                exits[T]      
                                  bool ndarray              bool ndarray  
                                            
                                          vbt.Portfolio.from_signals(
                                              close   = df['close'],
                                              entries = entries,     # bool[T]
                                              exits   = exits,       # bool[T]
                                              sl_stop = sl_frac,     # e.g. 0.02
                                              tp_stop = tp_frac,     # e.g. 0.05
                                              fees    = 0.001,       # 0.1% round-trip
                                              slippage= 0.001,
                                              freq    = 'D'
                                          )
```

### 6.2 Portfolio Simulation Parameters

| Parameter | Symbol | Type | Description |
|---|---|---|---|
| `sl_stop` | δ_SL | `float` | Stop-loss as fraction of entry price: `exit if price < entry  (1 - δ_SL)` |
| `tp_stop` | δ_TP | `float` | Take-profit fraction: `exit if price > entry  (1 + δ_TP)` |
| `fees` | f | `float` | One-way commission fraction applied at entry AND exit |
| `slippage` | s | `float` | Symmetric price impact applied as fraction of execution price |
| `freq` | — | `str` | Pandas offset alias for annualisation of Sharpe/Sortino: `'D'` = 252 trading days |
| `init_cash` | C | `float` | Starting capital; default `100.0` (returns normalised) |
| `size` | — | `float` | Position size as fraction of portfolio equity; default `1.0` (full Kelly) |

**Effective round-trip cost model:**
```
Net Return per Trade = (P_exit / P_entry) - 1
                     - 2  fees             (entry + exit commission)
                     - 2  slippage         (bilateral price impact)

At fees=0.001, slippage=0.001:
  Gross edge required to break even:  0.40% per trade
  NSE F&O realistic estimate: 0.03–0.05% (STT + brokerage + impact)
```

### 6.3 Performance Metrics Taxonomy

```
                         STRYKE X PERFORMANCE METRICS

  RETURN METRICS                    RISK METRICS
                      
  Total Return R_total              Max Drawdown MDD
      = (V_T - V_0) / V_0               = max over [0,T] of (V_peak - V_t)/V_peak

  CAGR                              Calmar Ratio
      = (V_T/V_0)^(252/T) - 1          = CAGR / |MDD|

  Benchmark Alpha α                 Volatility σ
      = R_strategy - R_benchmark        = std(daily_returns)  252

  RISK-ADJUSTED METRICS             TRADE STATISTICS
               
  Sharpe Ratio S                    Win Rate W
      = (μ_p - r_f) / σ_p               = N_winners / N_total

  Sortino Ratio S_d                 Profit Factor PF
      = (μ_p - r_f) / σ_downside        = Σ(wins) / |Σ(losses)|

  Information Ratio IR              Expectancy E
      = α / σ(α)                        = W  avg_win - (1-W)  avg_loss

  Omega Ratio Ω                     Avg Hold Period
      = ^ (1-F(r))dr / ^0 F(r)dr    = mean(exit_idx - entry_idx)
```

---

## 7. Caching Architecture

```
CACHE HIERARCHY & DECISION TREE

Request arrives at BacktestEngine
           
  cache_key = SHA-256(
      symbol + resolution + period +
      strategy_spec_json_sorted
  )
           
    Redis GET(cache_key)  
             
           HIT?  
        YES    NO
          Deserialise JSON  BacktestResponse   < 1ms
          Return immediately                 
               (MISS path)
              
   Parquet Cache Check        
   ~/.stryke/cache/{key}.parq 
             
             HIT?  
          YES    NO
     pd.read_parquet      TimescaleDB query           
      DataFrame         SELECT * FROM ohlcv WHERE  
                          (chunk-pruned index scan)   
                                         (STILL MISS)
                           yfinance.download()          
                           Fallback provider            
                           Write-through to OHLCV table 
```

**Redis Cache Policy:**
* `SET cache_key payload EX 3600` — 1-hour TTL for backtest results.
* `SET ohlcv:{sym}:{res} payload EX 86400` — 24-hour TTL for raw OHLCV.
* `ZSET leaderboard:sharpe {run_id: sharpe}` — Sorted set for ranking.

---

## 8. API Reference

### Endpoint: `GET /api/strategies`
Returns the merged strategy registry from TimescaleDB and file-based templates.

**Response Schema:**
```typescript
interface StrategyListResponse {
  strategies: Array<{
    id:          string;           // UUID
    name:        string;           // Human-readable name
    slug:        string;           // URL-safe identifier
    category:    "equity" | "futures" | "options" | "delta_neutral";
    description: string;
    tags:        string[];
    backtest_results: {
      total_return:   number;      // %
      win_rate:       number;      // %
      sharpe:         number;
      max_drawdown:   number;      // %, negative
    } | null;
    backtest_spec:   StrategySpec;
  }>;
  total: number;
}
```

### Endpoint: `POST /api/backtest`
Executes a vectorized historical simulation. Idempotent via SHA-256 cache key.

**Request Schema:**
```typescript
interface BacktestRequest {
  strategy_spec: {
    instrument_type: "EQUITY" | "FUTURES" | "OPTIONS";
    entry: {
      conditions: ConditionNode[];
      logical_operator: "AND" | "OR";
    };
    exit: {
      conditions: ConditionNode[];
      logical_operator: "AND" | "OR";
    };
    stop_loss:   number;           // fraction: 0.02 = 2%
    take_profit: number;           // fraction: 0.05 = 5%
  };
  symbol:      string;             // e.g. "NIFTY", "BANKNIFTY"
  period:      "1y" | "2y" | "5y" | "10y" | "max";
  resolution?: "1d" | "1h" | "15m" | "5m";  // default: "1d"
}

interface ConditionNode {
  indicator: string;               // "RSI", "SMA", "EMA", "ATR", ...
  params:    Record<string, number>;
  operator:  ">" | "<" | ">=" | "<=" | "==" | "crosses_above" | "crosses_below";
  value:     number | ConditionNode;  // scalar or nested indicator
}
```

**Response Schema:**
```typescript
interface BacktestResponse {
  symbol:           string;
  period:           string;
  resolution:       string;
  // Return Metrics
  total_return:     number;        // %
  benchmark_return: number;        // %
  alpha:            number;        // excess return over benchmark
  cagr:             number;        // Compound Annual Growth Rate %
  // Risk-Adjusted Metrics
  sharpe:           number;
  sortino:          number;
  calmar:           number;
  omega:            number;
  // Risk Metrics
  max_drawdown:     number;        // %, negative
  max_dd_duration:  number;        // trading days
  volatility:       number;        // annualised %
  // Trade Statistics
  total_trades:     number;
  win_rate:         number;        // %
  profit_factor:    number;
  avg_trade_return: number;        // %
  avg_hold_bars:    number;
  // Series Data
  equity_curve: Array<{ date: string; value: number }>;
  drawdown_curve: Array<{ date: string; value: number }>;
  monthly_returns: Array<{ year: number; month: number; return: number }>;
  trades: TradeRecord[];
  // Metadata
  params_hash:      string;        // SHA-256 for cache reference
  cached:           boolean;
  computation_ms:   number;
}
```

### Endpoint: `POST /api/strategy/generate`
Uses the LLM + RAG pipeline to synthesise a strategy spec from a natural-language hypothesis.

**Request:**
```json
{
  "hypothesis": "Buy NIFTY when RSI is oversold below 30 and price is above 200 EMA, sell when RSI reaches 70",
  "risk_profile": "conservative",
  "universe": "NIFTY"
}
```
**Response:** Full `BacktestRequest.strategy_spec` JSONB, plus the chain-of-thought reasoning tokens.

---

## 9. Deployment & Infrastructure

### 9.1 Docker Compose Topology

```yaml
services:
  # Storage Layer 
  postgres:
    image: timescale/timescaledb:2.14.2-pg16
    environment:
      POSTGRES_DB:       stryke_x
      POSTGRES_USER:     quant
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d   # Schema bootstrap
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quant -d stryke_x"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:v1.9.2
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"   # REST API
      - "6334:6334"   # gRPC

  # Cognitive Layer 
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Application Layer 
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    environment:
      DATABASE_URL:  postgresql+asyncpg://quant:${DB_PASSWORD}@postgres:5432/stryke_x
      REDIS_URL:     redis://redis:6379/0
      QDRANT_URL:    http://qdrant:6333
      OLLAMA_URL:    http://ollama:11434
    ports:
      - "8001:8000"
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_started }
      qdrant:   { condition: service_started }
    volumes:
      - parquet_cache:/app/.stryke/cache

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5075:80"
    depends_on:
      - backend

volumes:
  pg_data:
  redis_data:
  qdrant_data:
  ollama_models:
  parquet_cache:
```

### 9.2 Service Dependency Graph

```
                Frontend     Vite dev / Nginx prod
               :5075      
                     HTTP
                Backend      FastAPI + uvicorn workers
               :8001      
Postgres    Redis       Qdrant  
:5432       :6379       :6333   
                            
                              Ollama    
                              :11434    
```

---

## 10. Quantitative Research Methodology

### 10.1 Backtesting Integrity Framework

Every backtest executed by Stryke X is subject to the following **mandatory integrity constraints**:

```
BIAS PREVENTION CHECKLIST

1. LOOKAHEAD BIAS
    All indicator values computed on t-1 data before signal at t
    Signal arrays shifted forward by 1 bar before portfolio entry
    Verified: entries[t] uses only OHLCV data up to and including bar t-1

2. SURVIVORSHIP BIAS
    Current: yfinance universe includes delisted instruments partially
    Mitigation: TimescaleDB ingest pipeline flags delisted symbols
    Roadmap: NSE historical constituent database integration

3. OVERFITTING / DATA SNOOPING
    Walk-forward validation recommended: IS 70% / OOS 30%
    Parameter sensitivity analysis via Monte Carlo perturbation
    Multiple-testing correction: Bonferroni / BHY procedure on metrics

4. TRANSACTION COST REALISM
    NSE equity: ~0.05% round-trip (Zerodha / flat fee broker)
    NSE F&O: STT on sell side + 0.03% brokerage + ~0.02% impact
    Slippage model: symmetric uniform ε on execution price

5. REGIME CONDITIONING
    Sharpe decomposed by market regime (VIX quintile, trend state)
    Strategy performance evaluated across: Bull / Bear / Sideways
```

### 10.2 Statistical Validation Pipeline

```
STRATEGY VALIDATION WORKFLOW

Step 1: IN-SAMPLE CALIBRATION
  Period    : T_start  T_split (70% of data)
  Goal      : Initial parameter estimation
  KPI Gate  : Sharpe > 0.5 in-sample (raw)

Step 2: OUT-OF-SAMPLE VALIDATION
  Period    : T_split  T_end (30% of data)
  Goal      : Unbiased performance estimate
  KPI Gate  : Sharpe degradation < 40% vs IS

Step 3: WALK-FORWARD ANALYSIS
  Window    : Rolling 252-bar IS, 63-bar OOS
  Folds     : ~(T / 63) - 4 non-overlapping OOS windows
  Aggregate : Mean OOS Sharpe, OOS Win Rate
  KPI Gate  : OOS Sharpe > 0.3

Step 4: MONTE CARLO STRESS TEST
  Method    : Bootstrap 10,000 trade sequence permutations
  Metrics   : P5 Sharpe, P5 Max DD, P95 CAGR
  KPI Gate  : P5 Max DD < -25%

Step 5: PARAMETER SENSITIVITY
  Method    : Grid perturbation 20% each parameter
  Metric    : Sharpe gradient S/θ_i for each param θ_i
  KPI Gate  : No parameter with |S/θ_i| > 0.5 (cliff edge)

Step 6: REGIME ANALYSIS
  Segment   : VIX quintile buckets (Q1=low vol  Q5=crisis)
  Metric    : Conditional Sharpe per regime
  KPI Gate  : Positive Sharpe in  3 of 5 VIX quintiles

PASS/FAIL MATRIX
  Gate       Weight  Required
  Step 2      30%    MUST PASS
  Step 3      30%    MUST PASS
  Step 4      20%    MUST PASS
  Step 5      10%    RECOMMENDED
  Step 6      10%    RECOMMENDED
```

---

## 11. Performance Benchmarks & Complexity Analysis

### Computational Complexity

| Operation | Time Complexity | Space Complexity | Notes |
|---|---|---|---|
| OHLCV query (TimescaleDB) | O(log N_chunks + K) | O(K) | N=total bars, K=result rows; chunk pruning makes this effectively O(K) |
| Indicator computation (TA-Lib) | O(T) | O(T) | FFTW3 for FFT-based indicators; O(T log T) for spectral methods |
| Signal matrix evaluation | O(T  C) | O(T  C) | C = number of conditions; fully vectorized in NumPy |
| VectorBT portfolio simulation | O(T) | O(T) | Single-pass trade log construction via Numba JIT |
| Sharpe/Sortino/MDD | O(T) | O(1)* | *Streaming algorithms; MDD is O(T) time, O(1) space |
| Redis cache read | O(1) | O(|payload|) | Hash table lookup |
| Qdrant vector search | O(log N_vectors) | O(K  D) | HNSW; K=top-k, D=1024 dims |

### Empirical Throughput (Benchmarks, i9-13900K, RTX 4090)

```
Workload                              Latency      Throughput
OHLCV query, 5yr daily (1,260 bars)   12 ms        —
Signal matrix, 3 conditions, 1260 T   2  ms        —
VectorBT simulation, 1260 T           8  ms        —
Full backtest (cache miss)            ~80 ms       ~12 RPS
Full backtest (cache hit, Redis)      <1 ms        >1,000 RPS
LLM strategy generation (R1-7B)       3–8 sec      ~0.2 RPS
Qdrant top-5 retrieval (1M vectors)   ~2 ms        —
```

---

## 12. Development Roadmap

```
STRYKE X — PRODUCT ROADMAP

Q3 2025 — CORE ENGINE HARDENING
  [x] VectorBT backtesting engine
  [x] TimescaleDB hypertable data layer
  [x] Dynamic rule compiler (AST)
  [x] Redis caching layer
  [ ] Walk-forward validation engine
  [ ] Monte Carlo stress testing module
  [ ] Parameter sensitivity surface charts

Q4 2025 — OPTIONS ANALYTICS LAYER
  [ ] Black-Scholes-Merton pricing engine
  [ ] Greeks computation: Δ, Γ, Θ, ν, ρ
  [ ] IV surface builder (strike  expiry grid)
  [ ] Max Pain calculator (NSE weekly expiry)
  [ ] PCR (Put-Call Ratio) analytics
  [ ] Options strategy P&L simulator:
        Short Straddle, Iron Condor, Iron Fly,
        Calendar Spread, Ratio Spread

Q1 2026 — EXECUTION INTELLIGENCE
  [ ] DhanHQ WebSocket live feed integration
  [ ] Order flow imbalance signals (bid-ask delta)
  [ ] VWAP / TWAP deviation alerts
  [ ] Live paper trading mode (simulated fills)
  [ ] Regime detection (HMM-based, 3-state)

Q2 2026 — INSTITUTIONAL RESEARCH FEATURES
  [ ] Factor exposure decomposition (Fama-French)
  [ ] Strategy correlation matrix & diversification score
  [ ] Institutional-grade PDF research report export
  [ ] Multi-strategy portfolio optimiser (mean-variance)
  [ ] FinBERT news sentiment integration
  [ ] Alternative data: FII/DII flow signals
```

---

## 13. Contributing & Standards

### Code Quality Standards

```python
# All contributions must satisfy:

# 1. Type annotations (PEP 484)
def compute_sharpe(returns: pd.Series, rf: float = 0.065) -> float: ...

# 2. Vectorized operations — no Python loops on time-series
#  BAD  (O(T) Python overhead)
signals = [close[i] > sma[i] for i in range(len(close))]
#  GOOD (O(T) NumPy BLAS)
signals = (close.values > sma.values)

# 3. Docstrings with parameter types and mathematical definitions
def max_drawdown(equity_curve: np.ndarray) -> float:
    """
    Compute the maximum drawdown of an equity curve.

    Definition:
        MDD = max_{t  [0,T]} [ max_{s  t} V(s) - V(t) ] / max_{s  t} V(s)

    Parameters
    ----------
    equity_curve : np.ndarray of shape (T,)
        Portfolio value at each time step.

    Returns
    -------
    float
        Maximum drawdown as a negative fraction (e.g., -0.25 = -25%).
    """

# 4. Unit tests for all compiler and metric functions
# pytest tests/ -v --cov=app --cov-report=term-missing
```

### Git Branch Strategy
```
main           production; protected; requires 2 approvals
   develop   integration branch; CI must pass
        feat/options-greeks-engine
        feat/walk-forward-validator
        fix/compiler-crossover-lookahead
        infra/timescaledb-compression-policy
```

### Environment Variables

```bash
# .env.example — copy to .env and populate

# Database
DATABASE_URL=postgresql+asyncpg://quant:CHANGEME@localhost:5432/stryke_x
DB_PASSWORD=CHANGEME

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_BACKTEST=3600       # seconds
CACHE_TTL_OHLCV=86400

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b
VLLM_BASE_URL=http://localhost:8080    # production

# Vector Store
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=stryke_strategies
EMBEDDING_MODEL=BAAI/bge-m3

# Market Data
YFINANCE_TIMEOUT=30
NSE_RATE_LIMIT_RPS=2

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development   # development | production
SECRET_KEY=CHANGEME       # JWT signing key
```

---

## Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd stryke-x

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Launch infrastructure services
docker compose up -d postgres redis qdrant
docker compose logs -f postgres   # Wait for "database system is ready"

# 4. Ingest 14 years of historical OHLCV data
docker exec -it quant_backend python scripts/ingest_historical.py \
  --symbols NIFTY BANKNIFTY FINNIFTY \
  --resolution 1d 1h \
  --start 2010-01-01

# 5. Pull and serve the reasoning model
docker compose up -d ollama
docker exec -it stryke-ollama ollama pull deepseek-r1:7b

# 6. Seed strategy templates
docker exec -it quant_backend python scripts/seed_auto_strategies.py
docker exec -it quant_backend python seed_strategies.py

# 7. Start services
docker compose up -d backend frontend

# Platform available at:
#   Frontend : http://localhost:5075
#   API docs  : http://localhost:8001/docs   (OpenAPI 3.1)
#   TimescaleDB: localhost:5432 (psql -U quant -d stryke_x)
```

---

<div align="center">

**STRYKE X** — Proprietary & Confidential

*Private Software. Reserved for institutional quantitative research and validation.*
*Unauthorised copying, distribution, or decompilation strictly prohibited.*

FinStocks.ai Unified Design System  Built for NSE/BSE Derivatives Markets

</div>
