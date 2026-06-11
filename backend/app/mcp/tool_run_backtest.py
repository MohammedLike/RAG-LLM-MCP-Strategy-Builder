from pydantic import BaseModel, Field
from ..backtest.engine import BacktestEngine
from ..market.provider_yfinance import YFinanceProvider
from datetime import datetime, timedelta

engine = BacktestEngine()
provider = YFinanceProvider()

class RunBacktestInput(BaseModel):
    strategy_spec: dict = Field(description="JSON spec of the strategy with 'entry' and 'exit' conditions.")
    symbol: str = Field(description="Symbol to backtest on (e.g., 'NIFTY', 'RELIANCE')")
    period: str = Field(description="Period to backtest, e.g., '1y', '5y', '8y'", default="1y")

async def run_backtest_tool(input_data: RunBacktestInput) -> dict:
    """
    Runs a strategy backtest using the backtest engine and historical data.
    """
    try:
        # 1. Parse Period and Fetch Data
        # Simplified period parsing (e.g., '1y' -> 365 days)
        days_map = {"1y": 365, "2y": 730, "5y": 1825, "8y": 2920}
        days = days_map.get(input_data.period, 365)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Fetch OHLCV data
        df = await provider.get_ohlcv(input_data.symbol, interval="1d", start=start_date, end=end_date)
        
        if df.empty:
            return {"error": f"No data found for {input_data.symbol} in the requested period."}
            
        # 2. Run Engine
        result = engine.run(df, input_data.strategy_spec)
        
        # 3. Trim Large Data for LLM Context (e.g., only return summary metrics and truncated curve)
        summary = {k: v for k, v in result.items() if k not in ['equity_curve', 'drawdown', 'trades']}
        summary['equity_curve_sample'] = result['equity_curve'][:5] + [{"...": "..."}] + result['equity_curve'][-5:]
        summary['total_trades'] = len(result['trades'])
        
        return summary
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Backtest Tool Error: {error_detail}")
        return {"error": str(e)}
