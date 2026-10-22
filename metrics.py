import numpy as np
import pandas as pd
TRADING_DAYS = 252

def _max_drawdown(series: pd.Series) -> float:
    dd = series / series.cummax() - 1
    return float(dd.min())

def portfolio_metrics(nav: pd.Series, risk_free_rate: float = 0.0):
    returns = nav.pct_change(fill_method=None).dropna()
    cumulative = float(nav.iloc[-1] / nav.iloc[0] - 1)
    vol = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS))
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS) - 1
    excess = returns - daily_rf
    sharpe = float((excess.mean() * TRADING_DAYS) / vol) if vol > 0 else np.nan
    return {"cumulative_return": cumulative, "annualized_volatility": vol, "sharpe_ratio": sharpe, "max_drawdown": _max_drawdown(nav)}

def asset_metrics(prices: pd.DataFrame):
    returns = prices.pct_change(fill_method=None).dropna()
    rows = []
    for col in prices.columns:
        r = returns[col].dropna()
        s = prices[col].dropna()
        if len(s) < 2:
            continue
        cumulative = s.iloc[-1] / s.iloc[0] - 1
        years = max((s.index[-1] - s.index[0]).days / 365.25, 1 / 365.25)
        annual = (1 + cumulative) ** (1 / years) - 1
        vol = r.std(ddof=1) * np.sqrt(TRADING_DAYS)
        rows.append({"Ticker": col, "Annual return": annual, "Annual volatility": vol, "Max drawdown": _max_drawdown(s), "Cumulative return": cumulative})
    return pd.DataFrame(rows).set_index("Ticker")

def correlation_matrix(prices: pd.DataFrame):
    return prices.pct_change(fill_method=None).dropna().corr()
