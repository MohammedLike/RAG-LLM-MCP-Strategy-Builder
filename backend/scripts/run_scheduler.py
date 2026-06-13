"""Background scheduler — daily OHLCV refresh every 24 hours."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.market.ohlcv_refresh import default_refresh_args, run_refresh


async def run_once() -> None:
    print(f"[*] Scheduler: daily OHLCV refresh at {datetime.now(timezone.utc).isoformat()}")
    summary = await run_refresh(default_refresh_args())
    print(f"[*] Scheduler done: {summary.get('new_bars', 0)} new bars, {summary.get('updated_symbols', 0)} symbols updated")


async def loop(interval_hours: float) -> None:
    await run_once()
    while True:
        print(f"[*] Scheduler: sleeping {interval_hours}h")
        await asyncio.sleep(interval_hours * 3600)
        await run_once()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval-hours", type=float, default=24.0)
    args = parser.parse_args()
    asyncio.run(run_once() if args.once else loop(args.interval_hours))


if __name__ == "__main__":
    main()
