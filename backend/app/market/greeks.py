from scipy.stats import norm
import numpy as np
import pandas as pd

def calculate_black_scholes_premium(S, K, T, r, sigma, option_type='CE'):
    """
    Calculate Black-Scholes Option Premium.
    """
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K) if option_type == 'CE' else max(0.0, K - S)

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'CE':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
    return price

def calculate_black_scholes_greeks(S, K, T, r, sigma, option_type='CE'):
    """
    Calculate Black-Scholes Greeks.
    S: Spot Price
    K: Strike Price
    T: Time to Expiry (in years)
    r: Risk-free rate (e.g., 0.05 for 5%)
    sigma: Implied Volatility
    option_type: 'CE' for Call, 'PE' for Put
    """
    if T <= 0 or sigma <= 0:
        return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'CE':
        delta = norm.cdf(d1)
        theta = (- (S * sigma * norm.pdf(d1)) / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        rho = (K * T * np.exp(-r * T) * norm.cdf(d2)) / 100
    else:
        delta = norm.cdf(d1) - 1
        theta = (- (S * sigma * norm.pdf(d1)) / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        rho = (-K * T * np.exp(-r * T) * norm.cdf(-d2)) / 100

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = (S * norm.pdf(d1) * np.sqrt(T)) / 100

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 4),
        "vega": round(vega, 4),
        "rho": round(rho, 4)
    }

def compute_option_price_series(underlying_series: pd.Series, strike: float, option_type: str, dte_series: pd.Series, r: float = 0.06, iv_series: pd.Series = None) -> pd.Series:
    """
    Computes a daily series of option premiums using Black-Scholes.
    """
    prices = []
    if iv_series is None:
        # Fallback to rolling 20-day historical volatility if no IV is provided
        returns = np.log(underlying_series / underlying_series.shift(1))
        iv_series = returns.rolling(window=20).std() * np.sqrt(252)
        iv_series = iv_series.bfill().fillna(0.20) # default 20% IV fallback

    for i in range(len(underlying_series)):
        S = underlying_series.iloc[i]
        T = max(dte_series.iloc[i] / 365.0, 0.0001) # Avoid division by zero
        sigma = max(iv_series.iloc[i], 0.01)
        p = calculate_black_scholes_premium(S, strike, T, r, sigma, option_type)
        prices.append(p)
        
    return pd.Series(prices, index=underlying_series.index)

def compute_greeks_series(underlying_series: pd.Series, strike: float, option_type: str, dte_series: pd.Series, r: float = 0.06, iv_series: pd.Series = None) -> pd.DataFrame:
    """
    Computes a daily dataframe of Greeks.
    """
    greeks_list = []
    if iv_series is None:
        returns = np.log(underlying_series / underlying_series.shift(1))
        iv_series = returns.rolling(window=20).std() * np.sqrt(252)
        iv_series = iv_series.bfill().fillna(0.20)

    for i in range(len(underlying_series)):
        S = underlying_series.iloc[i]
        T = max(dte_series.iloc[i] / 365.0, 0.0001)
        sigma = max(iv_series.iloc[i], 0.01)
        g = calculate_black_scholes_greeks(S, strike, T, r, sigma, option_type)
        greeks_list.append(g)
        
    return pd.DataFrame(greeks_list, index=underlying_series.index)

