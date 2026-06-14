"""API routes for NIFTY options backtesting on stored options_chain data."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..backtest.options_chain_engine import OptionsChainBacktestEngine
from ..db.options_chain_store import get_chain_status, get_expiries_on_date, list_strikes_on_date

router = APIRouter(prefix="/options-backtest", tags=["options-backtest"])
_engine = OptionsChainBacktestEngine()


class OptionsBacktestRequest(BaseModel):
    run_name: str | None = None
    symbol: str = "NIFTY"
    start_date: str
    end_date: str
    option_type: str = "CE"
    strike: str = "ATM"
    expiry: str | None = None
    expiry_mode: str = "nearest_weekly"
    entry_condition: str = "always"
    exit_condition: str = "rsi_above_70"
    is_credit: bool = False
    trade_type: str = "positional"
    trade_start: str = "09:15"
    trade_end: str = "15:25"
    max_trades_per_day: int = 1
    txn_stop_loss: float | None = None
    txn_stop_loss_unit: str = "%"
    txn_take_profit: float | None = None
    txn_take_profit_unit: str = "%"
    daily_stop_loss: float | None = None
    daily_take_profit: float | None = None
    lot_size: int = 50
    initial_capital: float = 100000


@router.get("/status")
async def options_data_status(symbol: str = "NIFTY"):
    return await get_chain_status(symbol)


@router.get("/expiries")
async def options_expiries(symbol: str = "NIFTY", on_date: str | None = None):
    d = _parse(on_date) or (date.today() - timedelta(days=1))
    expiries = await get_expiries_on_date(symbol, d)
    return {"symbol": symbol.upper(), "on_date": str(d), "expiries": expiries}


@router.get("/strikes")
async def options_strikes(symbol: str = "NIFTY", on_date: str | None = None, option_type: str = "CE"):
    d = _parse(on_date) or (date.today() - timedelta(days=1))
    strikes = await list_strikes_on_date(symbol, d, option_type)
    return {"symbol": symbol.upper(), "on_date": str(d), "strikes": strikes}


@router.post("/run")
async def run_options_backtest(request: OptionsBacktestRequest):
    status = await get_chain_status(request.symbol)
    if not status.get("available"):
        raise HTTPException(503, "No options chain data in database. Run ingest_nifty_options_history.py first.")

    start = _parse(request.start_date)
    end = _parse(request.end_date)
    if not start or not end:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    db_start = _parse(status["from_date"])
    db_end = _parse(status["to_date"])
    if db_start and start < db_start:
        raise HTTPException(400, f"Data starts from {db_start}. Adjust start_date.")
    if db_end and end > db_end:
        raise HTTPException(400, f"Data ends at {db_end}. Adjust end_date.")

    result = await _engine.run(request.model_dump())
    if result.get("error"):
        raise HTTPException(422, result["error"])
    return result


def _parse(val: str | None) -> date | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(val[:10], fmt).date()
        except ValueError:
            continue
    return None
