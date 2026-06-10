"""
Quant AI Agent — Options Greeks Computation

Black-Scholes pricing, Greeks (Delta, Gamma, Theta, Vega, Rho),
Implied Volatility via Newton-Raphson, IV Surface construction,
and GEX (Gamma Exposure) / dealer positioning estimation.
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm


@dataclass
class GreeksResult:
    """Computed Greeks for a single option."""

    price: float        # Theoretical price
    delta: float
    gamma: float
    theta: float        # Per calendar day
    vega: float         # Per 1% change in IV
    rho: float

    def to_dict(self) -> dict:
        return {
            "price": round(self.price, 4),
            "delta": round(self.delta, 6),
            "gamma": round(self.gamma, 6),
            "theta": round(self.theta, 4),
            "vega": round(self.vega, 4),
            "rho": round(self.rho, 4),
        }


@dataclass
class IVSurfacePoint:
    """Single point on the IV surface."""

    strike: float
    expiry_days: int
    iv: float
    moneyness: float    # strike / spot


def _d1(S: float, K: float, r: float, sigma: float, T: float) -> float:
    """Calculate d1 in Black-Scholes formula."""
    if T <= 0 or sigma <= 0:
        return 0.0
    return (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))


def _d2(S: float, K: float, r: float, sigma: float, T: float) -> float:
    """Calculate d2 in Black-Scholes formula."""
    return _d1(S, K, r, sigma, T) - sigma * math.sqrt(T)


def black_scholes_price(
    S: float,          # Spot price
    K: float,          # Strike price
    r: float,          # Risk-free rate (annualized, e.g., 0.07 for 7%)
    sigma: float,      # Volatility (annualized, e.g., 0.15 for 15%)
    T: float,          # Time to expiry in years
    option_type: str,  # "CE" or "PE"
) -> float:
    """
    Calculate Black-Scholes option price.

    For Indian markets, r ≈ 0.065–0.075 (RBI repo rate vicinity).
    """
    if T <= 0:
        # At expiry: intrinsic value only
        if option_type.upper() == "CE":
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    d1_val = _d1(S, K, r, sigma, T)
    d2_val = _d2(S, K, r, sigma, T)

    if option_type.upper() == "CE":
        return S * norm.cdf(d1_val) - K * math.exp(-r * T) * norm.cdf(d2_val)
    else:
        return K * math.exp(-r * T) * norm.cdf(-d2_val) - S * norm.cdf(-d1_val)


def compute_greeks(
    S: float,
    K: float,
    r: float,
    sigma: float,
    T: float,
    option_type: str,
) -> GreeksResult:
    """
    Compute all Greeks for a European option using Black-Scholes.

    Returns: GreeksResult with price, delta, gamma, theta, vega, rho.
    """
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option_type.upper() == "CE" else max(K - S, 0)
        return GreeksResult(
            price=intrinsic,
            delta=1.0 if (option_type.upper() == "CE" and S > K) else (
                -1.0 if (option_type.upper() == "PE" and S < K) else 0.0
            ),
            gamma=0.0, theta=0.0, vega=0.0, rho=0.0,
        )

    d1_val = _d1(S, K, r, sigma, T)
    d2_val = _d2(S, K, r, sigma, T)
    sqrt_T = math.sqrt(T)
    exp_neg_rT = math.exp(-r * T)
    n_d1 = norm.pdf(d1_val)  # Standard normal PDF

    price = black_scholes_price(S, K, r, sigma, T, option_type)

    # Delta
    if option_type.upper() == "CE":
        delta = norm.cdf(d1_val)
    else:
        delta = norm.cdf(d1_val) - 1.0

    # Gamma (same for calls and puts)
    gamma = n_d1 / (S * sigma * sqrt_T)

    # Theta (per calendar day)
    common_theta = -(S * sigma * n_d1) / (2 * sqrt_T)
    if option_type.upper() == "CE":
        theta = (common_theta - r * K * exp_neg_rT * norm.cdf(d2_val)) / 365
    else:
        theta = (common_theta + r * K * exp_neg_rT * norm.cdf(-d2_val)) / 365

    # Vega (per 1% change in IV)
    vega = S * sqrt_T * n_d1 / 100

    # Rho
    if option_type.upper() == "CE":
        rho = K * T * exp_neg_rT * norm.cdf(d2_val) / 100
    else:
        rho = -K * T * exp_neg_rT * norm.cdf(-d2_val) / 100

    return GreeksResult(
        price=price,
        delta=delta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        rho=rho,
    )


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    r: float,
    T: float,
    option_type: str,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> float:
    """
    Calculate Implied Volatility using Newton-Raphson method.

    Returns IV as a decimal (e.g., 0.15 for 15%).
    Returns 0.0 if convergence fails.
    """
    if T <= 0 or market_price <= 0:
        return 0.0

    # Initial guess: use Brenner-Subrahmanyam approximation
    sigma = math.sqrt(2 * math.pi / T) * (market_price / S)
    sigma = max(0.01, min(sigma, 5.0))  # Clamp to reasonable range

    for _ in range(max_iterations):
        price = black_scholes_price(S, K, r, sigma, T, option_type)
        diff = price - market_price

        if abs(diff) < tolerance:
            return sigma

        # Vega for Newton-Raphson step
        d1_val = _d1(S, K, r, sigma, T)
        vega = S * math.sqrt(T) * norm.pdf(d1_val)

        if vega < 1e-10:
            break

        sigma -= diff / vega
        sigma = max(0.001, min(sigma, 10.0))  # Keep in bounds

    return sigma


def compute_iv_surface(
    contracts: list[dict],
    spot: float,
    r: float = 0.07,
) -> list[IVSurfacePoint]:
    """
    Construct an IV surface from option contracts.

    Each contract dict should have: strike, option_type, ltp, expiry_days, iv
    If IV is not provided, it's computed from the market price.

    Returns list of IVSurfacePoint for 3D surface plotting.
    """
    surface_points: list[IVSurfacePoint] = []

    for contract in contracts:
        strike = contract["strike"]
        expiry_days = contract.get("expiry_days", 7)
        T = expiry_days / 365.0
        option_type = contract.get("option_type", "CE")
        ltp = contract.get("ltp", 0)

        # Use provided IV or compute it
        iv = contract.get("iv", 0)
        if iv <= 0 and ltp > 0:
            iv = implied_volatility(ltp, spot, strike, r, T, option_type) * 100

        if iv > 0:
            surface_points.append(
                IVSurfacePoint(
                    strike=strike,
                    expiry_days=expiry_days,
                    iv=iv,
                    moneyness=strike / spot if spot > 0 else 0,
                )
            )

    return surface_points


def compute_gex(
    contracts: list[dict],
    spot: float,
    r: float = 0.07,
    lot_size: int = 50,
) -> dict:
    """
    Compute Gamma Exposure (GEX) profile.

    GEX estimates how much hedging pressure dealers exert on the market.
    Positive GEX at a strike → dealers are long gamma → price-stabilizing
    Negative GEX → dealers are short gamma → price-amplifying

    Returns:
        {
            "gex_by_strike": [{strike, gex, ce_gamma, pe_gamma, ce_oi, pe_oi}],
            "total_gex": float,
            "gex_flip_point": float,  # Strike where GEX flips from +ve to -ve
            "key_levels": {support, resistance, max_pain}
        }
    """
    gex_data: dict[float, dict] = {}

    for contract in contracts:
        strike = contract["strike"]
        oi = contract.get("open_interest", 0)
        option_type = contract.get("option_type", "CE")
        iv = contract.get("iv", 0) / 100  # Convert to decimal
        expiry_days = contract.get("expiry_days", 7)
        T = expiry_days / 365.0

        if iv <= 0 or T <= 0 or oi <= 0:
            continue

        # Compute gamma
        greeks = compute_greeks(spot, strike, r, iv, T, option_type)

        if strike not in gex_data:
            gex_data[strike] = {
                "strike": strike,
                "ce_gamma": 0.0,
                "pe_gamma": 0.0,
                "ce_oi": 0,
                "pe_oi": 0,
                "gex": 0.0,
            }

        # GEX = Gamma × OI × Spot² × lot_size × 0.01
        contract_gex = greeks.gamma * oi * spot * spot * lot_size * 0.01

        if option_type.upper() == "CE":
            gex_data[strike]["ce_gamma"] = greeks.gamma
            gex_data[strike]["ce_oi"] = oi
            gex_data[strike]["gex"] += contract_gex  # Positive for calls
        else:
            gex_data[strike]["pe_gamma"] = greeks.gamma
            gex_data[strike]["pe_oi"] = oi
            gex_data[strike]["gex"] -= contract_gex  # Negative for puts

    # Sort by strike
    gex_list = sorted(gex_data.values(), key=lambda x: x["strike"])

    # Compute total GEX
    total_gex = sum(g["gex"] for g in gex_list)

    # Find GEX flip point (where cumulative GEX changes sign)
    gex_flip = spot  # Default to spot
    prev_sign = None
    for g in gex_list:
        current_sign = 1 if g["gex"] >= 0 else -1
        if prev_sign is not None and current_sign != prev_sign:
            gex_flip = g["strike"]
            break
        prev_sign = current_sign

    # Key levels
    max_ce_oi_strike = max(gex_list, key=lambda x: x["ce_oi"])["strike"] if gex_list else spot
    max_pe_oi_strike = max(gex_list, key=lambda x: x["pe_oi"])["strike"] if gex_list else spot

    return {
        "gex_by_strike": gex_list,
        "total_gex": round(total_gex, 2),
        "gex_flip_point": gex_flip,
        "key_levels": {
            "resistance": max_ce_oi_strike,
            "support": max_pe_oi_strike,
            "gex_flip": gex_flip,
        },
    }
