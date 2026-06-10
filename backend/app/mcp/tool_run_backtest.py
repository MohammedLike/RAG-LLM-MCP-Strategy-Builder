from pydantic import BaseModel, Field

class RunBacktestInput(BaseModel):
    strategy_spec: dict = Field(description="JSON spec of the strategy")
    symbol: str = Field(description="Symbol to backtest on")
    period: str = Field(description="Time period to backtest, e.g., '1y'")

def run_backtest_tool(input_data: RunBacktestInput) -> dict:
    """
    Simulates running a backtest using VectorBT.
    """
    return {
        "sharpe": 1.5,
        "sortino": 2.1,
        "max_drawdown": -0.15,
        "equity_curve": []
    }
