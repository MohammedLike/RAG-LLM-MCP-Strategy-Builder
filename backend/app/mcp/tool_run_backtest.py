from pydantic import BaseModel, Field
from ..backtest.engine import BacktestEngine
from ..backtest.cache import backtest_cache
from ..market.provider_yfinance import YFinanceProvider
from datetime import datetime, timedelta

engine = BacktestEngine()
provider = YFinanceProvider()

LAST_BACKTEST = {}

class RunBacktestInput(BaseModel):
    strategy_spec: dict = Field(description="JSON spec with 'entry'/'exit' conditions, 'instrument_type' (EQUITY/OPTION), 'strike', 'option_type'")
    symbol: str = Field(description="Symbol to backtest on (e.g., 'NIFTY', 'RELIANCE', 'BANKNIFTY')")
    period: str = Field(description="Period: '1y', '2y', '5y', '8y'", default="1y")

async def run_backtest_tool(input_data: RunBacktestInput) -> dict:
    global LAST_BACKTEST
    try:
        cached = await backtest_cache.get(input_data.symbol, input_data.period, input_data.strategy_spec)
        if cached:
            LAST_BACKTEST = dict(cached)
            LAST_BACKTEST['equity_curve_sample'] = LAST_BACKTEST.get('equity_curve', [])[:5] + [{"...": "..."}] + LAST_BACKTEST.get('equity_curve', [])[-5:]
            LAST_BACKTEST['total_trades'] = len(LAST_BACKTEST.get('trades', []))
            LAST_BACKTEST['message'] = "Returned cached result."
            LAST_BACKTEST['cached'] = True
            return LAST_BACKTEST

        days_map = {"1y": 365, "2y": 730, "5y": 1825, "8y": 2920}
        days = days_map.get(input_data.period, 365)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        strategy_spec = {**input_data.strategy_spec, "symbol": input_data.symbol}
        df = await provider.get_ohlcv(input_data.symbol, interval="1d", start=start_date, end=end_date)

        if df.empty:
            return {"error": f"No data found for {input_data.symbol} in the requested period."}

        result = engine.run(df, strategy_spec)

        LAST_BACKTEST = {
            "symbol": input_data.symbol,
            "period": input_data.period,
            "strategy_spec": input_data.strategy_spec,
            "timestamp": datetime.utcnow().isoformat(),
            **result
        }

        LAST_BACKTEST['equity_curve_sample'] = LAST_BACKTEST.get('equity_curve', [])[:5] + [{"...": "..."}] + LAST_BACKTEST.get('equity_curve', [])[-5:]
        LAST_BACKTEST['total_trades'] = len(LAST_BACKTEST.get('trades', []))
        LAST_BACKTEST['message'] = f"Successfully ran backtest on {input_data.symbol} for {input_data.period} period."
        LAST_BACKTEST['cached'] = False

        await backtest_cache.set(input_data.symbol, input_data.period, input_data.strategy_spec, LAST_BACKTEST)

        return LAST_BACKTEST
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Backtest Tool Error: {error_detail}")
        return {"error": str(e)}
