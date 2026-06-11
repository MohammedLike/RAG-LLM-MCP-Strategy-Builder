from fastapi import APIRouter
from ..mcp.tool_run_backtest import run_backtest_tool, RunBacktestInput, LAST_BACKTEST
from ..backtest.indicators import IndicatorManager

router = APIRouter()

@router.get("/indicators")
async def get_indicators():
    return IndicatorManager.get_indicators_list()

@router.get("/backtest/latest")
async def get_latest_backtest():
    """Returns the full data of the last executed backtest."""
    return LAST_BACKTEST

@router.post("/backtest")
async def run_backtest(request: RunBacktestInput):
    # Execute the backtest tool
    summary = await run_backtest_tool(request)
    if "error" in summary:
        return summary
    # When called directly, return the full cached result instead of the trimmed summary
    return LAST_BACKTEST

@router.get("/backtest/{id}")
async def get_backtest(id: str):
    return {"status": "completed", "id": id, "results": {}}


