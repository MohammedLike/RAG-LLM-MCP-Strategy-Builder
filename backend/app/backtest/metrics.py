import numpy as np
import pandas as pd

def calculate_metrics(returns: pd.Series, risk_free_rate: float = 0.0) -> dict:
    """
    Calculate performance metrics from a returns series.
    """
    if len(returns) == 0:
        return {}

    mean_return = returns.mean()
    std_return = returns.std()
    
    # Annualization factor (assuming daily returns)
    ann_factor = 252
    
    sharpe = ((mean_return - risk_free_rate) / std_return) * np.sqrt(ann_factor) if std_return > 0 else 0
    
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    sortino = ((mean_return - risk_free_rate) / downside_std) * np.sqrt(ann_factor) if downside_std > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    calmar = (mean_return * ann_factor) / abs(max_drawdown) if max_drawdown < 0 else 0
    
    return {
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_drawdown": float(max_drawdown),
        "calmar": float(calmar)
    }
