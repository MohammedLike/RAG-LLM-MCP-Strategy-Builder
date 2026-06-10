from fastapi import APIRouter
from pydantic import BaseModel
from ..backtest.engine import BacktestEngine

router = APIRouter()
engine = BacktestEngine()

class BacktestRequest(BaseModel):
    strategy_spec: dict
    symbol: str
    period: str

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    return engine.run(request.strategy_spec, request.symbol, request.period)

@router.get("/backtest/{id}")
async def get_backtest(id: str):
    return {"status": "completed", "id": id, "results": {}}
