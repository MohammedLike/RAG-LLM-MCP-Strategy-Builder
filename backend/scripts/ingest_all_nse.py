"""
Bulk ingest NSE/BSE daily OHLCV (default: 7 years) into TimescaleDB.

Usage:
  cd backend
  python scripts/ingest_all_nse.py
  python scripts/ingest_all_nse.py --years 7 --concurrency 8
  python scripts/ingest_all_nse.py --symbols NIFTY BANKNIFTY RELIANCE --years 7
  python scripts/ingest_all_nse.py --resume
  python scripts/ingest_all_nse.py --limit 50   # smoke test

Docker:
  docker exec -it quant_backend python scripts/ingest_all_nse.py --years 7
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
import uuid
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import OHLCV
from app.db.session import async_session, is_db_available
from app.market.ingest_progress import ingest_progress

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../company_profiles.csv"))
CHECKPOINT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/ingest_checkpoint.json"))

SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "CNXFIN.NS",
    "SENSEX": "^BSESN",
    "NIFTY100": "^CNX100",
    "NIFTY500": "^CRSLDX",
}


def get_ticker_symbol(sym: str) -> str:
    return SYMBOL_MAP.get(sym.upper(), f"{sym.upper()}.NS")


def load_tickers(only: list[str] | None = None) -> list[tuple[str, str]]:
    tickers: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(sym: str) -> None:
        key = sym.upper()
        if key in seen:
            return
        seen.add(key)
        tickers.append((key, get_ticker_symbol(key)))

    if only:
        for sym in only:
            add(sym)
        return tickers

    for index_sym in SYMBOL_MAP:
        add(index_sym)

    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = (row.get("ticker") or "").strip()
                if sym:
                    add(sym)
    return tickers


def load_checkpoint() -> set[str]:
    if not os.path.exists(CHECKPOINT_PATH):
        return set()
    try:
        data = json.loads(open(CHECKPOINT_PATH, encoding="utf-8").read())
        return set(data.get("completed", []))
    except Exception:
        return set()


def save_checkpoint(completed: set[str]) -> None:
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({"completed": sorted(completed), "updated": datetime.utcnow().isoformat()}, f)


async def create_db_job(total: int, years: int) -> str | None:
    if not is_db_available():
        return None
    job_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO ingest_jobs (id, job_type, status, total_symbols, metadata)
                VALUES (CAST(:id AS uuid), 'nse_bse_daily', 'running', :total, CAST(:meta AS jsonb))
                """
            ),
            {"id": job_id, "total": total, "meta": json.dumps({"years": years})},
        )
        await session.commit()
    return job_id


async def update_db_job(job_id: str | None, completed: int, failed: list, status: str = "running") -> None:
    if not job_id or not is_db_available():
        return
    async with async_session() as session:
        await session.execute(
            text(
                """
                UPDATE ingest_jobs
                SET completed_symbols = :completed,
                    failed_symbols = CAST(:failed AS jsonb),
                    status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"id": job_id, "completed": completed, "failed": json.dumps(failed[-500:]), "status": status},
        )
        await session.commit()


async def download_symbol(
    original_sym: str,
    ticker: str,
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    def _fetch(t: str):
        return yf.download(t, start=start_date, end=end_date, interval="1d", progress=False, auto_adjust=True)

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
        records.append(
            {
                "time": dt,
                "symbol": original_sym,
                "resolution": "1d",
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]) if not pd.isna(row.get("volume")) else 0,
            }
        )
    return records


async def flush_queue(db_queue: list[dict]) -> int:
    if not db_queue:
        return 0
    chunk = db_queue[:3000]
    del db_queue[:3000]
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
    return len(chunk)


async def db_writer_task(db_queue: list[dict], finish_event: asyncio.Event) -> None:
    while not finish_event.is_set() or db_queue:
        if len(db_queue) >= 3000 or (finish_event.is_set() and db_queue):
            try:
                n = await flush_queue(db_queue)
                if n:
                    print(f"[*] Ingested {n} rows (queue remaining: {len(db_queue)})")
            except Exception as e:
                print(f"[!] Database bulk insertion error: {e}")
        await asyncio.sleep(0.5)


async def run_ingest(args: argparse.Namespace) -> None:
    if not is_db_available():
        print("[!] Database unavailable. Start Postgres first: docker compose up -d postgres")
        sys.exit(1)

    tickers = load_tickers(args.symbols or None)
    if args.limit:
        tickers = tickers[: args.limit]

    completed_set = load_checkpoint() if args.resume else set()
    if args.resume and completed_set:
        tickers = [(s, t) for s, t in tickers if s not in completed_set]
        print(f"[*] Resuming — skipping {len(completed_set)} already ingested symbols")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365 * args.years)

    print(f"[*] Ingesting {len(tickers)} symbols | {start_date.date()} → {end_date.date()} | 1d bars")

    job_id = await create_db_job(len(tickers), args.years)
    await ingest_progress.start(len(tickers), metadata={"years": args.years, "job_id": job_id})

    db_queue: list[dict] = []
    sem = asyncio.Semaphore(args.concurrency)
    finish_event = asyncio.Event()
    writer = asyncio.create_task(db_writer_task(db_queue, finish_event))

    failed: list[dict] = []
    done_count = 0

    for i in range(0, len(tickers), args.batch_size):
        batch = tickers[i : i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(tickers) - 1) // args.batch_size + 1
        print(f"\n---> Batch {batch_num}/{total_batches} ({len(batch)} symbols)")

        async def process_one(original_sym: str, ticker: str) -> None:
            nonlocal done_count
            async with sem:
                try:
                    records = await download_symbol(original_sym, ticker, start_date, end_date)
                    ok = bool(records)
                    if ok:
                        db_queue.extend(records)
                        completed_set.add(original_sym)
                        save_checkpoint(completed_set)
                        print(f"[+] {original_sym}: {len(records)} rows")
                    else:
                        failed.append({"symbol": original_sym, "error": "no data"})
                        print(f"[-] {original_sym}: no data ({ticker})")
                    done_count += 1
                    await ingest_progress.tick(original_sym, ok, len(records))
                    if done_count % 25 == 0:
                        await update_db_job(job_id, done_count, failed)
                except Exception as e:
                    failed.append({"symbol": original_sym, "error": str(e)})
                    done_count += 1
                    await ingest_progress.tick(original_sym, False, error=str(e))
                    print(f"[-] {original_sym}: {e}")

        await asyncio.gather(*[process_one(s, t) for s, t in batch])
        await asyncio.sleep(args.pause)

    finish_event.set()
    await writer
    await update_db_job(job_id, done_count, failed, status="completed")
    await ingest_progress.finish("completed")
    print(f"\n[*] Done. Symbols processed: {done_count}, failures: {len(failed)}")
    if failed:
        fail_path = os.path.join(os.path.dirname(CHECKPOINT_PATH), "ingest_failures.json")
        with open(fail_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2)
        print(f"[*] Failure log: {fail_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bulk NSE/BSE daily OHLCV ingest into Postgres")
    p.add_argument("--years", type=int, default=7, help="Years of history (default: 7)")
    p.add_argument("--concurrency", type=int, default=8, help="Parallel yfinance downloads")
    p.add_argument("--batch-size", type=int, default=50, help="Symbols per batch")
    p.add_argument("--pause", type=float, default=1.2, help="Seconds between batches (rate limit)")
    p.add_argument("--symbols", nargs="*", help="Subset of symbols (default: full catalog)")
    p.add_argument("--limit", type=int, default=0, help="Max symbols (smoke test)")
    p.add_argument("--resume", action="store_true", help="Skip symbols in checkpoint file")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(run_ingest(parse_args()))
