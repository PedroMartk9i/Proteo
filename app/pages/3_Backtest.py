"""Página Backtest: origen móvil, métricas por horizonte, Diebold-Mariano
y desglose por fase ENSO."""

import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

# Permite importar ``proteo`` y ``app`` al correr desde la raíz del repo.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import components, theme
from app.theme import PALETTE, PLOTLY_CONFIG
from proteo.backtest.dm_test import diebold_mariano
from proteo.backtest.metrics import by_enso_phase, by_horizon, coverage, skill
from proteo.backtest.rolling_origin import run_backtest
from proteo.dataset import build_dataset
from proteo.models.naive import Naive, SeasonalNaive
from proteo.models.presets import PAPER
from proteo.models.sarimax import SARIMAXModel
from proteo.store import vintages

theme.page_setup("Backtest")

st.title("Backtest")
st.markdown(
    '<p class="pt-help">Origen móvil: entrenar hasta t, pronosticar '
    "t+1..t+h, avanzar un mes. Usa el vintage más reciente para todas las "
    "fechas.</p>",
    unsafe_allow_html=True,
)

PRICE_INDEX = "xm_precio_bolsa"
CONFIG_PATH = ROOT / "config" / "active_model.json"
BACKTESTS_DIR = ROOT / "data" / "backtests"

MODEL_LABELS = {
    "naive": "Naive",
    "naive_estacional": "Naive estacional",
    "sarimax": "SARIMAX sin exógena",
    "sarimax_roni": "SARIMAX con exógena",
}
PHASE_NAMES = {"nino": "El Niño", "nina": "La Niña", "neutral": "Neutral"}


def _active_config() -> dict:
    """Configuración activa de la página Entrenar, o el preset del paper."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cfg = json.load(fh)
        return {
            "order": tuple(cfg["order"]),
            "seasonal_order": tuple(cfg["seasonal_order"]),
            "exog": cfg.get("exog") or "roni",
            "lag": cfg.get("lag", 2),
            "add_squared": cfg.get("add_squared", False),
            "log_target": cfg.get("log_target", False),
            "source": "config/active_model.json",
        }
    return {
        "order": PAPER["order"],
        "seasonal_order": tuple(PAPER["seasonal_order"]),
        "exog": PAPER["exog"],
        "lag": PAPER["lag"],
        "add_squared": PAPER["add_squared"],
        "log_target": PAPER["log_target"],
        "source": "preset del paper",
    }


cfg = _active_config()

# --- Barra lateral ----------------------------------------------------------
with st.sidebar:
    with st.container(border=True):
        components.control_header(
            "modelo sarimax",
            f"{cfg['order']}{cfg['seasonal_order']}",
        )
        st.markdown(
            f'<p class="pt-help">Exógena {cfg["exog"]} rezago {cfg["lag"]} · '
            f"fuente: {cfg['source']}</p>",
            unsafe_allow_html=True,
        )
        selected_models = st.multiselect(
            "Modelos",
            list(MODEL_LABELS),
            default=list(MODEL_LABELS),
            format_func=MODEL_LABELS.get,
        )

    with st.container(border=True):
        components.control_header("datos", cfg["exog"])
        price_vintages = vintages.list_vintages(PRICE_INDEX)
        exog_vintages = vintages.list_vintages(cfg["exog"])
        if not price_vintages or not exog_vintages:
            st.error(
                "Falta un vintage de precio o de exógena. "
                "Descárgalos en la página Datos."
            )
            st.stop()
        price_vintage = st.selectbox(
            "Vintage de precio", price_vintages, index=len(price_vintages) - 1
        )
        exog_vintage = st.selectbox(
            f"Vintage de {cfg['exog']}", exog_vintages,
            index=len(exog_vintages) - 1,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            range_start = st.date_input("Inicio de datos", date(2000, 1, 1))
        with col_b:
            range_end = st.date_input("Fin de datos", date.today())

    with st.container(border=True):
        components.control_header("origen móvil", "")
        initial_train = st.number_input("initial_train (meses)", 24, 400, 203)
        h_min, h_max = st.slider("Horizontes", 1, 12, (1, 6))
        window = st.radio("Ventana", ["expanding", "rolling"], horizontal=True)
        refit_every = st.number_input(
            "refit_every", 1, 12, 1,
            help="Reentrena cada k orígenes; los intermedios reutilizan parámetros.",
        )

    run_clicked = st.button("Correr backtest", type="primary")


def _model_factories() -> dict:
    sarimax_factory = lambda: SARIMAXModel(  # noqa: E731
        order=cfg["order"], seasonal_order=cfg["seasonal_order"]
    )
    return {
        "naive": (Naive, False),
        "naive_estacional": (SeasonalNaive, False),
        "sarimax": (sarimax_factory, False),
        "sarimax_roni": (sarimax_factory, True),
    }


# --- Correr -----------------------------------------------------------------
if run_clicked:
    if not selected_models:
        st.error("Selecciona al menos un modelo y vuelve a pulsar Correr backtest.")
        st.stop()

    price = vintages.load(PRICE_INDEX, price_vintage)
    exog = vintages.load(cfg["exog"], exog_vintage)
    y, X = build_dataset(
        price, exog, lag=cfg["lag"],
        start=range_start.isoformat(), end=range_end.isoformat(),
        log_target=cfg["log_target"], add_squared=cfg["add_squared"],
    )
    horizons = list(range(h_min, h_max + 1))
    if len(y) <= initial_train + max(horizons):
        st.error(
            f"Datos insuficientes: {len(y)} meses para initial_train="
            f"{initial_train} y horizonte {max(horizons)}. Reduce initial_train."
        )
        st.stop()

    factories = _model_factories()
    bar = st.progress(0.0, text="Corriendo backtest")
    t0 = time.time()
    frames = []
    for m_idx, key in enumerate(selected_models):
        factory, use_exog = factories[key]

        def _progress(i, total, _m=m_idx, _key=key):
            frac = (_m + i / total) / len(selected_models)
            bar.progress(
                min(frac, 1.0),
                text=f"{MODEL_LABELS[_key]} · origen {i}/{total} · "
                     f"{time.time() - t0:.0f} s",
            )

        frames.append(
            run_backtest(
                factory, y, X=X if use_exog else None,
                initial_train=int(initial_train), horizons=horizons,
                window=window, refit_every=int(refit_every),
                progress=_progress, label=key,
            )
        )
    bar.progress(1.0, text=f"Terminado en {time.time() - t0:.0f} s")
    results = pd.concat(frames, ignore_index=True)

    # Guardar la corrida: parquet + JSON con la configuración.
    BACKTESTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    results.to_parquet(BACKTESTS_DIR / f"{stamp}.parquet", index=False)
    run_config = {
        "models": selected_models,
        "order": list(cfg["order"]),
        "seasonal_order": list(cfg["seasonal_order"]),
        "exog": cfg["exog"], "lag": cfg["lag"],
        "add_squared": cfg["add_squared"], "log_target": cfg["log_target"],
        "initial_train": int(initial_train), "horizons": horizons,
        "window": window, "refit_every": int(refit_every),
        "range": [range_start.isoformat(), range_end.isoformat()],
        "vintages": {
            PRICE_INDEX: price_vintage.isoformat(),
            cfg["exog"]: exog_vintage.isoformat(),
        },
        "elapsed_s": round(time.time() - t0, 1),
        "n_obs": len(y),
    }
    with open(BACKTESTS_DIR / f"{stamp}.json", "w", encoding="utf-8") as fh:
        json.dump(run_config, fh, indent=2, ensure_ascii=False)
    st.success(f"Corrida guardada como data/backtests/{stamp}.parquet")

    st.session_state["bt_results"] = results
    st.session_state["bt_config"] = run_config

# --- Cargar corrida anterior ------------------------------------------------
saved_runs = (
    sorted(BACKTESTS_DIR.glob("*.parquet"), reverse=True)
    if BACKTESTS_DIR.exists() else []
)
if saved_runs and "bt_results" not in st.session_state:
    components.section("Cargar backtest anterior")
    chosen = st.selectbox(
        "Corridas guardadas", saved_runs, format_func=lambda p: p.stem
    )
    if st.button("Cargar"):
        st.session_state["bt_results"] = pd.read_parquet(chosen)
        config_file = chosen.with_suffix(".json")
        st.session_state["bt_config"] = (
            json.loads(config_file.read_text(encoding="utf-8"))
            if config_file.exists() else {}
        )
        st.rerun()

# --- Resultados -------------------------------------------------------------
if "bt_results" not in st.session_state:
    st.info("Configura y pulsa Correr backtest, o carga una corrida anterior.")
    st.stop()

results = st.session_state["bt_results"]
run_config = st.session_state.get("bt_config", {})
models_present = list(results["model"].unique())
horizons_present = sorted(results["horizon"].unique())

components.section("Métricas por modelo y horizonte")
table = by_horizon(results)
table["model"] = table["model"].map(lambda m: MODEL_LABELS.get(m, m))
st.dataframe(
    table,
    hide_index=True,
    column_config={
        metric: st.column_config.NumberColumn(metric, format="%.2f")
        for metric in ("mae", "rmse", "mape", "smape")
    },
)

if {"sarimax", "sarimax_roni"} <= set(models_present):
    components.section(
        "Mejora % por incluir RONI (RMSE)",
        help="Positivo = el SARIMAX con exógena mejora al que no la tiene.",
    )
    improvement = skill(results, "sarimax_roni", "sarimax")
    st.dataframe(
        improvement.style
        .format({"improvement_pct": "{:+.1f} %"})
        .map(
            lambda v: f"color: {PALETTE['nino']}; font-weight: 500" if v > 0
            else f"color: {PALETTE['nina']}; font-weight: 500",
            subset=["improvement_pct"],
        ),
        hide_index=True,
    )

components.section(
    "Diebold-Mariano (p-valores, pérdida cuadrática)",
    help="Celdas anotadas en oscuro: p < 0.05. stat < 0 = el modelo de la "
         "fila pierde menos.",
)
tabs = st.tabs([f"h = {h}" for h in horizons_present])
for tab, h in zip(tabs, horizons_present):
    with tab:
        sub = results[results["horizon"] == h]
        errors = {
            m: (lambda g: (g["actual"] - g["forecast"]))(
                sub[sub["model"] == m].set_index("origin").sort_index()
            )
            for m in models_present
        }
        labels = [MODEL_LABELS.get(m, m) for m in models_present]
        z = []
        for m1 in models_present:
            row = []
            for m2 in models_present:
                if m1 == m2:
                    row.append(None)
                    continue
                joined = pd.concat(
                    [errors[m1].rename("e1"), errors[m2].rename("e2")], axis=1
                ).dropna()
                out = diebold_mariano(joined["e1"], joined["e2"], h=int(h))
                row.append(out["pvalue"])
            z.append(row)

        fig = go.Figure(go.Heatmap(
            z=z, x=labels, y=labels,
            zmin=0, zmax=1,
            colorscale=[[0, PALETTE["panel"]], [1, PALETTE["papel"]]],
            showscale=False, hoverongaps=False,
        ))
        for i, m1 in enumerate(labels):
            for j, _ in enumerate(labels):
                value = z[i][j]
                if value is None:
                    continue
                fig.add_annotation(
                    x=j, y=i, text=f"{value:.3f}", showarrow=False,
                    font=dict(
                        color=PALETTE["linea"] if value < 0.05
                        else PALETTE["tinta"],
                        size=12,
                    ),
                )
        fig.update_layout(
            height=320, yaxis=dict(autorange="reversed"),
            xaxis=dict(showgrid=False), margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

components.section("Desglose por fase ENSO en el origen")
exog_name = run_config.get("exog", "roni")
exog_vintage_saved = run_config.get("vintages", {}).get(exog_name)
try:
    roni_df = vintages.load(
        exog_name,
        date.fromisoformat(exog_vintage_saved) if exog_vintage_saved else None,
    )
    phase_table = by_enso_phase(results, roni_df)
    phase_cols = st.columns(3)
    for col, phase in zip(phase_cols, ("nino", "nina", "neutral")):
        with col:
            block = phase_table[phase_table["phase"] == phase]
            n_origins = (
                int(block["n"].sum() / max(len(block), 1)) if not block.empty else 0
            )
            st.markdown(
                f'<div class="pt-datahead"><span class="pt-name">'
                f"{PHASE_NAMES[phase]}</span>{components.phase_led(phase)}"
                f'<span class="pt-stamp">n {n_origins} por horizonte</span></div>',
                unsafe_allow_html=True,
            )
            for model in models_present:
                rows = block[block["model"] == model]
                if rows.empty:
                    continue
                components.metric_card(
                    MODEL_LABELS.get(model, model),
                    f"{rows['rmse'].mean():.1f}",
                    hint=f"RMSE · MAE {rows['mae'].mean():.1f}",
                )
    with st.expander("Tabla completa por fase, modelo y horizonte"):
        detail = phase_table.copy()
        detail["model"] = detail["model"].map(lambda m: MODEL_LABELS.get(m, m))
        detail["phase"] = detail["phase"].map(lambda p: PHASE_NAMES.get(p, p))
        st.dataframe(
            detail,
            hide_index=True,
            column_config={
                metric: st.column_config.NumberColumn(metric, format="%.2f")
                for metric in ("mae", "rmse", "mape", "smape")
            },
        )
except FileNotFoundError:
    st.info(
        f"No hay vintage de {exog_name} para clasificar fases. "
        f"Descárgalo en la página Datos."
    )

components.section("Error absoluto en el tiempo")
chart_h = st.selectbox("Horizonte", horizons_present)
fig = go.Figure()
for m in models_present:
    sub = results[(results["model"] == m) & (results["horizon"] == chart_h)]
    fig.add_trace(go.Scatter(
        x=sub["target_date"], y=(sub["actual"] - sub["forecast"]).abs(),
        mode="lines", name=MODEL_LABELS.get(m, m), line=dict(width=1.3),
    ))
fig.update_layout(
    xaxis_title="Fecha objetivo", yaxis_title="|error| (COP/kWh)", height=350,
)
st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

components.section("Cobertura de intervalos (nominal 80 %)")
cov = coverage(results)
cov["model"] = cov["model"].map(lambda m: MODEL_LABELS.get(m, m))
st.dataframe(
    cov.pivot(index="model", columns="horizon", values="coverage_pct")
    .style.format("{:.0f} %"),
)
