from pydantic import BaseModel, Field
from typing import Optional
from ..backtest.engine import BacktestEngine
from ..backtest.cache import backtest_cache
from ..backtest.ohlcv_export import serialize_ohlcv
from ..market.provider_yfinance import YFinanceProvider
from datetime import datetime, timedelta

engine = BacktestEngine()
provider = YFinanceProvider()

LAST_BACKTEST = {}

class RunBacktestInput(BaseModel):
    strategy_spec: dict = Field(description="JSON spec with 'entry'/'exit' conditions, 'instrument_type' (EQUITY/OPTION), 'strike', 'option_type'")
    symbol: str = Field(description="Symbol to backtest on (e.g., 'NIFTY', 'RELIANCE', 'BANKNIFTY')")
    period: str = Field(description="Period: '1y', '2y', '5y', '8y', '6m', '3y'", default="1y")
    interval: str = Field(description="OHLCV resolution: 1m, 5m, 15m, 1h, 1d", default="1d")
    strategy_label: Optional[str] = Field(default=None, description="Human-readable strategy name for history")
    source: str = Field(default="engine", description="engine | pipeline | ai | template")
    pine_script: Optional[str] = Field(default=None, description="Optional Pine Script source to store")
    pine_script_id: Optional[str] = Field(default=None, description="Existing pine_scripts.id or slug")
    user_request: Optional[dict] = Field(default=None, description="Original user request metadata")
    persist: bool = Field(default=True, description="Save run to Postgres backtests table")


async def _persist_backtest(input_data: RunBacktestInput, result: dict) -> dict:
    """Save pine script + backtest run to Postgres when enabled."""
    if not input_data.persist or result.get("error") or result.get("cached"):
        return result

    from ..db.pine_store import save_pine_script
    from ..db.backtest_store import save_backtest_run

    pine_id = input_data.pine_script_id
    if input_data.pine_script and not pine_id:
        saved = await save_pine_script(
            input_data.pine_script,
            name=input_data.strategy_label,
            source=input_data.source,
            symbol=input_data.symbol,
            period=input_data.period,
            resolution=input_data.interval,
            strategy_spec=input_data.strategy_spec,
            prompt=(input_data.user_request or {}).get("prompt"),
        )
        if saved:
            pine_id = saved.get("id")
            result["pine_script_id"] = pine_id
            result["pine_slug"] = saved.get("slug")

    backtest_id = await save_backtest_run(
        result,
        strategy_spec=input_data.strategy_spec,
        symbol=input_data.symbol,
        period=input_data.period,
        resolution=input_data.interval,
        strategy_label=input_data.strategy_label,
        source=input_data.source,
        pine_script_id=pine_id,
        user_request=input_data.user_request,
    )
    if backtest_id:
        result["backtest_id"] = backtest_id
    return result


async def run_backtest_tool(input_data: RunBacktestInput) -> dict:
    global LAST_BACKTEST
    try:
        cache_key_spec = {**input_data.strategy_spec, "_interval": input_data.interval}
        cached = await backtest_cache.get(input_data.symbol, input_data.period, cache_key_spec)
        if cached:
            LAST_BACKTEST = dict(cached)
            LAST_BACKTEST['equity_curve_sample'] = LAST_BACKTEST.get('equity_curve', [])[:5] + [{"...": "..."}] + LAST_BACKTEST.get('equity_curve', [])[-5:]
            LAST_BACKTEST['total_trades'] = len(LAST_BACKTEST.get('trades', []))
            LAST_BACKTEST['message'] = "Returned cached result."
            LAST_BACKTEST['cached'] = True
            if 'ohlcv' not in LAST_BACKTEST:
                LAST_BACKTEST['ohlcv'] = []
            return await _persist_backtest(input_data, LAST_BACKTEST)

        days_map = {"1y": 365, "2y": 730, "5y": 1825, "8y": 2920, "6m": 180, "3y": 1095}
        days = days_map.get(input_data.period, 365)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        strategy_spec = {**input_data.strategy_spec, "symbol": input_data.symbol}
        df = await provider.get_ohlcv(input_data.symbol, interval=input_data.interval, start=start_date, end=end_date)

        if df.empty:
            from ..market.parquet_store import read_ohlcv
            df = read_ohlcv(input_data.symbol, input_data.interval, start_date, end_date)

        if df.empty:
            return {
                "error": (
                    f"No OHLCV data for {input_data.symbol} ({input_data.interval}, {input_data.period}). "
                    "Run ingest or POST /api/pipeline/ohlcv/cache/{symbol}/{resolution}"
                )
            }

        result = engine.run(df, strategy_spec)
        data_start = str(df["time"].iloc[0])[:10] if "time" in df.columns else None
        data_end = str(df["time"].iloc[-1])[:10] if "time" in df.columns else None

        from ..backtest.metrics import compute_monthly_returns_by_year
        monthly_returns = compute_monthly_returns_by_year(result.get("equity_curve") or [])

        LAST_BACKTEST = {
            "symbol": input_data.symbol,
            "period": input_data.period,
            "interval": input_data.interval,
            "strategy_spec": input_data.strategy_spec,
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "postgres",
            "data_rows": len(df),
            "data_start": data_start,
            "data_end": data_end,
            "ohlcv": serialize_ohlcv(df),
            "monthly_returns": monthly_returns,
            **result
        }

        LAST_BACKTEST['equity_curve_sample'] = LAST_BACKTEST.get('equity_curve', [])[:5] + [{"...": "..."}] + LAST_BACKTEST.get('equity_curve', [])[-5:]
        LAST_BACKTEST['total_trades'] = len(LAST_BACKTEST.get('trades', []))
        LAST_BACKTEST['message'] = f"Successfully ran backtest on {input_data.symbol} for {input_data.period} period."
        LAST_BACKTEST['cached'] = False

        await backtest_cache.set(input_data.symbol, input_data.period, cache_key_spec, LAST_BACKTEST)

        return await _persist_backtest(input_data, LAST_BACKTEST)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Backtest Tool Error: {error_detail}")
        return {"error": str(e)}
