import pandas as pd
import numpy as np

def normalize_weights(weight_dict):
    values = np.array(list(weight_dict.values()), dtype=float)
    total = values.sum()
    if total <= 0:
        raise ValueError("At least one portfolio weight must be greater than zero.")
    return dict(zip(weight_dict.keys(), values / total))

def portfolio_nav(prices: pd.DataFrame, weights: dict, initial_investment: float = 10_000):
    prices = prices[list(weights.keys())].dropna(how="any")
    if prices.empty:
        raise ValueError("No common price history is available for the selected assets.")
    w = pd.Series(weights, dtype=float).reindex(prices.columns)
    if abs(w.sum() - 1) > 1e-6:
        w = w / w.sum()
    normalized = prices / prices.iloc[0]
    nav = (normalized * w).sum(axis=1) * initial_investment
    nav.name = "Portfolio"
    return nav
