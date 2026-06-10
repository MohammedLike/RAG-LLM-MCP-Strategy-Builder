from pydantic import BaseModel, Field
from ..backtest.engine import BacktestEngine

engine = BacktestEngine()

class RunBacktestInput(BaseModel):
    strategy_spec: dict = Field(description="JSON spec of the strategy")
    symbol: str = Field(description="Symbol to backtest on")
    period: str = Field(description="Time period to backtest, e.g., '1y'")

async def run_backtest_tool(input_data: RunBacktestInput) -> dict:
    """
    Runs a strategy backtest using the backtest engine.
    """
    try:
        # In a real setup, this would be an async call or run in a thread
        result = engine.run(input_data.strategy_spec, input_data.symbol, input_data.period)
        return result
    except Exception as e:
        print(f"Backtest Error: {e}")
        return {"error": str(e)}
