from fastapi import APIRouter
from ..mcp.tool_run_backtest import run_backtest_tool, RunBacktestInput

router = APIRouter()

@router.post("/backtest")
async def run_backtest(request: RunBacktestInput):
    return await run_backtest_tool(request)

@router.get("/backtest/{id}")
async def get_backtest(id: str):
    return {"status": "completed", "id": id, "results": {}}
