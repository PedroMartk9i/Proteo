"""Página Entrenar: SARIMAX con controles para mover parámetros y ver
el resultado sin reentrenar lo ya calculado."""

import json
import sys
from datetime import date
from pathlib import Path

# Permite importar ``proteo`` al correr la app desde la raíz del repo.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from proteo.dataset import build_dataset, future_exog, inverse_transform
from proteo.models.presets import PAPER
from proteo.models.sarimax import SARIMAXModel
from proteo.store import vintages

st.set_page_config(page_title="Entrenar · Proteo", page_icon="🌊", layout="wide")

st.title("Entrenar")
st.caption("SARIMAX sobre el precio mensual, con exógena ENSO opcional.")

# Paleta de la guía de diseño del proyecto (guia_diseno_figuras.md).
COLOR = {
    "obs": "#22303f",       # serie observada
    "sarimax": "#1d4ed8",   # modelo principal
    "banda": "rgba(29, 78, 216, 0.15)",
    "asumido": "#c2410c",   # exógena supuesta: requiere atención
    "eje": "#8a949e",
    "calida": "#d94a3d",
    "fria": "#2f6fb0",
}

EXOG_OPTIONS = {"ninguna": None, "RONI": "roni", "Niño 3.4": "nino34"}
PRICE_INDEX = "xm_precio_bolsa"
CONFIG_PATH = ROOT / "config" / "active_model.json"


# --- Carga con caché --------------------------------------------------------
@st.cache_data
def _load_vintage(index: str, vintage_iso: str) -> pd.DataFrame:
    return vintages.load(index, date.fromisoformat(vintage_iso))


@st.cache_data(show_spinner=False)
def _train(
    price_vintage: str,
    exog_index: str | None,
    exog_vintage: str | None,
    lag: int,
    add_squared: bool,
    log_target: bool,
    start: str,
    end: str,
    order: tuple,
    seasonal_order: tuple,
    h: int,
    alpha: float,
) -> dict:
    """Entrena y pronostica. La clave de caché son todos los parámetros:
    mover un control no reentrena lo que ya se calculó."""
    price = _load_vintage(PRICE_INDEX, price_vintage)
    exog = _load_vintage(exog_index, exog_vintage) if exog_index else None

    y, X = build_dataset(
        price, exog, lag=lag, start=start, end=end,
        log_target=log_target, add_squared=add_squared,
    )
    model = SARIMAXModel(order=order, seasonal_order=seasonal_order).fit(y, X)

    X_future = None
    exog_future = None
    if exog is not None:
        exog_future = future_exog(exog, y.index[-1], h, lag, add_squared=add_squared)
        X_future = exog_future.drop(columns="assumed")

    fc = model.forecast(h, X_future=X_future, alpha=alpha)
    # Todo se devuelve en NIVEL para graficar (deshace el log si aplica).
    for col in ("mean", "lower", "upper"):
        fc[col] = inverse_transform(fc[col], log_target)
    fitted = inverse_transform(model.fitted(), log_target)
    y_level = inverse_transform(y, log_target)

    return {
        "y": y_level,
        "fitted": fitted,
        "forecast": fc,
        "summary": model.summary(),
        "exog_future": exog_future,
        "exog_series": (
            exog.set_index("date")["value"] if exog is not None else None
        ),
    }


# --- Barra lateral ----------------------------------------------------------
# Defaults de los controles con clave: se fijan una sola vez en session_state
# y los widgets NO declaran valor propio (evita el conflicto default/estado).
CONTROL_DEFAULTS = dict(
    p=1, d=1, q=1, P=1, D=0, Q=0,
    exog_label="RONI", lag=2, add_squared=False, target="nivel",
)
for key, value in CONTROL_DEFAULTS.items():
    st.session_state.setdefault(key, value)


def _apply_paper() -> None:
    """Aplica la configuración de referencia del paper a los controles."""
    st.session_state.update(
        p=PAPER["order"][0], d=PAPER["order"][1], q=PAPER["order"][2],
        P=PAPER["seasonal_order"][0], D=PAPER["seasonal_order"][1],
        Q=PAPER["seasonal_order"][2],
        exog_label="RONI", lag=PAPER["lag"],
        add_squared=PAPER["add_squared"],
        target="nivel" if not PAPER["log_target"] else "log",
    )


with st.sidebar:
    st.header("Configuración")

    price_vintages = vintages.list_vintages(PRICE_INDEX)
    if not price_vintages:
        st.error("No hay vintages de precio. Descarga XM en la página Datos.")
        st.stop()
    price_vintage = st.selectbox(
        "Vintage de precio", price_vintages, index=len(price_vintages) - 1,
        format_func=str,
    )

    exog_label = st.selectbox("Exógena", list(EXOG_OPTIONS), key="exog_label")
    exog_index = EXOG_OPTIONS[exog_label]

    exog_vintage = None
    if exog_index:
        exog_vintages = vintages.list_vintages(exog_index)
        if not exog_vintages:
            st.error(f"No hay vintages de {exog_label}. Descárgala en Datos.")
            st.stop()
        exog_vintage = st.selectbox(
            f"Vintage de {exog_label}", exog_vintages,
            index=len(exog_vintages) - 1, format_func=str,
        )

    price_df = _load_vintage(PRICE_INDEX, price_vintage.isoformat())
    last_month = price_df["date"].max().date()

    col_a, col_b = st.columns(2)
    with col_a:
        train_start = st.date_input(
            "Inicio", date(2000, 1, 1),
            min_value=date(2000, 1, 1), max_value=last_month,
        )
    with col_b:
        train_end = st.date_input(
            "Fin", last_month,
            min_value=date(2000, 1, 1), max_value=last_month,
        )

    target = st.radio("Objetivo", ["nivel", "log"], horizontal=True, key="target")

    lag = st.slider("Rezago de la exógena", 0, 6, key="lag",
                    disabled=exog_index is None)
    add_squared = st.checkbox("Agregar término cuadrático", key="add_squared",
                              disabled=exog_index is None)

    st.markdown("**Orden (p, d, q)**")
    c1, c2, c3 = st.columns(3)
    p = c1.number_input("p", 0, 3, key="p")
    d = c2.number_input("d", 0, 3, key="d")
    q = c3.number_input("q", 0, 3, key="q")

    st.markdown("**Estacional (P, D, Q), s = 12**")
    c4, c5, c6 = st.columns(3)
    P = c4.number_input("P", 0, 2, key="P")
    D = c5.number_input("D", 0, 2, key="D")
    Q = c6.number_input("Q", 0, 2, key="Q")

    h = st.slider("Horizonte (meses)", 1, 12, 6)
    confidence = st.select_slider("Confianza (%)", [80, 90, 95], value=80)
    alpha = round(1 - confidence / 100, 4)

    st.button("Cargar configuración del paper", on_click=_apply_paper)
    train_clicked = st.button("Entrenar", type="primary")

if train_clicked:
    st.session_state["trained"] = True

# --- Panel principal --------------------------------------------------------
if not st.session_state.get("trained"):
    st.info("Configura el modelo en la barra lateral y pulsa **Entrenar**.")
    st.stop()

log_target = target == "log"
order = (int(p), int(d), int(q))
seasonal_order = (int(P), int(D), int(Q), 12)

try:
    result = _train(
        price_vintage.isoformat(),
        exog_index,
        exog_vintage.isoformat() if exog_vintage else None,
        int(lag), bool(add_squared), log_target,
        train_start.isoformat(), train_end.isoformat(),
        order, seasonal_order, int(h), float(alpha),
    )
except Exception as exc:  # noqa: BLE001 — SARIMAX puede fallar al converger
    st.error(f"El entrenamiento falló con esta configuración: {exc}")
    st.stop()

y = result["y"]
fc = result["forecast"]
summary = result["summary"]

# Métricas de ajuste.
m1, m2, m3, m4 = st.columns(4)
m1.metric("AIC", f"{summary['aic']:.1f}")
m2.metric("BIC", f"{summary['bic']:.1f}")
m3.metric(
    "Ljung-Box p (12)", f"{summary['ljung_box_p']:.3f}",
    help="Si es menor a 0.05 quedan autocorrelaciones sin modelar.",
)
m4.metric("n_obs", summary["n_obs"])

# Advertencia de persistencia cuando el horizonte supera el rezago.
if exog_index and h > lag:
    first_assumed = lag + 1
    st.warning(
        f"Los pasos {first_assumed} a {h} usan {exog_label} supuesto por "
        "persistencia (último valor observado)."
    )

# Tabla de coeficientes con la fila de la exógena resaltada.
st.subheader("Coeficientes")
coef_df = pd.DataFrame(summary["coefficients"]).T
coef_df.index.name = "parámetro"
exog_rows = [
    name for name in coef_df.index
    if exog_index and name.startswith(f"{exog_index}_lag")
]
st.dataframe(
    coef_df.style
    .format({"coef": "{:.4f}", "std_err": "{:.4f}", "pvalue": "{:.2e}"})
    .apply(
        lambda row: ["background-color: #e8eef4; font-weight: bold"] * len(row)
        if row.name in exog_rows else [""] * len(row),
        axis=1,
    )
)

# --- Gráfica principal: observado, ajustado, pronóstico ---------------------
st.subheader("Ajuste y pronóstico")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=y.index, y=y.values, mode="lines", name="Observado",
    line=dict(color=COLOR["obs"], width=1),
))
fitted = result["fitted"]
fig.add_trace(go.Scatter(
    x=fitted.index, y=fitted.values, mode="lines", name="Ajustado",
    line=dict(color=COLOR["sarimax"], width=1.2, dash="dot"),
))
fig.add_trace(go.Scatter(
    x=pd.concat([fc["date"], fc["date"][::-1]]),
    y=pd.concat([fc["upper"], fc["lower"][::-1]]),
    fill="toself", fillcolor=COLOR["banda"], line=dict(width=0),
    name=f"Intervalo {confidence}%", hoverinfo="skip",
))
fig.add_trace(go.Scatter(
    x=fc["date"], y=fc["mean"], mode="lines+markers", name="Pronóstico",
    line=dict(color=COLOR["sarimax"], width=2.2), marker=dict(size=5),
))
fig.add_vline(x=y.index[-1], line_dash="dash", line_color=COLOR["eje"])
fig.update_layout(
    xaxis_title="Fecha", yaxis_title="Precio de bolsa (COP/kWh)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=30),
)
st.plotly_chart(fig, width="stretch")

# --- Panel de la exógena, con las filas supuestas en otro color -------------
if exog_index:
    exog_future = result["exog_future"]
    exog_col = f"{exog_index}_lag{lag}"
    observed_x = result["exog_series"]

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=observed_x.index, y=observed_x.values, mode="lines",
        name=f"{exog_label} observado",
        line=dict(color=COLOR["obs"], width=1),
    ))
    real = exog_future[~exog_future["assumed"]]
    sup = exog_future[exog_future["assumed"]]
    if not real.empty:
        fig2.add_trace(go.Scatter(
            x=real.index, y=real[exog_col], mode="markers",
            name="Futuro con valor observado",
            marker=dict(color=COLOR["sarimax"], size=7),
        ))
    if not sup.empty:
        fig2.add_trace(go.Scatter(
            x=sup.index, y=sup[exog_col], mode="markers",
            name="Futuro supuesto (persistencia)",
            marker=dict(color=COLOR["asumido"], size=7, symbol="diamond"),
        ))
    fig2.add_hline(y=0.5, line_dash="dash", line_color=COLOR["calida"])
    fig2.add_hline(y=-0.5, line_dash="dash", line_color=COLOR["fria"])
    fig2.update_layout(
        xaxis_title="Fecha", yaxis_title=f"{exog_label} (anomalía, °C)",
        hovermode="x unified", height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30),
    )
    st.plotly_chart(fig2, width="stretch")

# --- Acciones ---------------------------------------------------------------
col_save, col_csv = st.columns(2)

with col_save:
    if st.button("Guardar como configuración activa"):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        active = {
            "model": "sarimax",
            "order": list(order),
            "seasonal_order": list(seasonal_order),
            "exog": exog_index,
            "lag": int(lag),
            "add_squared": bool(add_squared),
            "log_target": log_target,
            "train_start": train_start.isoformat(),
            "train_end": train_end.isoformat(),
            "alpha": float(alpha),
            "h": int(h),
            "vintages": {
                PRICE_INDEX: price_vintage.isoformat(),
                **({exog_index: exog_vintage.isoformat()} if exog_index else {}),
            },
            "saved_at": date.today().isoformat(),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(active, fh, indent=2, ensure_ascii=False)
        st.success(f"Configuración activa guardada en {CONFIG_PATH.relative_to(ROOT)}.")

with col_csv:
    st.download_button(
        "Descargar pronóstico (CSV)",
        fc.to_csv(index=False).encode("utf-8"),
        file_name=f"pronostico_{date.today().isoformat()}.csv",
        mime="text/csv",
    )
