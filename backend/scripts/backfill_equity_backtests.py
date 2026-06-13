"""
Run real backtests for all equity strategies using OHLCV data from Postgres.
Stores results in strategies.backtest_results (no fake stats).

Usage (inside backend container):
  python scripts/backfill_equity_backtests.py
  python scripts/backfill_equity_backtests.py --symbol NIFTY --period 2y --limit 20
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.backtest.engine import BacktestEngine
from app.backtest.metrics import compute_monthly_returns_by_year
from app.market.provider_yfinance import YFinanceProvider
from app.strategies.compiler import compile_db_strategy

DATABASE_URL = "postgresql+asyncpg://quant_user:quant_password@postgres:5432/quant_db"
EXCLUDED = ("Options", "Indicator Based", "Fundamental")

engine_bt = BacktestEngine()
provider = YFinanceProvider()


async def backfill(symbol: str, period: str, limit: int | None):
    days_map = {"1y": 365, "2y": 730, "5y": 1825, "8y": 2920}
    days = days_map.get(period, 730)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    db_engine = create_async_engine(DATABASE_URL)
    Session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    df = await provider.get_ohlcv(symbol, "1d", start_date, end_date)
    if df.empty:
        print(f"No OHLCV data for {symbol}. Seed market data first.")
        return

    print(f"Loaded {len(df)} OHLCV rows for {symbol} ({period})")

    async with Session() as session:
        result = await session.execute(
            text(
                "SELECT slug, name, category, hypothesis, entry_rules, exit_rules, risk_params "
                "FROM strategies "
                "WHERE category NOT IN ('Options', 'Indicator Based', 'Fundamental') "
                "ORDER BY name ASC"
            )
        )
        rows = result.fetchall()
        if limit:
            rows = rows[:limit]

        ok, fail = 0, 0
        for row in rows:
            slug, name, category = row[0], row[1], row[2]
            db_strat = {
                "name": name,
                "slug": slug,
                "category": category,
                "hypothesis": row[3],
                "entry_rules": row[4],
                "exit_rules": row[5],
                "risk_params": row[6],
            }
            try:
                spec = compile_db_strategy(db_strat)
                if spec.get("instrument_type", "EQUITY").upper() == "OPTION":
                    continue
                spec = {**spec, "symbol": symbol, "instrument_type": "EQUITY"}
                bt = engine_bt.run(df.copy(), spec)
                equity_curve = bt.get("equity_curve", [])
                stored = {
                    "source": "live_backtest",
                    "backtested_at": datetime.utcnow().isoformat(),
                    "symbol": symbol,
                    "period": period,
                    "total_return": bt.get("total_return"),
                    "win_rate": bt.get("win_rate"),
                    "sharpe": bt.get("sharpe"),
                    "sortino": bt.get("sortino"),
                    "max_drawdown": bt.get("max_drawdown"),
                    "cagr": bt.get("cagr"),
                    "profit_factor": bt.get("profit_factor"),
                    "expectancy": bt.get("expectancy"),
                    "total_trades": len(bt.get("trades", [])),
                    "equity_curve": equity_curve,
                    "monthly_returns": compute_monthly_returns_by_year(equity_curve),
                    "drawdown": bt.get("drawdown", []),
                }
                await session.execute(
                    text("UPDATE strategies SET backtest_results = :results WHERE slug = :slug"),
                    {"results": json.dumps(stored), "slug": slug},
                )
                ok += 1
                print(
                    f"  OK  {slug[:40]:40} return={stored['total_return']:.2f}% "
                    f"trades={stored['total_trades']} wr={stored['win_rate']:.0f}%"
                )
            except Exception as e:
                fail += 1
                print(f"  FAIL {slug}: {e}")

        await session.commit()
        print(f"\nDone: {ok} backtests saved, {fail} failed.")

    await db_engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="NIFTY")
    parser.add_argument("--period", default="2y")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(backfill(args.symbol, args.period, args.limit))
