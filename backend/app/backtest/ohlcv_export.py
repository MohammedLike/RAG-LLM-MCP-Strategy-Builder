"""Serialize OHLCV dataframe rows for TradingView Lightweight Charts."""

from __future__ import annotations

import pandas as pd


def serialize_ohlcv(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []

    rows: list[dict] = []
    for _, row in df.iterrows():
        time_val = row.get("time")
        if time_val is None:
            continue
        time_str = str(time_val)[:10]
        rows.append(
            {
                "time": time_str,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0) or 0),
            }
        )
    return rows
