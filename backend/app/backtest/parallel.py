import asyncio
from typing import Dict, List, Any
from .engine import BacktestEngine
from .options_engine import OptionsEngine

async def run_multi_backtest(strategies: List[Dict[str, Any]], symbol: str, period: str, market_provider) -> Dict[str, Any]:
    """
    Runs multiple backtests concurrently on the same underlying data.
    """
    if not strategies:
        return {}
        
    # Fetch data once for all strategies
    df = await market_provider.get_historical_data(symbol, period=period)
    
    if df.empty:
        raise ValueError(f"No market data found for {symbol} over {period}")
        
    async def _run_single(strategy_id: str, strategy_spec: dict):
        # Run CPU-bound backtest in thread pool to avoid blocking event loop
        def _execute():
            inst_type = strategy_spec.get('instrument_type', 'EQUITY').upper()
            if inst_type == 'OPTION':
                engine = OptionsEngine()
            else:
                engine = BacktestEngine()
            return engine.run(df.copy(), strategy_spec)
            
        try:
            result = await asyncio.to_thread(_execute)
            return strategy_id, result
        except Exception as e:
            print(f"Parallel Backtest Error [{strategy_id}]: {e}")
            return strategy_id, {"error": str(e)}

    # Schedule all executions
    tasks = []
    for strat in strategies:
        strat_id = strat.get("id", "default")
        spec = strat.get("strategy_spec", {})
        tasks.append(_run_single(strat_id, spec))
        
    # Gather results concurrently
    results_list = await asyncio.gather(*tasks)
    
    return {strat_id: res for strat_id, res in results_list}
