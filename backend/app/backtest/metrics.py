import numpy as np
import pandas as pd

def calculate_metrics(returns: pd.Series, risk_free_rate: float = 0.065) -> dict:
    if len(returns) == 0:
        return {}

    mean_return = returns.mean()
    std_return = returns.std()
    ann_factor = 252

    sharpe = ((mean_return - risk_free_rate / ann_factor) / std_return) * np.sqrt(ann_factor) if std_return > 0 else 0

    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    sortino = ((mean_return - risk_free_rate / ann_factor) / downside_std) * np.sqrt(ann_factor) if downside_std > 0 else 0

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    total_return = float(cumulative.iloc[-1] - 1) if len(cumulative) > 0 else 0
    days = len(returns)
    years = max(days / ann_factor, 0.01)
    cagr = ((1 + total_return) ** (1 / years)) - 1

    calmar = cagr / abs(max_drawdown) if max_drawdown < 0 else 0

    ulcer_index = np.sqrt((drawdown ** 2).mean()) if len(drawdown) > 0 else 0

    downside_semivariance = (downside_returns ** 2).mean()
    sortino_annualized = (cagr - risk_free_rate) / np.sqrt(downside_semivariance * ann_factor) if downside_semivariance > 0 else 0

    return {
        "total_return": float(total_return * 100),
        "cagr": float(cagr * 100),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "sortino_annualized": float(sortino_annualized),
        "max_drawdown": float(max_drawdown * 100),
        "calmar": float(calmar),
        "ulcer_index": float(ulcer_index * 100),
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
    }
