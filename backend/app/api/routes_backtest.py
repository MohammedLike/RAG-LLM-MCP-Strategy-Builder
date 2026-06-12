from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from ..mcp.tool_run_backtest import run_backtest_tool, RunBacktestInput, LAST_BACKTEST
from ..backtest.indicators import IndicatorManager
from ..backtest.engine import BacktestEngine
from ..backtest.cache import backtest_cache
from ..market.provider_yfinance import YFinanceProvider
from datetime import datetime, timedelta
import uuid
import asyncio
from typing import Optional

router = APIRouter()

engine = BacktestEngine()
provider = YFinanceProvider()

_tasks: dict = {}

class AsyncBacktestRequest(BaseModel):
    strategy_spec: dict
    symbol: str
    period: str = "1y"

class BacktestStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None

@router.get("/indicators")
async def get_indicators():
    return IndicatorManager.get_indicators_list()

@router.get("/backtest/latest")
async def get_latest_backtest():
    return LAST_BACKTEST

@router.post("/backtest")
async def run_backtest(request: RunBacktestInput):
    summary = await run_backtest_tool(request)
    if "error" in summary:
        return summary
    return LAST_BACKTEST

@router.post("/backtest/async")
async def run_backtest_async(requests: list[AsyncBacktestRequest], background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "running", "result": None}

    async def execute():
        try:
            results = []
            for req in requests:
                days_map = {"1y": 365, "2y": 730, "5y": 1825, "8y": 2920}
                days = days_map.get(req.period, 365)
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)

                cached = await backtest_cache.get(req.symbol, req.period, req.strategy_spec)
                if cached:
                    results.append({"symbol": req.symbol, "period": req.period, "cached": True, **cached})
                    continue

                df = await provider.get_ohlcv(req.symbol, "1d", start_date, end_date)
                if df.empty:
                    results.append({"symbol": req.symbol, "error": f"No data for {req.symbol}"})
                    continue

                strategy_spec = {**req.strategy_spec, "symbol": req.symbol}
                result = engine.run(df, strategy_spec)
                await backtest_cache.set(req.symbol, req.period, req.strategy_spec, result)
                results.append({"symbol": req.symbol, "period": req.period, **result})

            _tasks[task_id] = {"status": "completed", "result": results}
        except Exception as e:
            _tasks[task_id] = {"status": "failed", "error": str(e)}

    background_tasks.add_task(execute)
    return {"task_id": task_id, "status": "running"}

@router.get("/backtest/async/{task_id}")
async def get_async_result(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return task

@router.get("/backtest/{id}")
async def get_backtest(id: str):
    return {"status": "completed", "id": id}
