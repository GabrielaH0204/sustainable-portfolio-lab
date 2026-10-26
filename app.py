import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Sustainable Portfolio Lab",
    page_icon="🌱",
    layout="wide"
)

CAPITAL = 100_000


# ---------------------------------------------------------
# ETF DATA
# ---------------------------------------------------------

ETF_INFO = {
    "ESGU": {
        "name": "iShares ESG Aware MSCI USA ETF",
        "description": "Empresas estadounidenses seleccionadas incorporando criterios ESG.",
        "why": "Aporta exposición diversificada a grandes y medianas empresas de EE. UU. bajo criterios ESG.",
        "problem": "Integra factores ambientales, sociales y de gobernanza en la selección de inversiones."
    },

    "ESGD": {
        "name": "iShares ESG Aware MSCI EAFE ETF",
        "description": "Empresas de mercados desarrollados fuera de EE. UU. y Canadá con criterios ESG.",
        "why": "Agrega diversificación internacional al portafolio sostenible.",
        "problem": "Reduce la concentración geográfica y amplía la inversión responsable a otros mercados."
    },

    "ICLN": {
        "name": "iShares Global Clean Energy ETF",
        "description": "Empresas globales relacionadas con energía limpia y transición energética.",
        "why": "Permite exposición a compañías vinculadas al crecimiento de energías limpias.",
        "problem": "Apoya la transición desde fuentes intensivas en carbono hacia energías más limpias."
    },

    "TAN": {
        "name": "Invesco Solar ETF",
        "description": "ETF enfocado específicamente en compañías de la industria solar.",
        "why": "Añade exposición directa a uno de los sectores clave de la transición energética.",
        "problem": "Contribuye al financiamiento de empresas relacionadas con generación de energía solar."
    },

    "BGRN": {
        "name": "iShares USD Green Bond ETF",
        "description": "ETF de bonos verdes investment-grade denominados en dólares.",
        "why": "Introduce renta fija y diversifica el portafolio frente a los ETFs de acciones.",
        "problem": "Canaliza capital hacia deuda destinada a proyectos con objetivos ambientales."
    }
}


# ---------------------------------------------------------
# STRATEGIES
# ---------------------------------------------------------

STRATEGIES = {
    "Balanced Sustainable": {
        "ESGU": 0.35,
        "ESGD": 0.20,
        "ICLN": 0.15,
        "TAN": 0.10,
        "BGRN": 0.20
    },

    "Climate Tilt": {
        "ESGU": 0.25,
        "ESGD": 0.10,
        "ICLN": 0.25,
        "TAN": 0.20,
        "BGRN": 0.20
    },

    "Lower Volatility": {
        "ESGU": 0.30,
        "ESGD": 0.15,
        "ICLN": 0.10,
        "TAN": 0.05,
        "BGRN": 0.40
    }
}


# ---------------------------------------------------------
# 5-YEAR RETURN
# ---------------------------------------------------------

@st.cache_data(ttl=3600)
def get_five_year_returns():

    tickers = list(ETF_INFO.keys())

    data = yf.download(
        tickers,
        period="5y",
        auto_adjust=True,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data[["Close"]]

    returns = {}

    for ticker in tickers:

        try:
            series = prices[ticker].dropna()

            start = series.iloc[0]
            end = series.iloc[-1]

            days = (
                series.index[-1]
                - series.index[0]
            ).days

            years = days / 365.25

            cagr = (
                (end / start) ** (1 / years)
                - 1
            )

            returns[ticker] = cagr

        except:
            returns[ticker] = np.nan

    return returns


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🌱 Sustainable Portfolio Lab")

st.write(
    "Portafolio sostenible de **USD 100,000** construido con "
    "5 ETFs y datos históricos reales."
)

st.caption(
    "Selecciona una estrategia y observa cómo cambia automáticamente "
    "la distribución del capital."
)


# ---------------------------------------------------------
# STRATEGY SELECTOR
# ---------------------------------------------------------

strategy = st.selectbox(
    "Estrategia del portafolio",
    list(STRATEGIES.keys())
)

weights = STRATEGIES[strategy]


# ---------------------------------------------------------
# STRATEGY DESCRIPTION
# ---------------------------------------------------------

if strategy == "Balanced Sustainable":

    st.info(
        "⚖️ Balanced Sustainable: busca equilibrio entre "
        "diversificación ESG, energía limpia y bonos verdes."
    )

elif strategy == "Climate Tilt":

    st.info(
        "🌍 Climate Tilt: aumenta la exposición a energía limpia "
        "y energía solar."
    )

elif strategy == "Lower Volatility":

    st.info(
        "🛡️ Lower Volatility: aumenta la participación de bonos verdes "
        "para reducir la concentración en renta variable."
    )


# ---------------------------------------------------------
# RETURNS
# ---------------------------------------------------------

five_year_returns = get_five_year_returns()


# ---------------------------------------------------------
# BUILD TABLE
# ---------------------------------------------------------

rows = []

for ticker, weight in weights.items():

    info = ETF_INFO[ticker]

    r = five_year_returns.get(
        ticker,
        np.nan
    )

    rows.append({
        "ETF": ticker,
        "Nombre": info["name"],
        "Descripción": info["description"],
        "Asignación": weight,
        "USD": CAPITAL * weight,
        "Rentabilidad anualizada 5 años": r,
        "¿Por qué?": info["why"],
        "¿Qué problema aborda?": info["problem"]
    })


df = pd.DataFrame(rows)


# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Capital",
    "USD 100,000"
)

col2.metric(
    "ETFs",
    "5"
)

col3.metric(
    "Asignación",
    f"{df['Asignación'].sum():.0%}"
)


# ---------------------------------------------------------
# TABLE
# ---------------------------------------------------------

st.subheader("Portafolio")

st.dataframe(
    df,
    hide_index=True,
    use_container_width=True,

    column_config={

        "Asignación":
            st.column_config.NumberColumn(
                "Asignación %",
                format="%.1f%%"
            ),

        "USD":
            st.column_config.NumberColumn(
                "USD $",
                format="$ %.0f"
            ),

        "Rentabilidad anualizada 5 años":
            st.column_config.NumberColumn(
                "Rentabilidad promedio 5 años*",
                format="%.2f%%"
            )
    }
)

st.caption(
    "*Rentabilidad histórica anualizada calculada mediante CAGR "
    "con aproximadamente cinco años de precios de mercado. "
    "No representa una rentabilidad futura garantizada."
)


# ---------------------------------------------------------
# ALLOCATION CHART
# ---------------------------------------------------------

st.subheader("Distribución del capital")

chart_df = df[
    [
        "ETF",
        "Asignación",
        "USD"
    ]
].copy()

chart_df["Asignación %"] = (
    chart_df["Asignación"]
    * 100
)

fig = px.pie(
    chart_df,
    names="ETF",
    values="Asignación %",
    hole=0.55
)

fig.update_traces(
    textinfo="label+percent"
)

fig.update_layout(
    showlegend=True,
    margin=dict(
        t=20,
        b=20,
        l=20,
        r=20
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------------------------------------------------------
# SHORT INTERPRETATION
# ---------------------------------------------------------

st.subheader("¿Qué busca esta estrategia?")

if strategy == "Balanced Sustainable":

    st.write(
        """
        Combinar diversificación tradicional con criterios de sostenibilidad.
        ESGU y ESGD forman el núcleo del portafolio, ICLN y TAN agregan
        exposición a la transición energética y BGRN incorpora renta fija verde.
        """
    )

elif strategy == "Climate Tilt":

    st.write(
        """
        Dar mayor peso a sectores vinculados con la transición energética.
        ICLN y TAN representan una mayor proporción del capital, aumentando
        tanto la exposición climática como el riesgo de concentración sectorial.
        """
    )

elif strategy == "Lower Volatility":

    st.write(
        """
        Mantener exposición sostenible reduciendo la dependencia exclusiva
        de acciones. El mayor peso de BGRN introduce bonos verdes y busca
        moderar la volatilidad del portafolio.
        """
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Datos históricos obtenidos mediante Yahoo Finance / yfinance. "
    "Proyecto académico — no constituye asesoría de inversión."
)
