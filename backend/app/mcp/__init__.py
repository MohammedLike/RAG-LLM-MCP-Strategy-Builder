from .tool_fetch_market import fetch_market_data, FetchMarketInput
from .tool_query_strategy import query_strategy_data, QueryStrategyInput
from .tool_run_backtest import run_backtest_tool, RunBacktestInput
from .tool_analyse_greeks import analyse_greeks_tool, AnalyseGreeksInput

# Exposing tools for MCP server
TOOLS = [
    {
        "name": "fetch_market",
        "description": "Fetch live or historical market data",
        "schema": FetchMarketInput,
        "func": fetch_market_data
    },
    {
        "name": "query_strategy",
        "description": "Query strategy knowledge base via RAG",
        "schema": QueryStrategyInput,
        "func": query_strategy_data
    },
    {
        "name": "run_backtest",
        "description": "Run strategy backtest",
        "schema": RunBacktestInput,
        "func": run_backtest_tool
    },
    {
        "name": "analyse_greeks",
        "description": "Analyse options greeks",
        "schema": AnalyseGreeksInput,
        "func": analyse_greeks_tool
    }
]
