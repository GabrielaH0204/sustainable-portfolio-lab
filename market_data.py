import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def download_prices(tickers, start, end):
    raw = yf.download(tickers=tickers, start=start, end=end, auto_adjust=True, progress=False, group_by="column", threads=True)
    if raw is None or raw.empty:
        raise ValueError("Yahoo Finance returned an empty dataset.")
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            raise ValueError("Downloaded data does not contain a Close field.")
        prices = raw["Close"].copy()
    else:
        if "Close" not in raw.columns:
            raise ValueError("Downloaded data does not contain a Close field.")
        prices = raw[["Close"]].copy()
        prices.columns = [tickers[0] if isinstance(tickers, list) else tickers]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    prices = prices.sort_index().dropna(how="all")
    prices.index.name = "Date"
    return prices
