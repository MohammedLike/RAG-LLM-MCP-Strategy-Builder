"""Incremental daily OHLCV refresh — append bars since last DB date."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd
import yfinance as yf
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from ..backtest.cache import backtest_cache
from ..db.models import OHLCV
from ..db.session import async_session, is_db_available
from .ingest_progress import ingest_progress

SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "CNXFIN.NS",
    "SENSEX": "^BSESN",
    "NIFTY100": "^CNX100",
    "NIFTY500": "^CRSLDX",
}

UTC = timezone.utc


def get_ticker_symbol(sym: str) -> str:
    return SYMBOL_MAP.get(sym.upper(), f"{sym.upper()}.NS")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def default_refresh_args(**overrides) -> SimpleNamespace:
    base = {
        "symbols": None,
        "concurrency": 12,
        "batch_size": 80,
        "pause": 0.8,
        "max_symbols": 0,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


async def fetch_symbol_last_dates(symbols: list[str] | None) -> list[tuple[str, datetime | None]]:
    async with async_session() as session:
        if symbols:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT symbol, MAX(time) AS last_time
                        FROM ohlcv
                        WHERE resolution = '1d' AND symbol = ANY(:symbols)
                        GROUP BY symbol
                        """
                    ),
                    {"symbols": symbols},
                )
            ).mappings().all()
            found = {r["symbol"]: r["last_time"] for r in rows}
            return [(s, found.get(s)) for s in symbols]

        rows = (
            await session.execute(
                text(
                    """
                    SELECT symbol, MAX(time) AS last_time
                    FROM ohlcv
                    WHERE resolution = '1d'
                    GROUP BY symbol
                    ORDER BY symbol
                    """
                )
            )
        ).mappings().all()
        return [(r["symbol"], r["last_time"]) for r in rows]


async def download_delta(symbol: str, ticker: str, start: datetime, end: datetime) -> list[dict]:
    def _fetch(t: str):
        return yf.download(t, start=start, end=end, interval="1d", progress=False, auto_adjust=True)

    df = await asyncio.to_thread(_fetch, ticker)
    if df.empty and ticker.endswith(".NS"):
        df = await asyncio.to_thread(_fetch, ticker.replace(".NS", ".BO"))

    if df.empty:
        return []

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df = df.reset_index()
    df = df.rename(columns={df.columns[0]: "time"})
    df.columns = [c.lower() for c in df.columns]

    records = []
    for _, row in df.iterrows():
        t_val = row["time"]
        dt = t_val.to_pydatetime() if hasattr(t_val, "to_pydatetime") else pd.to_datetime(t_val).to_pydatetime()
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        records.append(
            {
                "time": dt,
                "symbol": symbol,
                "resolution": "1d",
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]) if not pd.isna(row.get("volume")) else 0,
            }
        )
    return records


async def upsert_records(records: list[dict]) -> None:
    if not records:
        return
    for i in range(0, len(records), 3000):
        chunk = records[i : i + 3000]
        async with async_session() as session:
            stmt = insert(OHLCV).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="ohlcv_unique_pk",
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                },
            )
            await session.execute(stmt)
            await session.commit()


async def run_refresh(args) -> dict:
    if not is_db_available():
        raise RuntimeError("Database unavailable")

    if getattr(args, "symbols", None):
        targets = [(s.upper(), get_ticker_symbol(s)) for s in args.symbols]
        last_dates = dict(await fetch_symbol_last_dates([s for s, _ in targets]))
        work = [(s, t, last_dates.get(s)) for s, t in targets]
    else:
        rows = await fetch_symbol_last_dates(None)
        max_symbols = getattr(args, "max_symbols", 0) or 0
        if max_symbols:
            rows = rows[:max_symbols]
        work = [(sym, get_ticker_symbol(sym), last) for sym, last in rows]

    end = _utcnow() + timedelta(days=1)
    sem = asyncio.Semaphore(getattr(args, "concurrency", 12))
    queue: list[dict] = []
    updated = 0
    skipped = 0
    failed: list[dict] = []
    new_bars = 0

    await ingest_progress.start(len(work), job_type="daily_refresh")

    async def process(symbol: str, ticker: str, last_time: datetime | None) -> None:
        nonlocal updated, skipped, new_bars
        async with sem:
            try:
                if last_time and hasattr(last_time, "tzinfo") and last_time.tzinfo:
                    last_time = last_time.replace(tzinfo=None)
                start = (last_time + timedelta(days=1)) if last_time else (_utcnow() - timedelta(days=30))
                if start.date() >= end.date():
                    skipped += 1
                    await ingest_progress.tick(symbol, True, 0)
                    return

                records = await download_delta(symbol, ticker, start, end)
                if records:
                    queue.extend(records)
                    new_bars += len(records)
                    if len(queue) >= 3000:
                        await upsert_records(queue[:3000])
                        del queue[:3000]
                    updated += 1
                else:
                    skipped += 1
                await ingest_progress.tick(symbol, bool(records), len(records))
            except Exception as e:
                failed.append({"symbol": symbol, "error": str(e)})
                await ingest_progress.tick(symbol, False, error=str(e))

    batch_size = getattr(args, "batch_size", 80)
    pause = getattr(args, "pause", 0.8)
    for i in range(0, len(work), batch_size):
        batch = work[i : i + batch_size]
        await asyncio.gather(*[process(s, t, lt) for s, t, lt in batch])
        await asyncio.sleep(pause)

    if queue:
        await upsert_records(queue)

    await backtest_cache.invalidate()
    summary = await ingest_progress.finish("completed")
    summary["updated_symbols"] = updated
    summary["skipped_symbols"] = skipped
    summary["failed"] = failed
    summary["new_bars"] = new_bars
    return summary
