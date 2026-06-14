"""
Ingest NIFTY index options chain history into TimescaleDB (options_chain).

Uses free NSE public archives — no API key:
  - Legacy FO bhavcopy (pre Jul 2024)
  - UDiFF FO bhavcopy (Jul 2024+)

Usage:
  cd backend
  python scripts/ingest_nifty_options_history.py --years 5
  python scripts/ingest_nifty_options_history.py --years 5 --resume
  python scripts/ingest_nifty_options_history.py --days 5          # smoke test
  python scripts/ingest_nifty_options_history.py --symbol BANKNIFTY --years 3

Docker:
  docker exec -it quant_backend python scripts/ingest_nifty_options_history.py --years 5 --resume
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import OptionsChain
from app.db.session import async_session, is_db_available
from app.market.nse_fo_bhavcopy import _session, fetch_nifty_options_day, trading_days

CHECKPOINT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/nifty_options_ingest_checkpoint.json")
)
BATCH_SIZE = 800


def load_checkpoint() -> set[str]:
    if not os.path.exists(CHECKPOINT_PATH):
        return set()
    try:
        data = json.loads(open(CHECKPOINT_PATH, encoding="utf-8").read())
        return set(data.get("completed_dates", []))
    except Exception:
        return set()


def save_checkpoint(completed: set[str], meta: dict | None = None) -> None:
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    payload = {
        "completed_dates": sorted(completed),
        "updated": datetime.utcnow().isoformat(),
        "meta": meta or {},
    }
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


async def ensure_options_unique_index() -> None:
    migration = (
        Path(__file__).resolve().parents[2]
        / "infra"
        / "postgres"
        / "migrations"
        / "005_options_chain_unique.sql"
    )
    if not migration.exists() or not is_db_available():
        return
    sql = migration.read_text(encoding="utf-8")
    async with async_session() as session:
        await session.execute(text(sql))
        await session.commit()


async def upsert_rows(rows: list[dict]) -> int:
    if not rows or not is_db_available():
        return 0
    stored = 0
    async with async_session() as session:
        for i in range(0, len(rows), BATCH_SIZE):
            chunk = rows[i : i + BATCH_SIZE]
            stmt = insert(OptionsChain).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["time", "symbol", "expiry", "strike", "option_type"],
                set_={
                    "oi": stmt.excluded.oi,
                    "volume": stmt.excluded.volume,
                    "iv": stmt.excluded.iv,
                    "ltp": stmt.excluded.ltp,
                    "greeks_json": stmt.excluded.greeks_json,
                },
            )
            await session.execute(stmt)
            stored += len(chunk)
        await session.commit()
    return stored


async def create_job(total_days: int, symbol: str, years: float) -> str | None:
    if not is_db_available():
        return None
    job_id = str(uuid.uuid4())
    async with async_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO ingest_jobs (id, job_type, status, total_symbols, metadata)
                VALUES (CAST(:id AS uuid), 'nifty_options_fo', 'running', :total, CAST(:meta AS jsonb))
                """
            ),
            {
                "id": job_id,
                "total": total_days,
                "meta": json.dumps({"symbol": symbol, "years": years, "source": "nse_fo_bhavcopy"}),
            },
        )
        await session.commit()
    return job_id


async def update_job(job_id: str | None, completed: int, failed: list[str], status: str = "running") -> None:
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
                    updated_at = NOW()
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {
                "id": job_id,
                "completed": completed,
                "failed": json.dumps(failed[-50:]),
                "status": status,
            },
        )
        await session.commit()


async def run_ingest(
    symbol: str,
    years: float,
    days: int | None,
    resume: bool,
    pause_sec: float,
) -> None:
    global CHECKPOINT_PATH
    if symbol != "NIFTY":
        CHECKPOINT_PATH = CHECKPOINT_PATH.replace("nifty_", f"{symbol.lower()}_")

    if not is_db_available():
        print("Database unavailable. Start Postgres: docker compose up -d postgres")
        sys.exit(1)

    await ensure_options_unique_index()

    end = date.today() - timedelta(days=1)
    if days:
        start = end - timedelta(days=days)
    else:
        start = end - timedelta(days=int(years * 365.25))

    all_days = trading_days(start, end)
    completed = load_checkpoint() if resume else set()
    pending = [d for d in all_days if d.isoformat() not in completed]

    print(f"NIFTY options ingest: {symbol} | {start} to {end} | {len(pending)} trading days to fetch", flush=True)
    job_id = await create_job(len(pending), symbol, years if not days else days / 252)

    session = _session()
    total_rows = 0
    failed_days: list[str] = []
    done_count = 0

    for d in pending:
        try:
            rows = fetch_nifty_options_day(session, d, symbol=symbol, pause_sec=pause_sec)
            if not rows:
                failed_days.append(d.isoformat())
                print(f"  [{d.isoformat()}] no data (holiday or download failed)", flush=True)
            else:
                stored = await upsert_rows(rows)
                total_rows += stored
                print(f"  [{d.isoformat()}] stored {stored} contracts", flush=True)
            completed.add(d.isoformat())
            done_count += 1
            if done_count % 10 == 0:
                save_checkpoint(completed, {"symbol": symbol, "rows": total_rows})
                await update_job(job_id, done_count, failed_days)
        except KeyboardInterrupt:
            print("\nInterrupted — progress saved. Re-run with --resume")
            save_checkpoint(completed, {"symbol": symbol, "rows": total_rows})
            await update_job(job_id, done_count, failed_days, status="paused")
            return
        except Exception as exc:
            failed_days.append(d.isoformat())
            print(f"  [{d.isoformat()}] error: {exc}")

    save_checkpoint(completed, {"symbol": symbol, "rows": total_rows})
    await update_job(
        job_id,
        done_count,
        failed_days,
        status="completed" if not failed_days else "completed_with_errors",
    )
    print(f"\nDone. {total_rows:,} option rows stored for {symbol} ({done_count} days processed).", flush=True)
    if failed_days:
        print(f"Skipped/failed days: {len(failed_days)} (weekends/holidays/NSE gaps)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest NIFTY F&O option chain history from NSE archives")
    parser.add_argument("--symbol", default="NIFTY", help="Index symbol (default: NIFTY)")
    parser.add_argument("--years", type=float, default=5.0, help="Years of history (default: 5)")
    parser.add_argument("--days", type=int, default=None, help="Override: ingest last N calendar days only")
    parser.add_argument("--resume", action="store_true", help="Skip dates already in checkpoint")
    parser.add_argument("--pause", type=float, default=0.35, help="Seconds between NSE requests")
    args = parser.parse_args()
    asyncio.run(
        run_ingest(
            symbol=args.symbol.upper(),
            years=args.years,
            days=args.days,
            resume=args.resume,
            pause_sec=args.pause,
        )
    )


if __name__ == "__main__":
    main()
