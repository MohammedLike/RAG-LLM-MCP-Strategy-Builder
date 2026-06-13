"""Parquet OHLCV store — multi-timeframe cache layer (1m, 5m, 15m, 1h, 1d)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from ..config import settings

SUPPORTED_RESOLUTIONS = ("1m", "5m", "15m", "1h", "1d")


def _root() -> Path:
    root = Path(settings.PARQUET_DATA_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def parquet_path(symbol: str, resolution: str) -> Path:
    clean = symbol.upper().replace("^", "").replace(".NS", "")
    return _root() / clean / f"{resolution}.parquet"


def write_ohlcv(symbol: str, resolution: str, df: pd.DataFrame) -> Path:
    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution {resolution}. Use one of {SUPPORTED_RESOLUTIONS}")
    if df.empty:
        raise ValueError("Cannot write empty OHLCV frame")

    path = parquet_path(symbol, resolution)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    if "time" in out.columns:
        out["time"] = pd.to_datetime(out["time"])
    out.to_parquet(path, index=False)
    return path


def read_ohlcv(
    symbol: str,
    resolution: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    path = parquet_path(symbol, resolution)
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_parquet(path)
    if "time" not in df.columns:
        return pd.DataFrame()

    df["time"] = pd.to_datetime(df["time"])
    if start is not None:
        df = df[df["time"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["time"] <= pd.Timestamp(end)]
    df.columns = [c.lower() for c in df.columns]
    return df.reset_index(drop=True)


def list_available(symbol: str | None = None) -> list[dict]:
    root = _root()
    items: list[dict] = []
    if not root.exists():
        return items

    symbols = [symbol.upper()] if symbol else [p.name for p in root.iterdir() if p.is_dir()]
    for sym in symbols:
        sym_dir = root / sym.replace("^", "").replace(".NS", "")
        if not sym_dir.is_dir():
            continue
        for res in SUPPORTED_RESOLUTIONS:
            path = sym_dir / f"{res}.parquet"
            if path.exists():
                try:
                    df = pd.read_parquet(path, columns=["time"])
                    items.append({
                        "symbol": sym,
                        "resolution": res,
                        "rows": len(df),
                        "start": str(df["time"].min())[:10] if len(df) else None,
                        "end": str(df["time"].max())[:10] if len(df) else None,
                        "path": str(path),
                    })
                except Exception:
                    items.append({"symbol": sym, "resolution": res, "rows": 0, "path": str(path)})
    return items
