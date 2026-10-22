# 🌱 Sustainable Portfolio Lab

Interactive sustainable-investing portfolio built with **Python + Streamlit + Plotly**.

## What it does
- Downloads real historical market prices at runtime.
- Builds a 5-ETF sustainable portfolio.
- Calculates cumulative return, annualized volatility, Sharpe ratio and max drawdown.
- Compares the portfolio with ACWI or SPY.
- Lets the user change weights with sliders.
- Shows correlation and drawdown interactively.
- Separates market performance from sustainability criteria.
- Documents official fund sources and key limitations.

## Portfolio universe
| Ticker | Role |
|---|---|
| ESGU | US ESG core |
| ESGD | Developed ex-US ESG diversification |
| ICLN | Global clean energy |
| TAN | Solar theme |
| BGRN | Green bonds |

### Default: Balanced Sustainable
- ESGU 35%
- ESGD 20%
- ICLN 15%
- TAN 10%
- BGRN 20%

Other presets: **Climate Tilt**, **Lower Volatility**, and **Custom**.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload all files in this folder.
3. Open Streamlit Community Cloud.
4. Choose **Create app**.
5. Select your repository.
6. Main file path: `app.py`.
7. Deploy.

## Suggested repository description
> Interactive sustainable portfolio construction tool combining historical market performance, risk metrics and documented ESG / climate-investing criteria.

## Academic framing
Do not present this as “the best sustainable portfolio.” Present it as a **transparent portfolio laboratory** that asks whether a sustainability thesis also makes sense from a diversification and risk perspective.

## Data
Historical market prices are downloaded at runtime with `yfinance`. Sustainability/product metadata is kept in `data/sustainability_metadata.csv` and links to official issuer pages.

## Disclaimer
Educational project only. Not investment advice. Historical performance does not guarantee future results.
