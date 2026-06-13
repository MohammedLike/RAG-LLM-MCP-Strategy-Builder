"""Options strategy payoff and scenario analysis."""

from __future__ import annotations

import math
from typing import Any


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def black_scholes(
    spot: float,
    strike: float,
    tte_days: float,
    iv: float = 0.18,
    r: float = 0.065,
    option_type: str = "CE",
) -> float:
    t = max(tte_days / 365.0, 1 / 365.0)
    if spot <= 0 or strike <= 0:
        return 0.0
    d1 = (math.log(spot / strike) + (r + 0.5 * iv ** 2) * t) / (iv * math.sqrt(t))
    d2 = d1 - iv * math.sqrt(t)
    if option_type.upper() in ("CE", "CALL"):
        return spot * _norm_cdf(d1) - strike * math.exp(-r * t) * _norm_cdf(d2)
    return strike * math.exp(-r * t) * _norm_cdf(-d2) - spot * _norm_cdf(-d1)


def compute_payoff_curve(
    spot: float,
    strategy_spec: dict,
    price_range_pct: float = 0.15,
    steps: int = 41,
) -> dict[str, Any]:
    """
    Build expiry payoff curve for single-leg or straddle options strategies.
    """
    strike_label = strategy_spec.get("strike", "ATM")
    option_type = strategy_spec.get("option_type", "CE").upper()
    is_credit = bool(strategy_spec.get("is_credit", False))

    interval = 50 if spot > 10000 else (25 if spot > 5000 else 10)
    atm = round(spot / interval) * interval

    strike_map = {
        "ITM-2": atm - 2 * interval,
        "ITM-1": atm - interval,
        "ATM": atm,
        "OTM+1": atm + interval,
        "OTM+2": atm + 2 * interval,
    }
    strike = float(strategy_spec.get("strike_price") or strike_map.get(strike_label, atm))

    low = spot * (1 - price_range_pct)
    high = spot * (1 + price_range_pct)
    prices = [low + (high - low) * i / (steps - 1) for i in range(steps)]

    premium_ce = black_scholes(spot, strike, 7, option_type="CE")
    premium_pe = black_scholes(spot, strike, 7, option_type="PE")

    curve: list[dict] = []
    max_profit = float("-inf")
    max_loss = float("inf")
    breakevens: list[float] = []

    for p in prices:
        if option_type == "STRADDLE":
            ce_payoff = max(p - strike, 0) - premium_ce
            pe_payoff = max(strike - p, 0) - premium_pe
            payoff = ce_payoff + pe_payoff
            if is_credit:
                payoff = -(ce_payoff + pe_payoff)
        elif option_type in ("CE", "CALL"):
            payoff = max(p - strike, 0) - premium_ce
            if is_credit:
                payoff = premium_ce - max(p - strike, 0)
        else:
            payoff = max(strike - p, 0) - premium_pe
            if is_credit:
                payoff = premium_pe - max(strike - p, 0)

        curve.append({"spot": round(p, 2), "payoff": round(payoff, 2)})
        max_profit = max(max_profit, payoff)
        max_loss = min(max_loss, payoff)

    for i in range(1, len(curve)):
        if curve[i - 1]["payoff"] * curve[i]["payoff"] <= 0:
            breakevens.append(round((curve[i - 1]["spot"] + curve[i]["spot"]) / 2, 2))

    risk_reward = abs(max_profit / max_loss) if max_loss != 0 else 0

    return {
        "spot": spot,
        "strike": strike,
        "option_type": option_type,
        "is_credit": is_credit,
        "premium_ce": round(premium_ce, 2),
        "premium_pe": round(premium_pe, 2),
        "max_profit": round(max_profit, 2),
        "max_loss": round(max_loss, 2),
        "breakevens": breakevens[:4],
        "risk_reward": round(risk_reward, 2),
        "curve": curve,
    }
