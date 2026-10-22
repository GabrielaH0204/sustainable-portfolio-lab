import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px

from src.market_data import download_prices
from src.portfolio import normalize_weights, portfolio_nav
from src.metrics import portfolio_metrics, asset_metrics, correlation_matrix

st.set_page_config(page_title="Sustainable Portfolio Lab", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.hero {padding:1.2rem 1.35rem;border:1px solid rgba(120,120,120,.20);border-radius:18px;background:linear-gradient(135deg,rgba(33,150,83,.12),rgba(46,204,113,.05));margin-bottom:1rem;}
.small-note {font-size:.88rem;opacity:.78;}
.chip {display:inline-block;padding:.2rem .55rem;margin:.12rem .18rem .12rem 0;border-radius:999px;border:1px solid rgba(120,120,120,.28);font-size:.78rem;}
div[data-testid='stMetric'] {border:1px solid rgba(120,120,120,.18);padding:.65rem .8rem;border-radius:14px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_metadata():
    return pd.read_csv("data/sustainability_metadata.csv")

meta = load_metadata()
tickers = meta["ticker"].tolist()

st.markdown("""
<div class='hero'>
<h1>🌱 Sustainable Portfolio Lab</h1>
<div>Build. Measure. Question the impact.</div>
<div class='small-note'>Interactive sustainable-investing portfolio using live market prices + documented fund criteria.</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("Portfolio settings")
preset = st.sidebar.selectbox("Strategy", ["Balanced Sustainable", "Climate Tilt", "Lower Volatility", "Custom"])

presets = {
    "Balanced Sustainable": {"ESGU":35,"ESGD":20,"ICLN":15,"TAN":10,"BGRN":20},
    "Climate Tilt": {"ESGU":25,"ESGD":10,"ICLN":25,"TAN":20,"BGRN":20},
    "Lower Volatility": {"ESGU":30,"ESGD":15,"ICLN":10,"TAN":5,"BGRN":40},
}

if preset == "Custom":
    st.sidebar.caption("Move the sliders. We normalize them automatically to 100%.")
    raw = {t: st.sidebar.slider(t, 0, 100, 20, 5) for t in tickers}
    weights = normalize_weights(raw)
else:
    weights = {k: v / 100 for k, v in presets[preset].items()}

st.sidebar.divider()
start_date = st.sidebar.date_input("Start date", value=date(2020,1,1), min_value=date(2016,1,1), max_value=date.today()-timedelta(days=5))
end_date = st.sidebar.date_input("End date", value=date.today(), min_value=start_date+timedelta(days=1), max_value=date.today())
benchmark = st.sidebar.selectbox("Benchmark", ["ACWI", "SPY"])
initial_investment = st.sidebar.number_input("Initial investment (USD)", min_value=1000, max_value=1_000_000, value=10_000, step=1000)
risk_free = st.sidebar.slider("Risk-free rate for Sharpe (%)", 0.0, 10.0, 0.0, 0.25) / 100
st.sidebar.caption("Prices: Yahoo Finance via yfinance. Sustainability metadata: official issuer pages.")

all_symbols = tickers + [benchmark]
try:
    prices = download_prices(all_symbols, str(start_date), str(end_date))
except Exception as e:
    st.error("Live market data could not be downloaded.")
    st.code(str(e))
    st.stop()

missing = [t for t in all_symbols if t not in prices.columns or prices[t].dropna().empty]
if missing:
    st.error(f"No usable price series returned for: {', '.join(missing)}")
    st.stop()

portfolio_prices = prices[tickers].dropna(how="any")
benchmark_prices = prices[benchmark].reindex(portfolio_prices.index).ffill().bfill()
if len(portfolio_prices) < 30:
    st.error("Not enough observations. Choose a wider date range.")
    st.stop()

nav = portfolio_nav(portfolio_prices, weights, initial_investment)
bench_nav = benchmark_prices / benchmark_prices.iloc[0] * initial_investment
metrics = portfolio_metrics(nav, risk_free_rate=risk_free)
assets = asset_metrics(portfolio_prices)
corr = correlation_matrix(portfolio_prices)

tabs = st.tabs(["Overview", "Performance", "Risk Lab", "Sustainability Lens", "Methodology"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portfolio return", f"{metrics['cumulative_return']:.1%}")
    c2.metric("Annualized volatility", f"{metrics['annualized_volatility']:.1%}")
    c3.metric("Sharpe ratio", f"{metrics['sharpe_ratio']:.2f}")
    c4.metric("Max drawdown", f"{metrics['max_drawdown']:.1%}")

    left, right = st.columns([1.45, 1])
    with left:
        perf_df = pd.DataFrame({"Portfolio": nav, benchmark: bench_nav}).reset_index()
        date_col = perf_df.columns[0]
        fig = px.line(perf_df, x=date_col, y=["Portfolio", benchmark], title=f"Growth of ${initial_investment:,.0f}", labels={"value":"Portfolio value (USD)", "variable":""})
        fig.update_layout(legend_orientation="h", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        alloc = pd.DataFrame({"Ticker": list(weights.keys()), "Weight": [v * 100 for v in weights.values()]})
        fig = px.pie(alloc, names="Ticker", values="Weight", hole=.56, title="Current allocation")
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Allocation")
    alloc_table = meta[["ticker", "fund_name", "role"]].copy()
    alloc_table["weight"] = alloc_table["ticker"].map(lambda x: weights[x])
    alloc_table["weight"] = alloc_table["weight"].map(lambda x: f"{x:.1%}")
    st.dataframe(alloc_table.rename(columns={"ticker":"Ticker", "fund_name":"Fund", "role":"Portfolio role", "weight":"Weight"}), hide_index=True, use_container_width=True)

with tabs[1]:
    st.subheader("Portfolio vs benchmark")
    st.caption("Historical results are backward-looking and do not predict future performance.")
    ret = portfolio_prices.pct_change(fill_method=None).dropna()
    growth = (1 + ret).cumprod() * 100
    growth = growth.reset_index()
    fig = px.line(growth, x=growth.columns[0], y=tickers, title="Growth of $100 by asset", labels={"value":"Value", "variable":"Ticker"})
    fig.update_layout(hovermode="x unified", legend_orientation="h")
    st.plotly_chart(fig, use_container_width=True)

    m1, m2 = st.columns(2)
    with m1:
        st.subheader("Asset metrics")
        show = assets.copy()
        for col in ["Annual return", "Annual volatility", "Max drawdown", "Cumulative return"]:
            show[col] = show[col].map(lambda x: f"{x:.1%}")
        st.dataframe(show, use_container_width=True)
    with m2:
        bar_df = assets.reset_index()
        fig = px.bar(bar_df, x="Ticker", y="Annual volatility", title="Annualized volatility by asset")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("Risk Lab")
    st.caption("Diversification matters because sustainable themes can still be highly concentrated.")
    fig = px.imshow(corr, text_auto=".2f", aspect="auto", zmin=-1, zmax=1, title="Return correlation matrix")
    st.plotly_chart(fig, use_container_width=True)
    dd = nav / nav.cummax() - 1
    fig = px.area(x=dd.index, y=dd.values, title="Portfolio drawdown", labels={"x":"Date", "y":"Drawdown"})
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
    st.info("A sustainability label does not eliminate market, sector, interest-rate, valuation, concentration or liquidity risk.")

with tabs[3]:
    st.subheader("Sustainability Lens")
    st.caption("Uses official fund objectives and screening information. It does not claim that holding an ETF directly causes the environmental outcomes described.")
    for _, row in meta.iterrows():
        with st.expander(f"{row['ticker']} — {row['fund_name']}"):
            a, b, c = st.columns(3)
            a.metric("Portfolio weight", f"{weights[row['ticker']]:.1%}")
            b.metric("Expense ratio", f"{row['expense_ratio']:.2%}")
            c.metric("Asset type", row["asset_type"])
            st.markdown(f"**Role:** {row['role']}")
            st.markdown(f"**Sustainability rationale:** {row['sustainability_rationale']}")
            st.markdown(f"**What to question:** {row['limitations']}")
            st.markdown(" ".join(f"<span class='chip'>ODS {x.strip()}</span>" for x in str(row["sdgs"]).split(",")), unsafe_allow_html=True)
            st.markdown(f"[Official fund source]({row['source_url']})")
    st.warning("ESG methodologies differ across providers. A fund can satisfy an ESG or thematic methodology while still holding companies that some investors may not personally consider sustainable.")

with tabs[4]:
    st.subheader("Methodology")
    st.markdown("""
**1. Asset selection.** Broad ESG equity + developed ex-US ESG + clean-energy themes + green bonds.

**2. Market data.** Adjusted historical market prices are requested at runtime from Yahoo Finance through `yfinance`.

**3. Return series.** Daily percentage returns are computed from downloaded prices.

**4. Portfolio calculation.** Buy-and-hold allocation at the selected starting weights; no transaction costs, taxes or periodic rebalancing.

**5. Metrics.** Cumulative return, annualized volatility, Sharpe ratio and maximum drawdown.

**6. Sustainability information.** Objectives, screens and expense ratios come from official issuer pages stored in `data/sustainability_metadata.csv`.

**7. Interpretation.** Educational analytical tool, not investment advice. Historical performance does not guarantee future results.
""")
    st.subheader("Current normalized weights")
    st.json({k: round(v, 4) for k, v in weights.items()})

st.caption(f"Market data window: {portfolio_prices.index.min().date()} → {portfolio_prices.index.max().date()} · Last observation: {portfolio_prices.index.max().date()}")
