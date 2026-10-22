import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly.express as px
import yfinance as yf

st.set_page_config(page_title='Sustainable Portfolio Lab', page_icon='🌱', layout='wide')

# -------------------- Styling --------------------
st.markdown('''
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {padding:1.15rem 1.25rem;border:1px solid rgba(120,120,120,.18);border-radius:18px;
background:linear-gradient(135deg,rgba(46,204,113,.14),rgba(52,152,219,.05));margin-bottom:1rem;}
.hero h1 {margin:0 0 .2rem 0;}
.small-note {font-size:.88rem;opacity:.75;}
.chip {display:inline-block;padding:.18rem .5rem;margin:.1rem .12rem .1rem 0;border-radius:999px;
border:1px solid rgba(120,120,120,.25);font-size:.78rem;}
div[data-testid='stMetric'] {border:1px solid rgba(120,120,120,.16);padding:.6rem .75rem;border-radius:14px;}
</style>
''', unsafe_allow_html=True)

# -------------------- Static fund metadata --------------------
META = pd.DataFrame([
    {
        'ticker':'ESGU','fund_name':'iShares ESG Aware MSCI USA ETF','asset_type':'Equity','role':'US ESG core',
        'expense_ratio':0.0015,'sdgs':'8,9,12,13',
        'sustainability_rationale':'Broad US large- and mid-cap exposure using an ESG-aware index and business-involvement screens.',
        'limitations':'ESG-aware is not the same as impact investing; methodology remains relative to a conventional parent universe.',
        'source_url':'https://www.ishares.com/us/products/286007/ishares-esg-aware-msci-usa-etf/'
    },
    {
        'ticker':'ESGD','fund_name':'iShares ESG Aware MSCI EAFE ETF','asset_type':'Equity','role':'Developed ex-US ESG diversification',
        'expense_ratio':0.0020,'sdgs':'8,9,12,13',
        'sustainability_rationale':'Developed-market equity exposure outside the US and Canada with ESG-aware screening.',
        'limitations':'ESG scores depend on provider methodology and the fund still carries equity, currency and regional risk.',
        'source_url':'https://www.ishares.com/us/products/283778/ishares-esg-aware-msci-eafe-etf'
    },
    {
        'ticker':'ICLN','fund_name':'iShares Global Clean Energy ETF','asset_type':'Equity','role':'Global clean-energy theme',
        'expense_ratio':0.0038,'sdgs':'7,9,11,13',
        'sustainability_rationale':'Global exposure to companies associated with clean-energy production and related technologies.',
        'limitations':'Clean-energy themes can be concentrated and volatile; supply chains can still create environmental and social impacts.',
        'source_url':'https://www.ishares.com/us/products/239738/ishares-global-clean-energy-etf/'
    },
    {
        'ticker':'TAN','fund_name':'Invesco Solar ETF','asset_type':'Equity','role':'Solar energy theme',
        'expense_ratio':0.0070,'sdgs':'7,9,11,13',
        'sustainability_rationale':'Focused exposure to companies in the global solar-energy industry.',
        'limitations':'High sector concentration can increase sensitivity to interest rates, policy, valuations and technology cycles.',
        'source_url':'https://www.invesco.com/us/en/financial-products/etfs/invesco-solar-etf.html'
    },
    {
        'ticker':'BGRN','fund_name':'iShares USD Green Bond ETF','asset_type':'Fixed income','role':'Green-bond stabilizer',
        'expense_ratio':0.0020,'sdgs':'6,7,9,11,13',
        'sustainability_rationale':'Investment-grade USD green bonds whose proceeds are designated for environmental projects.',
        'limitations':'Green labels do not remove credit, duration or interest-rate risk and do not guarantee perfect environmental additionality.',
        'source_url':'https://www.ishares.com/us/products/305296/ishares-usd-green-bond-etf'
    },
])
TICKERS = META['ticker'].tolist()

# -------------------- Portfolio utilities --------------------
def normalize_weights(weight_dict):
    values = np.array(list(weight_dict.values()), dtype=float)
    total = values.sum()
    if total <= 0:
        raise ValueError('At least one portfolio weight must be greater than zero.')
    return dict(zip(weight_dict.keys(), values / total))

@st.cache_data(ttl=3600, show_spinner=False)
def download_prices(tickers, start, end):
    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by='column',
        threads=True,
    )
    if raw is None or raw.empty:
        raise ValueError('Yahoo Finance returned an empty dataset.')
    if isinstance(raw.columns, pd.MultiIndex):
        if 'Close' not in raw.columns.get_level_values(0):
            raise ValueError('Downloaded data does not contain Close prices.')
        prices = raw['Close'].copy()
    else:
        if 'Close' not in raw.columns:
            raise ValueError('Downloaded data does not contain Close prices.')
        prices = raw[['Close']].copy()
        prices.columns = [tickers[0] if isinstance(tickers, list) else tickers]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    prices = prices.sort_index().dropna(how='all')
    prices.index.name = 'Date'
    return prices

def portfolio_nav(prices, weights, initial_investment=10000):
    prices = prices[list(weights.keys())].dropna(how='any')
    if prices.empty:
        raise ValueError('No common price history is available for the selected assets.')
    w = pd.Series(weights, dtype=float).reindex(prices.columns)
    w = w / w.sum()
    normalized = prices / prices.iloc[0]
    nav = (normalized * w).sum(axis=1) * initial_investment
    nav.name = 'Portfolio'
    return nav

def max_drawdown(series):
    dd = series / series.cummax() - 1
    return float(dd.min())

def portfolio_metrics(nav, risk_free_rate=0.0):
    returns = nav.pct_change(fill_method=None).dropna()
    cumulative_return = float(nav.iloc[-1] / nav.iloc[0] - 1)
    annualized_volatility = float(returns.std(ddof=1) * np.sqrt(252))
    daily_rf = (1 + risk_free_rate) ** (1/252) - 1
    excess = returns - daily_rf
    sharpe = float((excess.mean() * 252) / annualized_volatility) if annualized_volatility > 0 else np.nan
    return {
        'cumulative_return': cumulative_return,
        'annualized_volatility': annualized_volatility,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown(nav),
    }

def asset_metrics(prices):
    rows = []
    for col in prices.columns:
        s = prices[col].dropna()
        r = s.pct_change(fill_method=None).dropna()
        if len(s) < 2:
            continue
        cumulative = s.iloc[-1] / s.iloc[0] - 1
        years = max((s.index[-1] - s.index[0]).days / 365.25, 1/365.25)
        annual_return = (1 + cumulative) ** (1/years) - 1
        annual_vol = r.std(ddof=1) * np.sqrt(252)
        rows.append({
            'Ticker': col,
            'Annual return': annual_return,
            'Annual volatility': annual_vol,
            'Max drawdown': max_drawdown(s),
            'Cumulative return': cumulative,
        })
    return pd.DataFrame(rows).set_index('Ticker')

# -------------------- Header --------------------
st.markdown('''
<div class="hero">
  <h1>🌱 Sustainable Portfolio Lab</h1>
  <div>Build. Measure. Question the impact.</div>
  <div class="small-note">Interactive sustainable-investing portfolio using live market prices and documented fund criteria.</div>
</div>
''', unsafe_allow_html=True)

# -------------------- Sidebar --------------------
st.sidebar.header('Portfolio settings')

presets = {
    'Balanced Sustainable': {'ESGU':35,'ESGD':20,'ICLN':15,'TAN':10,'BGRN':20},
    'Climate Tilt': {'ESGU':25,'ESGD':10,'ICLN':25,'TAN':20,'BGRN':20},
    'Lower Volatility': {'ESGU':30,'ESGD':15,'ICLN':10,'TAN':5,'BGRN':40},
}
preset = st.sidebar.selectbox('Strategy', list(presets.keys()) + ['Custom'])

if preset == 'Custom':
    st.sidebar.caption('Move the sliders. The app normalizes them automatically to 100%.')
    raw = {t: st.sidebar.slider(t, 0, 100, 20, 5) for t in TICKERS}
    weights = normalize_weights(raw)
else:
    weights = {k:v/100 for k,v in presets[preset].items()}

st.sidebar.divider()
start_date = st.sidebar.date_input('Start date', value=date(2020,1,1), min_value=date(2016,1,1), max_value=date.today()-timedelta(days=5))
end_date = st.sidebar.date_input('End date', value=date.today(), min_value=start_date+timedelta(days=1), max_value=date.today())
benchmark = st.sidebar.selectbox('Benchmark', ['ACWI','SPY'])
initial_investment = st.sidebar.number_input('Initial investment (USD)', 1000, 1000000, 10000, 1000)
risk_free = st.sidebar.slider('Risk-free rate for Sharpe (%)', 0.0, 10.0, 0.0, 0.25)/100

# -------------------- Data --------------------
with st.spinner('Loading market data…'):
    try:
        prices = download_prices(TICKERS + [benchmark], str(start_date), str(end_date + timedelta(days=1)))
    except Exception as e:
        st.error('Market data could not be downloaded.')
        st.code(str(e))
        st.stop()

missing = [t for t in TICKERS + [benchmark] if t not in prices.columns or prices[t].dropna().empty]
if missing:
    st.error('No usable price series returned for: ' + ', '.join(missing))
    st.stop()

portfolio_prices = prices[TICKERS].dropna(how='any')
benchmark_prices = prices[benchmark].reindex(portfolio_prices.index).ffill().bfill()
if len(portfolio_prices) < 30:
    st.error('Not enough observations. Choose a wider date range.')
    st.stop()

nav = portfolio_nav(portfolio_prices, weights, initial_investment)
bench_nav = benchmark_prices / benchmark_prices.iloc[0] * initial_investment
metrics = portfolio_metrics(nav, risk_free)
assets = asset_metrics(portfolio_prices)
corr = portfolio_prices.pct_change(fill_method=None).dropna().corr()

# -------------------- Tabs --------------------
tabs = st.tabs(['Overview','Performance','Risk Lab','Sustainability Lens','Methodology'])

with tabs[0]:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Portfolio return', f"{metrics['cumulative_return']:.1%}")
    c2.metric('Annualized volatility', f"{metrics['annualized_volatility']:.1%}")
    c3.metric('Sharpe ratio', f"{metrics['sharpe_ratio']:.2f}")
    c4.metric('Max drawdown', f"{metrics['max_drawdown']:.1%}")

    left,right = st.columns([1.45,1])
    with left:
        perf_df = pd.DataFrame({'Portfolio':nav, benchmark:bench_nav}).reset_index()
        fig = px.line(perf_df, x='Date', y=['Portfolio',benchmark], title=f'Growth of ${initial_investment:,.0f}', labels={'value':'Portfolio value (USD)','variable':''})
        fig.update_layout(legend_orientation='h', hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    with right:
        alloc = pd.DataFrame({'Ticker':list(weights.keys()), 'Weight':[v*100 for v in weights.values()]})
        fig = px.pie(alloc, names='Ticker', values='Weight', hole=.56, title='Current allocation')
        fig.update_traces(textinfo='label+percent')
        st.plotly_chart(fig, use_container_width=True)

    table = META[['ticker','fund_name','role']].copy()
    table['Weight'] = table['ticker'].map(lambda x: f"{weights[x]:.1%}")
    table.columns = ['Ticker','Fund','Portfolio role','Weight']
    st.dataframe(table, hide_index=True, use_container_width=True)

with tabs[1]:
    st.subheader('Performance')
    ret = portfolio_prices.pct_change(fill_method=None).dropna()
    growth = ((1+ret).cumprod()*100).reset_index()
    fig = px.line(growth, x='Date', y=TICKERS, title='Growth of $100 by asset', labels={'value':'Value','variable':'Ticker'})
    fig.update_layout(hovermode='x unified', legend_orientation='h')
    st.plotly_chart(fig, use_container_width=True)

    show = assets.copy()
    for col in ['Annual return','Annual volatility','Max drawdown','Cumulative return']:
        show[col] = show[col].map(lambda x: f'{x:.1%}')
    st.dataframe(show, use_container_width=True)

with tabs[2]:
    st.subheader('Risk Lab')
    fig = px.imshow(corr, text_auto='.2f', aspect='auto', zmin=-1, zmax=1, title='Return correlation matrix')
    st.plotly_chart(fig, use_container_width=True)
    dd = nav/nav.cummax()-1
    fig = px.area(x=dd.index, y=dd.values, title='Portfolio drawdown', labels={'x':'Date','y':'Drawdown'})
    fig.update_yaxes(tickformat='.0%')
    st.plotly_chart(fig, use_container_width=True)
    st.info('A sustainability label does not eliminate market, sector, interest-rate, valuation, concentration or liquidity risk.')

with tabs[3]:
    st.subheader('Sustainability Lens')
    st.caption('Fund objectives and screening information are documented by the issuers. This app does not claim that holding an ETF directly causes the environmental outcomes described.')
    for _,row in META.iterrows():
        with st.expander(f"{row['ticker']} — {row['fund_name']}"):
            a,b,c = st.columns(3)
            a.metric('Portfolio weight', f"{weights[row['ticker']]:.1%}")
            b.metric('Expense ratio', f"{row['expense_ratio']:.2%}")
            c.metric('Asset type', row['asset_type'])
            st.markdown(f"**Role:** {row['role']}")
            st.markdown(f"**Sustainability rationale:** {row['sustainability_rationale']}")
            st.markdown(f"**What to question:** {row['limitations']}")
            st.markdown(' '.join(f"<span class='chip'>ODS {x.strip()}</span>" for x in str(row['sdgs']).split(',')), unsafe_allow_html=True)
            st.markdown(f"[Official fund source]({row['source_url']})")
    st.warning('ESG methodologies differ across providers. A fund may satisfy an ESG or thematic methodology while still holding companies some investors would not personally consider sustainable.')

with tabs[4]:
    st.subheader('Methodology')
    st.markdown('''
**Asset selection.** Five ETFs combine broad ESG equity, developed-market ESG diversification, clean energy, solar and green bonds.

**Market data.** Adjusted historical prices are downloaded with `yfinance` from Yahoo Finance.

**Portfolio model.** Buy-and-hold allocation at the selected starting weights. The app does not simulate taxes, transaction costs, bid/ask spreads or periodic rebalancing.

**Metrics.**
- Cumulative return: total change in portfolio value.
- Annualized volatility: daily return standard deviation × √252.
- Sharpe ratio: annualized excess return divided by annualized volatility.
- Maximum drawdown: largest peak-to-trough decline.

**Sustainability information.** Fund objectives, screens and expense ratios come from official issuer sources.

**Interpretation.** Educational analytical tool only. Historical performance does not guarantee future results.
''')
    st.subheader('Current normalized weights')
    st.json({k:round(v,4) for k,v in weights.items()})

st.caption(f"Market data window: {portfolio_prices.index.min().date()} → {portfolio_prices.index.max().date()} · Last observation: {portfolio_prices.index.max().date()}")
