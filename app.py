import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta
import plotly.express as px

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Sustainable Portfolio Lab",
    page_icon="🌱",
    layout="wide",
)

CAPITAL_USD = 100_000
TRADING_DAYS = 252


# ============================================================
# INFORMACIÓN DE LOS ETFs
# ============================================================

ETF_INFO = {
    "ESGU": {
        "name": "iShares ESG Aware MSCI USA ETF",
        "description": (
            "Acciones de EE. UU. seleccionadas mediante criterios "
            "ambientales, sociales y de gobierno corporativo (ESG)."
        ),
        "role": "Núcleo ESG de EE. UU.",
        "why": (
            "Aporta diversificación amplia en renta variable estadounidense "
            "incorporando criterios ESG, sin concentrar todo el portafolio "
            "en un único sector."
        ),
        "problem": (
            "Integra factores ambientales, sociales y de gobernanza "
            "en la asignación de capital hacia empresas cotizadas."
        ),
        "asset_type": "Renta variable",
        "expense_ratio": 0.0015,
        "sdgs": "8, 9, 12, 13",
        "limitations": (
            "ESG no equivale automáticamente a impacto positivo. "
            "La clasificación depende de la metodología del proveedor."
        ),
        "source": (
            "https://www.ishares.com/us/products/286007/"
            "ishares-esg-aware-msci-usa-etf"
        ),
    },

    "ESGD": {
        "name": "iShares ESG Aware MSCI EAFE ETF",
        "description": (
            "Acciones de mercados desarrollados fuera de EE. UU. "
            "y Canadá seleccionadas con criterios ESG."
        ),
        "role": "Diversificación internacional ESG",
        "why": (
            "Reduce la dependencia exclusiva del mercado estadounidense "
            "y agrega exposición internacional con criterios ESG."
        ),
        "problem": (
            "Amplía la inversión responsable hacia mercados desarrollados "
            "internacionales y reduce la concentración geográfica."
        ),
        "asset_type": "Renta variable",
        "expense_ratio": 0.0020,
        "sdgs": "8, 9, 12, 13",
        "limitations": (
            "Mantiene riesgo de mercado, divisas y diferencias regulatorias "
            "entre países."
        ),
        "source": (
            "https://www.ishares.com/us/literature/fact-sheet/"
            "esgd-ishares-esg-aware-msci-eafe-etf-fund-fact-sheet-en-us.pdf"
        ),
    },

    "ICLN": {
        "name": "iShares Global Clean Energy ETF",
        "description": (
            "Empresas globales relacionadas con energía limpia "
            "y transición energética."
        ),
        "role": "Energía limpia global",
        "why": (
            "Permite exposición directa a compañías relacionadas con "
            "el crecimiento de tecnologías de energía limpia."
        ),
        "problem": (
            "Canaliza capital hacia empresas vinculadas con la transición "
            "desde fuentes intensivas en carbono hacia energías más limpias."
        ),
        "asset_type": "Renta variable temática",
        "expense_ratio": 0.0038,
        "sdgs": "7, 9, 11, 13",
        "limitations": (
            "Al ser un ETF temático puede presentar mayor volatilidad "
            "y concentración sectorial."
        ),
        "source": (
            "https://www.ishares.com/us/products/239738/"
            "ishares-global-clean-energy-etf"
        ),
    },

    "TAN": {
        "name": "Invesco Solar ETF",
        "description": (
            "ETF temático enfocado en compañías pertenecientes "
            "a la industria de energía solar."
        ),
        "role": "Exposición al sector solar",
        "why": (
            "Agrega una apuesta temática específica dentro de la transición "
            "energética y complementa la exposición más amplia de ICLN."
        ),
        "problem": (
            "Apoya la expansión de tecnologías y compañías relacionadas "
            "con generación de energía solar."
        ),
        "asset_type": "Renta variable temática",
        "expense_ratio": 0.0070,
        "sdgs": "7, 9, 11, 13",
        "limitations": (
            "Su concentración en energía solar aumenta sensibilidad a tasas, "
            "regulación, ciclos tecnológicos y valuaciones."
        ),
        "source": (
            "https://www.invesco.com/us/en/financial-products/etfs/"
            "invesco-solar-etf.html"
        ),
    },

    "BGRN": {
        "name": "iShares USD Green Bond ETF",
        "description": (
            "Bonos verdes globales investment-grade denominados en USD."
        ),
        "role": "Renta fija verde",
        "why": (
            "Introduce renta fija para diversificar el riesgo del portafolio "
            "y exposición a deuda destinada a proyectos ambientales."
        ),
        "problem": (
            "Canaliza financiamiento hacia proyectos ambientales mediante "
            "bonos cuyo uso de recursos está vinculado a objetivos verdes."
        ),
        "asset_type": "Renta fija",
        "expense_ratio": 0.0020,
        "sdgs": "6, 7, 9, 11, 13",
        "limitations": (
            "Un bono verde sigue teniendo riesgo de crédito, duración y tasas. "
            "La etiqueta verde no garantiza impacto ambiental perfecto."
        ),
        "source": (
            "https://www.ishares.com/us/products/305296/BGRN"
        ),
    },
}


TICKERS = list(ETF_INFO.keys())


# ============================================================
# PORTAFOLIOS PREDEFINIDOS
# ============================================================

PRESETS = {
    "Balanced Sustainable": {
        "ESGU": 0.35,
        "ESGD": 0.20,
        "ICLN": 0.15,
        "TAN": 0.10,
        "BGRN": 0.20,
    },

    "Climate Tilt": {
        "ESGU": 0.25,
        "ESGD": 0.10,
        "ICLN": 0.25,
        "TAN": 0.20,
        "BGRN": 0.20,
    },

    "Lower Volatility": {
        "ESGU": 0.30,
        "ESGD": 0.15,
        "ICLN": 0.10,
        "TAN": 0.05,
        "BGRN": 0.40,
    },
}


# ============================================================
# DISEÑO
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.3rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    .hero {
        padding: 1.3rem 1.45rem;
        border: 1px solid rgba(120,120,120,.20);
        border-radius: 18px;
        background:
            linear-gradient(
                135deg,
                rgba(30,130,76,.14),
                rgba(46,204,113,.04)
            );
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin-bottom: .15rem;
    }

    .small-note {
        font-size: .88rem;
        opacity: .78;
    }

    .chip {
        display: inline-block;
        padding: .22rem .58rem;
        margin: .12rem .18rem .12rem 0;
        border-radius: 999px;
        border: 1px solid rgba(120,120,120,.28);
        font-size: .78rem;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(120,120,120,.18);
        padding: .65rem .8rem;
        border-radius: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES
# ============================================================

def normalize_weights(weight_dict):

    values = np.array(
        list(weight_dict.values()),
        dtype=float
    )

    total = values.sum()

    if total <= 0:
        equal = 1 / len(weight_dict)

        return {
            ticker: equal
            for ticker in weight_dict
        }

    normalized = values / total

    return dict(
        zip(
            weight_dict.keys(),
            normalized
        )
    )


def extract_close(raw, tickers):

    if raw is None or raw.empty:
        raise ValueError(
            "Yahoo Finance devolvió un dataset vacío."
        )

    if isinstance(raw.columns, pd.MultiIndex):

        first_level = raw.columns.get_level_values(0)

        if "Close" not in first_level:
            raise ValueError(
                "No se encontró el campo Close."
            )

        prices = raw["Close"].copy()

    else:

        if "Close" not in raw.columns:
            raise ValueError(
                "No se encontró el campo Close."
            )

        prices = raw[["Close"]].copy()

        if (
            isinstance(tickers, (list, tuple))
            and len(tickers) == 1
        ):
            prices.columns = [tickers[0]]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = (
        prices
        .sort_index()
        .dropna(how="all")
    )

    prices.index.name = "Date"

    return prices


@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def download_prices(
    tickers,
    start,
    end
):

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )

    return extract_close(
        raw,
        tickers
    )


@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def download_five_year_prices(tickers):

    raw = yf.download(
        tickers=tickers,
        period="5y",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )

    return extract_close(
        raw,
        tickers
    )


def five_year_cagr(series):

    series = series.dropna()

    if len(series) < 2:
        return np.nan

    days = (
        series.index[-1]
        - series.index[0]
    ).days

    years = days / 365.25

    if (
        years <= 0
        or series.iloc[0] <= 0
    ):
        return np.nan

    return (
        series.iloc[-1]
        / series.iloc[0]
    ) ** (1 / years) - 1


def portfolio_nav(
    prices,
    weights,
    initial_investment=CAPITAL_USD
):

    prices = (
        prices[
            list(weights.keys())
        ]
        .dropna(how="any")
    )

    if prices.empty:
        raise ValueError(
            "No hay suficiente historial común."
        )

    w = pd.Series(
        weights,
        dtype=float
    ).reindex(
        prices.columns
    )

    w = w / w.sum()

    normalized_prices = (
        prices
        / prices.iloc[0]
    )

    nav = (
        normalized_prices * w
    ).sum(axis=1) * initial_investment

    nav.name = "Portfolio"

    return nav


def max_drawdown(series):

    drawdown = (
        series
        / series.cummax()
        - 1
    )

    return float(
        drawdown.min()
    )


def portfolio_metrics(
    nav,
    risk_free_rate=0.0
):

    returns = (
        nav
        .pct_change(
            fill_method=None
        )
        .dropna()
    )

    cumulative_return = float(
        nav.iloc[-1]
        / nav.iloc[0]
        - 1
    )

    annualized_volatility = float(
        returns.std(ddof=1)
        * np.sqrt(TRADING_DAYS)
    )

    daily_rf = (
        (1 + risk_free_rate)
        ** (1 / TRADING_DAYS)
        - 1
    )

    excess_returns = (
        returns
        - daily_rf
    )

    if annualized_volatility > 0:

        sharpe = float(
            (
                excess_returns.mean()
                * TRADING_DAYS
            )
            / annualized_volatility
        )

    else:
        sharpe = np.nan

    return {
        "cumulative_return":
            cumulative_return,

        "annualized_volatility":
            annualized_volatility,

        "sharpe_ratio":
            sharpe,

        "max_drawdown":
            max_drawdown(nav),
    }


def asset_metrics(prices):

    returns = prices.pct_change(
        fill_method=None
    )

    rows = []

    for ticker in prices.columns:

        series = (
            prices[ticker]
            .dropna()
        )

        r = (
            returns[ticker]
            .dropna()
        )

        if len(series) < 2:
            continue

        cumulative = (
            series.iloc[-1]
            / series.iloc[0]
            - 1
        )

        days = (
            series.index[-1]
            - series.index[0]
        ).days

        years = max(
            days / 365.25,
            1 / 365.25
        )

        annual_return = (
            (1 + cumulative)
            ** (1 / years)
            - 1
        )

        annual_vol = (
            r.std(ddof=1)
            * np.sqrt(TRADING_DAYS)
        )

        rows.append(
            {
                "Ticker": ticker,

                "Rentabilidad anualizada":
                    annual_return,

                "Volatilidad anualizada":
                    annual_vol,

                "Max drawdown":
                    max_drawdown(series),

                "Rentabilidad acumulada":
                    cumulative,
            }
        )

    return (
        pd.DataFrame(rows)
        .set_index("Ticker")
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">

        <h1>🌱 Sustainable Portfolio Lab</h1>

        <div>
            <strong>
            USD 100,000 · 5 ETFs sostenibles ·
            datos reales de mercado
            </strong>
        </div>

        <div class="small-note">
            Construcción y análisis interactivo
            de un portafolio que combina
            desempeño financiero,
            diversificación y criterios
            de sostenibilidad.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "Construcción del portafolio"
)

strategy = st.sidebar.selectbox(
    "Estrategia",
    [
        "Balanced Sustainable",
        "Climate Tilt",
        "Lower Volatility",
        "Custom",
    ]
)


if strategy == "Custom":

    st.sidebar.caption(
        "Mueve los sliders. "
        "La app normaliza automáticamente "
        "los pesos para sumar 100%."
    )

    raw_weights = {}

    for ticker in TICKERS:

        raw_weights[ticker] = (
            st.sidebar.slider(
                ticker,
                min_value=0,
                max_value=100,
                value=20,
                step=5,
            )
        )

    weights = normalize_weights(
        raw_weights
    )

else:

    weights = PRESETS[strategy]


st.sidebar.metric(
    "Capital del taller",
    f"USD {CAPITAL_USD:,.0f}"
)

st.sidebar.caption(
    "El 100% del capital se distribuye "
    "entre los cinco ETFs."
)


st.sidebar.divider()


# ============================================================
# PARÁMETROS FINANCIEROS
# ============================================================

st.sidebar.subheader(
    "Análisis financiero"
)

default_start = (
    date.today()
    - timedelta(days=365 * 5)
)

start_date = (
    st.sidebar.date_input(
        "Inicio del análisis",
        value=default_start,
        min_value=date(2016, 1, 1),
        max_value=(
            date.today()
            - timedelta(days=5)
        ),
    )
)

end_date = (
    st.sidebar.date_input(
        "Fin del análisis",
        value=date.today(),
        min_value=(
            start_date
            + timedelta(days=1)
        ),
        max_value=date.today(),
    )
)

benchmark = (
    st.sidebar.selectbox(
        "Benchmark",
        [
            "ACWI",
            "SPY",
        ]
    )
)

risk_free = (
    st.sidebar.slider(
        "Tasa libre de riesgo para Sharpe (%)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.25,
    )
    / 100
)


# ============================================================
# DESCARGA DE DATOS
# ============================================================

symbols = (
    TICKERS
    + [benchmark]
)

try:

    prices = download_prices(
        symbols,
        str(start_date),
        str(
            end_date
            + timedelta(days=1)
        ),
    )

    prices_5y = (
        download_five_year_prices(
            TICKERS
        )
    )

except Exception as e:

    st.error(
        "No fue posible descargar "
        "los datos de mercado."
    )

    st.code(str(e))

    st.info(
        "Actualiza la página. "
        "Yahoo Finance puede limitar "
        "temporalmente algunas consultas."
    )

    st.stop()


missing = [
    ticker
    for ticker in symbols
    if (
        ticker not in prices.columns
        or prices[ticker]
        .dropna()
        .empty
    )
]


if missing:

    st.error(
        "No se obtuvieron datos para: "
        + ", ".join(missing)
    )

    st.stop()


portfolio_prices = (
    prices[TICKERS]
    .dropna(how="any")
)

benchmark_prices = (
    prices[benchmark]
    .reindex(
        portfolio_prices.index
    )
    .ffill()
    .bfill()
)


if len(portfolio_prices) < 30:

    st.error(
        "El período seleccionado "
        "tiene muy pocas observaciones."
    )

    st.stop()


# ============================================================
# CÁLCULOS
# ============================================================

nav = portfolio_nav(
    portfolio_prices,
    weights
)

benchmark_nav = (
    benchmark_prices
    / benchmark_prices.iloc[0]
    * CAPITAL_USD
)

metrics = portfolio_metrics(
    nav,
    risk_free
)

assets = asset_metrics(
    portfolio_prices
)

corr = (
    portfolio_prices
    .pct_change(
        fill_method=None
    )
    .dropna()
    .corr()
)


five_year_returns = {
    ticker:
        five_year_cagr(
            prices_5y[ticker]
        )
        if ticker
        in prices_5y.columns
        else np.nan

    for ticker in TICKERS
}


# ============================================================
# PESTAÑAS
# ============================================================

(
    tab_assignment,
    tab_performance,
    tab_risk,
    tab_sustainability,
    tab_methodology

) = st.tabs(
    [
        "📋 Portafolio del taller",
        "📈 Performance",
        "⚖️ Risk Lab",
        "🌱 Sustainability Lens",
        "🧠 Metodología",
    ]
)


# ============================================================
# PORTAFOLIO DEL TALLER
# ============================================================

with tab_assignment:

    st.subheader(
        "Portafolio sostenible — USD 100,000"
    )

    st.caption(
        "La asignación siempre suma 100%. "
        "La rentabilidad de cinco años "
        "se calcula automáticamente con "
        "datos históricos reales."
    )


    assignment_rows = []


    for ticker in TICKERS:

        info = ETF_INFO[ticker]

        w = weights[ticker]

        return_5y = (
            five_year_returns[ticker]
        )

        assignment_rows.append(
            {
                "Nombre del ETF":
                    f"{ticker} — {info['name']}",

                "Descripción":
                    info["description"],

                "Asignación %":
                    w * 100,

                "USD $":
                    CAPITAL_USD * w,

                "Rentabilidad promedio 5 años":
                    (
                        return_5y * 100
                        if pd.notna(return_5y)
                        else np.nan
                    ),

                "¿Por qué ese ETF?":
                    info["why"],

                "¿Qué problema resuelve?":
                    info["problem"],
            }
        )


    assignment_df = pd.DataFrame(
        assignment_rows
    )


    st.dataframe(
        assignment_df,
        hide_index=True,
        use_container_width=True,

        column_config={

            "Asignación %":
                st.column_config.NumberColumn(
                    "Asignación %",
                    format="%.1f%%",
                ),

            "USD $":
                st.column_config.NumberColumn(
                    "USD $",
                    format="$ %.0f",
                ),

            "Rentabilidad promedio 5 años":
                st.column_config.NumberColumn(
                    "Rentabilidad promedio 5 años*",
                    format="%.2f%%",
                ),
        },
    )


    c1, c2, c3 = st.columns(3)


    c1.metric(
        "Capital asignado",
        f"USD {CAPITAL_USD:,.0f}"
    )


    c2.metric(
        "Número de ETFs",
        len(TICKERS)
    )


    c3.metric(
        "Asignación total",
        f"{sum(weights.values()):.0%}"
    )


    st.caption(
        "*La rentabilidad de cinco años "
        "se presenta como CAGR: "
        "tasa de crecimiento anual compuesta. "
        "Es información histórica y no garantiza "
        "rentabilidad futura."
    )


    st.markdown(
        "### Distribución del capital"
    )


    allocation_view = (
        pd.DataFrame(
            {
                "ETF": TICKERS,

                "Peso": [
                    weights[ticker] * 100
                    for ticker in TICKERS
                ],

                "USD": [
                    CAPITAL_USD
                    * weights[ticker]

                    for ticker
                    in TICKERS
                ],
            }
        )
    )


    left, right = st.columns(
        [1, 1]
    )


    with left:

        fig = px.pie(
            allocation_view,
            names="ETF",
            values="Peso",
            hole=0.58,
            title="Asignación del portafolio",
        )

        fig.update_traces(
            textinfo="label+percent"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with right:

        fig = px.bar(
            allocation_view,
            x="ETF",
            y="USD",
            title="Capital invertido por ETF",
            text_auto=".3s",
        )

        fig.update_yaxes(
            title="USD"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# PERFORMANCE
# ============================================================

with tab_performance:

    st.subheader(
        "Desempeño financiero"
    )


    m1, m2, m3, m4 = st.columns(4)


    m1.metric(
        "Rentabilidad acumulada",
        f"{metrics['cumulative_return']:.1%}"
    )


    m2.metric(
        "Volatilidad anualizada",
        f"{metrics['annualized_volatility']:.1%}"
    )


    m3.metric(
        "Sharpe ratio",
        f"{metrics['sharpe_ratio']:.2f}"
    )


    m4.metric(
        "Máximo drawdown",
        f"{metrics['max_drawdown']:.1%}"
    )


    perf_df = (
        pd.DataFrame(
            {
                "Portafolio sostenible":
                    nav,

                benchmark:
                    benchmark_nav,
            }
        )
        .reset_index()
    )


    fig = px.line(
        perf_df,
        x="Date",

        y=[
            "Portafolio sostenible",
            benchmark,
        ],

        title=(
            "Crecimiento de "
            f"USD {CAPITAL_USD:,.0f}"
        ),

        labels={
            "value":
                "Valor del portafolio (USD)",

            "variable":
                "",
        },
    )


    fig.update_layout(
        hovermode="x unified",
        legend_orientation="h",
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.subheader(
        "Métricas por ETF"
    )


    show_assets = assets.copy()


    for col in [
        "Rentabilidad anualizada",
        "Volatilidad anualizada",
        "Max drawdown",
        "Rentabilidad acumulada",
    ]:

        show_assets[col] = (
            show_assets[col]
            .map(
                lambda x:
                    f"{x:.1%}"
                    if pd.notna(x)
                    else "N/A"
            )
        )


    st.dataframe(
        show_assets,
        use_container_width=True
    )


    st.info(
        "La sostenibilidad no elimina "
        "el riesgo financiero. "
        "Un ETF temático puede ser más volátil "
        "que un ETF ampliamente diversificado."
    )


# ============================================================
# RISK LAB
# ============================================================

with tab_risk:

    st.subheader(
        "Risk Lab"
    )


    st.caption(
        "Esta sección permite observar "
        "si los activos realmente diversifican "
        "el portafolio o tienden a moverse juntos."
    )


    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        zmin=-1,
        zmax=1,
        title="Matriz de correlaciones",
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    drawdown = (
        nav
        / nav.cummax()
        - 1
    )


    fig = px.area(
        x=drawdown.index,
        y=drawdown.values,

        title=(
            "Drawdown del portafolio"
        ),

        labels={
            "x": "Fecha",
            "y": "Drawdown",
        },
    )


    fig.update_yaxes(
        tickformat=".0%"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.markdown(
        """
        **Lectura rápida**

        **Volatilidad:** cuánto fluctúan los retornos.

        **Sharpe ratio:** cuánto retorno se obtiene en relación con el riesgo asumido.

        **Drawdown:** caída desde un máximo anterior hasta un mínimo posterior.

        **Correlación:** qué tanto dos activos tienden a moverse juntos.
        """
    )


# ============================================================
# SUSTAINABILITY LENS
# ============================================================

with tab_sustainability:

    st.subheader(
        "Sustainability Lens"
    )


    st.caption(
        "La etiqueta ESG o sostenible "
        "no se acepta automáticamente "
        "como prueba de impacto."
    )


    for ticker in TICKERS:

        info = ETF_INFO[ticker]


        with st.expander(
            f"{ticker} — {info['name']}",
            expanded=False,
        ):


            a, b, c = st.columns(3)


            a.metric(
                "Peso en el portafolio",
                f"{weights[ticker]:.1%}"
            )


            b.metric(
                "Expense ratio",
                f"{info['expense_ratio']:.2%}"
            )


            c.metric(
                "Tipo de activo",
                info["asset_type"]
            )


            st.markdown(
                f"**Rol:** "
                f"{info['role']}"
            )


            st.markdown(
                f"**Por qué está en el portafolio:** "
                f"{info['why']}"
            )


            st.markdown(
                f"**Problema que aborda:** "
                f"{info['problem']}"
            )


            st.markdown(
                f"**Qué cuestionar:** "
                f"{info['limitations']}"
            )


            st.markdown(
                "".join(
                    f"<span class='chip'>"
                    f"ODS {ods.strip()}"
                    f"</span>"

                    for ods
                    in info["sdgs"].split(",")
                ),

                unsafe_allow_html=True,
            )


            st.markdown(
                f"[Fuente oficial del ETF]"
                f"({info['source']})"
            )


    st.warning(
        "Un ETF ESG no significa que todas "
        "sus empresas sean perfectamente sostenibles. "
        "Los criterios y metodologías varían "
        "entre proveedores."
    )


# ============================================================
# METODOLOGÍA
# ============================================================

with tab_methodology:

    st.subheader(
        "Metodología"
    )


    st.markdown(
        f"""
### 1. Capital

El taller parte de **USD {CAPITAL_USD:,.0f}**, distribuidos completamente entre cinco ETFs.

### 2. Selección de activos

El portafolio combina:

- renta variable ESG de EE. UU.;
- renta variable ESG internacional;
- energía limpia;
- energía solar;
- bonos verdes.

### 3. Datos

Los precios históricos se descargan automáticamente desde Yahoo Finance mediante `yfinance`.

### 4. Rentabilidad de cinco años

La columna solicitada en el taller utiliza **CAGR**, es decir, la tasa anual compuesta que conecta el precio inicial y final del ETF durante aproximadamente cinco años.

### 5. Métricas financieras

**Rentabilidad acumulada:** variación total del valor del portafolio.

**Volatilidad anualizada:** mide cuánto fluctúan sus retornos.

**Sharpe ratio:** relaciona retorno y riesgo.

**Maximum drawdown:** mayor caída desde un máximo previo.

**Correlación:** muestra qué tanto los ETFs tienden a moverse juntos.

### 6. Sostenibilidad

La selección no depende únicamente del desempeño histórico. Cada ETF incorpora una metodología o temática asociada con ESG, energía limpia, energía solar o bonos verdes.

### 7. Limitación

**Sostenible no significa sin riesgo y tampoco garantiza mayor rentabilidad.**

Este proyecto tiene fines educativos y no constituye asesoría de inversión.
        """
    )


    st.subheader(
        "Pesos actuales"
    )


    st.json(
        {
            ticker:
                f"{weight:.2%}"

            for ticker, weight
            in weights.items()
        }
    )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Datos de mercado: Yahoo Finance vía yfinance · "
    f"Ventana analizada: "
    f"{portfolio_prices.index.min().date()} → "
    f"{portfolio_prices.index.max().date()} · "
    f"Última observación disponible: "
    f"{portfolio_prices.index.max().date()}"
)
