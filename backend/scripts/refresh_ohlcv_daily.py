"""CLI wrapper for daily OHLCV refresh."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.market.ohlcv_refresh import default_refresh_args, run_refresh


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Append new daily OHLCV bars since last DB date")
    p.add_argument("--symbols", nargs="*", help="Refresh subset only")
    p.add_argument("--concurrency", type=int, default=12)
    p.add_argument("--batch-size", type=int, default=80)
    p.add_argument("--pause", type=float, default=0.8)
    p.add_argument("--max-symbols", type=int, default=0)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    summary = asyncio.run(run_refresh(args))
    print(
        f"[*] Refresh done — updated: {summary.get('updated_symbols')}, "
        f"skipped: {summary.get('skipped_symbols')}, new bars: {summary.get('new_bars')}"
    )
