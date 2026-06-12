from .tool_fetch_market import fetch_market_data, FetchMarketInput
from .tool_query_strategy import query_strategy_data, QueryStrategyInput
from .tool_run_backtest import run_backtest_tool, RunBacktestInput
from .tool_analyse_greeks import analyse_greeks_tool, AnalyseGreeksInput

TOOLS = [
    {
        "name": "fetch_market",
        "description": "Fetch live or historical market data for Equity, Futures, and Options",
        "schema": FetchMarketInput,
        "func": fetch_market_data
    },
    {
        "name": "query_strategy",
        "description": "Query strategy knowledge base via RAG for Equity, Futures, and Options",
        "schema": QueryStrategyInput,
        "func": query_strategy_data
    },
    {
        "name": "run_backtest",
        "description": "Run strategy backtest. Params: symbol, period (1y/2y/5y/8y), strategy_spec (entry/exit conditions), optional instrument_type/strike/option_type for options",
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
