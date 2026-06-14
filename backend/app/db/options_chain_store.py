"""Query helpers for historical options_chain TimescaleDB data."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import text

from .session import async_session, is_db_available


async def get_chain_status(symbol: str = "NIFTY") -> dict:
    if not is_db_available():
        return {"available": False, "symbol": symbol, "rows": 0}
    async with async_session() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(1) AS rows,
                           MIN(time::date) AS from_date,
                           MAX(time::date) AS to_date,
                           COUNT(DISTINCT time::date) AS trading_days
                    FROM options_chain
                    WHERE symbol = :symbol
                    """
                ),
                {"symbol": symbol.upper()},
            )
        ).mappings().first()
    if not row or not row["rows"]:
        return {"available": False, "symbol": symbol, "rows": 0}
    return {
        "available": True,
        "symbol": symbol.upper(),
        "rows": int(row["rows"]),
        "from_date": str(row["from_date"]),
        "to_date": str(row["to_date"]),
        "trading_days": int(row["trading_days"]),
    }


async def get_expiries_on_date(symbol: str, on_date: date) -> list[str]:
    if not is_db_available():
        return []
    async with async_session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT DISTINCT expiry::text
                    FROM options_chain
                    WHERE symbol = :symbol AND time::date = :on_date
                    ORDER BY expiry
                    """
                ),
                {"symbol": symbol.upper(), "on_date": on_date},
            )
        ).scalars().all()
    return list(rows)


async def fetch_chain_series(
    symbol: str,
    start: date,
    end: date,
    strike: float | None,
    option_type: str,
    expiry: date | None = None,
    expiry_mode: str = "nearest_weekly",
    strike_spec: str | None = None,
) -> list[dict]:
    """Daily option OHLCV + OI from stored chain snapshots."""
    if not is_db_available():
        return []

    option_type = option_type.upper()
    use_dynamic = strike_spec and str(strike_spec).upper() != str(strike or "")
    if strike_spec and strike_spec.upper() not in ("ATM", "OTM", "ITM") and not str(strike_spec).startswith(("OTM", "ITM")):
        try:
            strike = float(strike_spec)
            use_dynamic = False
        except ValueError:
            use_dynamic = True

    if use_dynamic or strike is None:
        return await _fetch_dynamic_series(
            symbol, start, end, option_type, strike_spec or "ATM", expiry, expiry_mode
        )

    async with async_session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT time::date AS trade_date,
                           expiry::date AS expiry,
                           strike,
                           option_type,
                           ltp,
                           oi,
                           volume,
                           greeks_json
                    FROM options_chain
                    WHERE symbol = :symbol
                      AND time::date BETWEEN :start AND :end
                      AND option_type = :option_type
                      AND strike = :strike
                      AND (:expiry IS NULL OR expiry = :expiry)
                    ORDER BY time, expiry
                    """
                ),
                {
                    "symbol": symbol.upper(),
                    "start": start,
                    "end": end,
                    "option_type": option_type,
                    "strike": float(strike),
                    "expiry": expiry,
                },
            )
        ).mappings().all()

    if not rows:
        return []

    by_date: dict[date, list[dict]] = {}
    for r in rows:
        d = r["trade_date"]
        by_date.setdefault(d, []).append(dict(r))

    return _build_series_from_groups(by_date, expiry, expiry_mode)


async def _fetch_dynamic_series(
    symbol: str,
    start: date,
    end: date,
    option_type: str,
    strike_spec: str,
    expiry: date | None,
    expiry_mode: str,
) -> list[dict]:
    async with async_session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT time::date AS trade_date,
                           expiry::date AS expiry,
                           strike,
                           option_type,
                           ltp,
                           oi,
                           volume,
                           greeks_json
                    FROM options_chain
                    WHERE symbol = :symbol
                      AND time::date BETWEEN :start AND :end
                      AND option_type = :option_type
                    ORDER BY time, expiry, strike
                    """
                ),
                {
                    "symbol": symbol.upper(),
                    "start": start,
                    "end": end,
                    "option_type": option_type,
                },
            )
        ).mappings().all()

    by_date: dict[date, list[dict]] = {}
    for r in rows:
        d = r["trade_date"]
        by_date.setdefault(d, []).append(dict(r))

    interval = {"NIFTY": 50, "BANKNIFTY": 100, "FINNIFTY": 50}.get(symbol.upper(), 50)
    filtered: dict[date, list[dict]] = {}
    for d, legs in by_date.items():
        und = _underlying_from_legs(legs)
        if und is None:
            continue
        target = _resolve_strike_value(und, strike_spec, interval)
        day_legs = [l for l in legs if abs(float(l["strike"]) - target) < 0.01]
        if day_legs:
            filtered[d] = day_legs

    return _build_series_from_groups(filtered, expiry, expiry_mode)


def _build_series_from_groups(
    by_date: dict[date, list[dict]],
    expiry: date | None,
    expiry_mode: str,
) -> list[dict]:
    series: list[dict] = []
    for d in sorted(by_date):
        legs = by_date[d]
        pick = _pick_expiry(legs, d, expiry, expiry_mode)
        if not pick:
            continue
        gj = pick.get("greeks_json") or {}
        if isinstance(gj, str):
            import json
            try:
                gj = json.loads(gj)
            except Exception:
                gj = {}
        series.append(
            {
                "date": str(d),
                "expiry": str(pick["expiry"]),
                "strike": float(pick["strike"]),
                "option_type": pick["option_type"],
                "ltp": float(pick["ltp"] or 0),
                "oi": int(pick["oi"] or 0),
                "volume": int(pick["volume"] or 0),
                "open": _f(gj.get("open")),
                "high": _f(gj.get("high")),
                "low": _f(gj.get("low")),
                "close": _f(gj.get("close")) or float(pick["ltp"] or 0),
                "underlying": _f(gj.get("underlying")),
            }
        )
    return series


def _underlying_from_legs(legs: list[dict]) -> float | None:
    for leg in legs:
        gj = leg.get("greeks_json") or {}
        if isinstance(gj, str):
            import json
            try:
                gj = json.loads(gj)
            except Exception:
                gj = {}
        u = _f(gj.get("underlying"))
        if u:
            return u
    return None


def _resolve_strike_value(underlying: float, strike_spec: str, interval: int) -> float:
    atm = round(underlying / interval) * interval
    spec = str(strike_spec).upper().strip()
    if spec == "ATM":
        return float(atm)
    if spec.startswith("OTM+"):
        return float(atm + int(spec.replace("OTM+", "")) * interval)
    if spec == "OTM":
        return float(atm + interval)
    if spec.startswith("ITM-"):
        return float(atm - int(spec.replace("ITM-", "")) * interval)
    if spec == "ITM":
        return float(atm - interval)
    try:
        return float(spec)
    except ValueError:
        return float(atm)


async def resolve_strike_from_chain(
    symbol: str,
    on_date: date,
    strike_spec: str,
    underlying: float | None = None,
) -> float | None:
    """Resolve ATM/OTM/ITM strike using chain underlying or OHLCV close."""
    interval = {"NIFTY": 50, "BANKNIFTY": 100, "FINNIFTY": 50}.get(symbol.upper(), 50)
    if underlying is None:
        underlying = await _underlying_on_date(symbol, on_date)
    if underlying is None:
        return None

    atm = round(underlying / interval) * interval
    spec = str(strike_spec).upper().strip()
    if spec == "ATM":
        return float(atm)
    if spec.startswith("OTM+"):
        return float(atm + int(spec.replace("OTM+", "")) * interval)
    if spec == "OTM":
        return float(atm + interval)
    if spec.startswith("ITM-"):
        return float(atm - int(spec.replace("ITM-", "")) * interval)
    if spec == "ITM":
        return float(atm - interval)
    try:
        return float(spec)
    except ValueError:
        return float(atm)


async def list_strikes_on_date(symbol: str, on_date: date, option_type: str = "CE") -> list[float]:
    if not is_db_available():
        return []
    async with async_session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT DISTINCT strike
                    FROM options_chain
                    WHERE symbol = :symbol AND time::date = :on_date AND option_type = :ot
                    ORDER BY strike
                    """
                ),
                {"symbol": symbol.upper(), "on_date": on_date, "ot": option_type.upper()},
            )
        ).scalars().all()
    return [float(x) for x in rows]


async def _underlying_on_date(symbol: str, on_date: date) -> float | None:
    async with async_session() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT (greeks_json->>'underlying')::float AS u
                    FROM options_chain
                    WHERE symbol = :symbol AND time::date = :on_date
                      AND greeks_json->>'underlying' IS NOT NULL
                    LIMIT 1
                    """
                ),
                {"symbol": symbol.upper(), "on_date": on_date},
            )
        ).scalar()
    return float(row) if row else None


def _f(val) -> float | None:
    try:
        if val is None:
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def _pick_expiry(legs: list[dict], trade_date: date, fixed_expiry: date | None, mode: str) -> dict | None:
    if not legs:
        return None
    if fixed_expiry:
        for leg in legs:
            if leg["expiry"] == fixed_expiry:
                return leg
        return None

    future = [l for l in legs if l["expiry"] >= trade_date]
    if not future:
        return None
    future.sort(key=lambda x: x["expiry"])

    if mode == "nearest_monthly":
        monthly = [l for l in future if _is_monthly_expiry(l["expiry"])]
        return monthly[0] if monthly else future[0]

    # nearest_weekly (default): closest expiry
    return future[0]


def _is_monthly_expiry(expiry: date) -> bool:
    """NIFTY monthly expiries are last Tuesday — approximate: expiry day >= 24."""
    return expiry.day >= 24
