"""Download and parse NSE F&O bhavcopy files for index options (NIFTY/BANKNIFTY).

Free public sources (no API key):
- Legacy format (until 2024-07-07): archives.nseindia.com historical DERIVATIVES zip
- UDiFF format (from 2024-07-08): nsearchives.nseindia.com BhavCopy_NSE_FO_*.zip
"""

from __future__ import annotations

import io
import logging
import time
import zipfile
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

UDIFF_CUTOFF = date(2024, 7, 8)
LEGACY_ARCHIVE = "https://archives.nseindia.com/content/historical/DERIVATIVES"
UDIFF_ARCHIVE = "https://nsearchives.nseindia.com/content/fo"

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


def trading_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    s.get("https://www.nseindia.com", timeout=15)
    return s


def legacy_bhavcopy_url(d: date) -> str:
    folder = f"{LEGACY_ARCHIVE}/{d.year}/{d.strftime('%b').upper()}"
    fname = f"fo{d.strftime('%d%b%Y').upper()}bhav.csv.zip"
    return f"{folder}/{fname}"


def udiff_bhavcopy_url(d: date) -> str:
    ds = d.strftime("%Y%m%d")
    return f"{UDIFF_ARCHIVE}/BhavCopy_NSE_FO_0_0_0_{ds}_F_0000.csv.zip"


def download_bhavcopy_zip(session: requests.Session, d: date, timeout: int = 45) -> bytes | None:
    url = udiff_bhavcopy_url(d) if d >= UDIFF_CUTOFF else legacy_bhavcopy_url(d)
    try:
        res = session.get(url, timeout=timeout)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        return res.content
    except requests.RequestException as exc:
        logger.debug("Bhavcopy download failed for %s: %s", d.isoformat(), exc)
        return None


def _read_zip_csv(payload: bytes) -> pd.DataFrame | None:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            name = next((n for n in zf.namelist() if n.lower().endswith(".csv")), None)
            if not name:
                return None
            return pd.read_csv(zf.open(name))
    except (zipfile.BadZipFile, ValueError, KeyError) as exc:
        logger.debug("Bhavcopy zip parse failed: %s", exc)
        return None


def _safe_float(val: Any) -> float | None:
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> int | None:
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _parse_expiry(val: Any) -> date | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    text = str(val).strip()
    try:
        if "-" in text and len(text.split("-")[0]) == 4:
            return pd.to_datetime(text, format="%Y-%m-%d").date()
        return pd.to_datetime(text, dayfirst=True).date()
    except Exception:
        return None


def parse_legacy_nifty_options(df: pd.DataFrame, symbol: str = "NIFTY", as_of: date | None = None) -> list[dict]:
    if df is None or df.empty:
        return []
    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]
    mask = (work["SYMBOL"] == symbol) & (work["INSTRUMENT"] == "OPTIDX")
    rows = work.loc[mask]
    if rows.empty:
        return []

    snap_time = datetime.combine(as_of or date.today(), datetime.min.time())
    out: list[dict] = []
    for _, row in rows.iterrows():
        expiry = _parse_expiry(row.get("EXPIRY_DT"))
        opt_type = str(row.get("OPTION_TYP", "")).strip().upper()
        strike = _safe_float(row.get("STRIKE_PR"))
        if not expiry or opt_type not in ("CE", "PE") or strike is None:
            continue
        out.append(
            {
                "time": snap_time,
                "symbol": symbol,
                "expiry": expiry,
                "strike": strike,
                "option_type": opt_type,
                "oi": _safe_int(row.get("OPEN_INT")),
                "volume": _safe_int(row.get("CONTRACTS")),
                "iv": None,
                "ltp": _safe_float(row.get("CLOSE")) or _safe_float(row.get("SETTLE_PR")),
                "greeks_json": {
                    "source": "nse_fo_bhavcopy_legacy",
                    "open": _safe_float(row.get("OPEN")),
                    "high": _safe_float(row.get("HIGH")),
                    "low": _safe_float(row.get("LOW")),
                    "close": _safe_float(row.get("CLOSE")),
                    "settle": _safe_float(row.get("SETTLE_PR")),
                    "chg_oi": _safe_int(row.get("CHG_IN_OI")),
                    "val_inlakh": _safe_float(row.get("VAL_INLAKH")),
                    "instrument": "OPTIDX",
                },
            }
        )
    return out


def parse_udiff_nifty_options(df: pd.DataFrame, symbol: str = "NIFTY", as_of: date | None = None) -> list[dict]:
    if df is None or df.empty:
        return []
    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]
    mask = (work["TckrSymb"] == symbol) & (work["FinInstrmTp"] == "IDO")
    rows = work.loc[mask]
    if rows.empty:
        return []

    snap_time = datetime.combine(as_of or date.today(), datetime.min.time())
    out: list[dict] = []
    for _, row in rows.iterrows():
        expiry = _parse_expiry(row.get("XpryDt") or row.get("FininstrmActlXpryDt"))
        opt_type = str(row.get("OptnTp", "")).strip().upper()
        strike = _safe_float(row.get("StrkPric"))
        if not expiry or opt_type not in ("CE", "PE") or strike is None:
            continue
        out.append(
            {
                "time": snap_time,
                "symbol": symbol,
                "expiry": expiry,
                "strike": strike,
                "option_type": opt_type,
                "oi": _safe_int(row.get("OpnIntrst")),
                "volume": _safe_int(row.get("TtlTradgVol")),
                "iv": None,
                "ltp": _safe_float(row.get("ClsPric")) or _safe_float(row.get("LastPric")) or _safe_float(row.get("SttlmPric")),
                "greeks_json": {
                    "source": "nse_fo_bhavcopy_udiff",
                    "open": _safe_float(row.get("OpnPric")),
                    "high": _safe_float(row.get("HghPric")),
                    "low": _safe_float(row.get("LwPric")),
                    "close": _safe_float(row.get("ClsPric")),
                    "last": _safe_float(row.get("LastPric")),
                    "settle": _safe_float(row.get("SttlmPric")),
                    "underlying": _safe_float(row.get("UndrlygPric")),
                    "chg_oi": _safe_int(row.get("ChngInOpnIntrst")),
                    "turnover": _safe_float(row.get("TtlTrfVal")),
                    "instrument": "IDO",
                    "name": row.get("FinInstrmNm"),
                },
            }
        )
    return out


def fetch_nifty_options_day(
    session: requests.Session,
    d: date,
    symbol: str = "NIFTY",
    pause_sec: float = 0.35,
) -> list[dict]:
    payload = download_bhavcopy_zip(session, d)
    if pause_sec:
        time.sleep(pause_sec)
    if not payload:
        return []
    df = _read_zip_csv(payload)
    if df is None:
        return []
    if d >= UDIFF_CUTOFF:
        return parse_udiff_nifty_options(df, symbol=symbol, as_of=d)
    return parse_legacy_nifty_options(df, symbol=symbol, as_of=d)
