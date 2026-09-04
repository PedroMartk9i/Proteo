"""Página Pronósticos: emitir por temporada, registrar de forma
inmutable, verificar contra lo observado y exportar el boletín."""

import json
import sys
from datetime import date
from pathlib import Path

# Permite importar ``proteo`` y ``app`` al correr desde la raíz del repo.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import components, theme
from app.theme import PALETTE, PLOTLY_CONFIG
from proteo.dataset import build_dataset, future_exog, inverse_transform
from proteo.forecasts import registry
from proteo.forecasts.seasons import next_season
from proteo.models.sarimax import SARIMAXModel
from proteo.store import vintages

st.set_page_config(page_title="Pronósticos · Proteo", layout="wide")
theme.inject_css()
theme.plotly_template()

st.title("Pronósticos")
st.markdown(
    '<p class="pt-help">Emitir, registrar de forma inmutable y verificar '
    "cuando llegue el dato real. Una fila verificada no se toca nunca, ni "
    "con valores revisados.</p>",
    unsafe_allow_html=True,
)

PRICE_INDEX = "xm_precio_bolsa"
CONFIG_PATH = ROOT / "config" / "active_model.json"
FORECASTS_DIR = ROOT / "data" / "forecasts"

STEP_EXOG = {True: "supuesta (persistencia)", False: "observada"}

# --- Configuración activa ---------------------------------------------------
if not CONFIG_PATH.exists():
    st.info(
        "No hay configuración activa. Ve a la página Entrenar, ajusta el "
        "modelo y pulsa Guardar como configuración activa."
    )
    st.stop()

with open(CONFIG_PATH, encoding="utf-8") as fh:
    cfg = json.load(fh)

saved_at = (
    date.fromisoformat(cfg["saved_at"]) if cfg.get("saved_at") else None
)
config_name = (
    f"SARIMAX{tuple(cfg['order'])}{tuple(cfg['seasonal_order'])} · "
    f"exógena {cfg.get('exog') or 'ninguna'} rezago {cfg.get('lag', 0)} · "
    f"objetivo {'log' if cfg.get('log_target') else 'nivel'}"
)
components.data_header(config_name, "configuración activa", saved_at)
train_vintages = ", ".join(
    f"{k} {v}" for k, v in cfg.get("vintages", {}).items()
)
st.markdown(
    f'<p class="pt-help">Vintages de entrenamiento: {train_vintages}.</p>',
    unsafe_allow_html=True,
)

# --- Emitir -----------------------------------------------------------------
components.section(
    "Emitir",
    help="Dos pasos: preparar el pronóstico de la próxima temporada y, "
    "cuando convenza, confirmar para escribirlo en el registro.",
)

extend_h = st.checkbox("Extender a 6 pasos (más allá de la temporada)", value=True)

if st.button("Preparar pronóstico de la próxima temporada"):
    with st.spinner("Entrenando con la configuración activa"):
        price_vintage = vintages.list_vintages(PRICE_INDEX)[-1]
        price = vintages.load(PRICE_INDEX, price_vintage)
        exog_index = cfg.get("exog")
        exog = exog_vintage = None
        if exog_index:
            exog_vintage = vintages.list_vintages(exog_index)[-1]
            exog = vintages.load(exog_index, exog_vintage)

        y, X = build_dataset(
            price, exog, lag=cfg.get("lag", 0),
            start=cfg.get("train_start", "2000-01-01"),
            log_target=cfg.get("log_target", False),
            add_squared=cfg.get("add_squared", False),
        )
        last_observed = y.index[-1].date()
        season, months = next_season(last_observed)
        h_season = (months[-1].year - last_observed.year) * 12 + (
            months[-1].month - last_observed.month
        )
        h = max(6, h_season) if extend_h else h_season

        model = SARIMAXModel(
            order=tuple(cfg["order"]), seasonal_order=tuple(cfg["seasonal_order"])
        ).fit(y, X)

        X_future = None
        assumed = [False] * h
        if exog is not None:
            ef = future_exog(
                exog, y.index[-1], h, cfg.get("lag", 0),
                add_squared=cfg.get("add_squared", False),
            )
            X_future = ef.drop(columns="assumed")
            assumed = ef["assumed"].tolist()

        fc = model.forecast(h, X_future=X_future, alpha=cfg.get("alpha", 0.2))
        for col in ("mean", "lower", "upper"):
            fc[col] = inverse_transform(fc[col], cfg.get("log_target", False))
        fc["assumed_exog"] = assumed

        st.session_state["prepared"] = {
            "fc": fc,
            "season": season,
            "season_months": [m.isoformat() for m in months],
            "last_observed": last_observed.isoformat(),
            "y_tail": y.iloc[-36:] if not cfg.get("log_target") else
                      inverse_transform(y.iloc[-36:], True),
            "vintages": {
                PRICE_INDEX: price_vintage.isoformat(),
                **({exog_index: exog_vintage.isoformat()} if exog_index else {}),
            },
        }

if "prepared" in st.session_state:
    prep = st.session_state["prepared"]
    fc = prep["fc"]
    season_months = set(pd.to_datetime(prep["season_months"]))

    components.section(
        f"Temporada objetivo: {prep['season']}",
        help=f"Último dato observado: {prep['last_observed']}. Los meses "
        "previos a la temporada son pasos intermedios; los posteriores, "
        "extendidos.",
    )

    def _membership(d) -> str:
        if d in season_months:
            return "objetivo"
        return "intermedio" if d < min(season_months) else "extendido"

    display = fc.copy()
    display["temporada"] = display["date"].map(_membership)
    display["exógena"] = display["assumed_exog"].map(STEP_EXOG.get)
    st.dataframe(
        display[["date", "temporada", "mean", "lower", "upper", "exógena"]],
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("fecha", format="YYYY-MM"),
            **{
                c: st.column_config.NumberColumn(c, format="%.1f")
                for c in ("mean", "lower", "upper")
            },
        },
    )

    y_tail = prep["y_tail"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=y_tail.index, y=y_tail.values, mode="lines", name="Observado",
        line=dict(color=PALETTE["linea"], width=1.4),
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([fc["date"], fc["date"][::-1]]),
        y=pd.concat([fc["upper"], fc["lower"][::-1]]),
        fill="toself", fillcolor=PALETTE["banda"], mode="none",
        name="Intervalo", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fc["date"], y=fc["mean"], mode="lines+markers", name="Pronóstico",
        line=dict(color=PALETTE["nino"], width=2.2, dash="dash"),
    ))
    sup = fc[fc["assumed_exog"]]
    if not sup.empty:
        fig.add_trace(go.Scatter(
            x=sup["date"], y=sup["mean"], mode="markers",
            name="Exógena supuesta (persistencia)",
            marker=dict(color=PALETTE["tinta"], size=9, symbol="diamond"),
        ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Precio de bolsa (COP/kWh)",
        height=380,
    )
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

    notes = st.text_input("Notas del pronóstico (contexto, supuestos, dudas)")
    if st.button("Confirmar y registrar", type="primary"):
        forecast_id = registry.issue(
            fc,
            {**cfg, "vintages": prep["vintages"]},
            issued_at=date.today(),
            notes=notes,
        )
        del st.session_state["prepared"]
        st.success(f"Pronóstico registrado: {forecast_id}")
        st.rerun()

# --- Verificar --------------------------------------------------------------
components.section("Verificar")

pend = registry.pending()
st.markdown(
    f'<p class="pt-help">Filas pendientes: {len(pend)}.</p>',
    unsafe_allow_html=True,
)

if st.button("Verificar pendientes"):
    if pend.empty:
        st.info("No hay pronósticos pendientes de verificar.")
    else:
        price = vintages.load(PRICE_INDEX)
        actual = price.set_index("date")["value"]
        verified = registry.verify(actual, date.today())
        if verified.empty:
            first_target = pend["target_date"].min()
            st.info(
                "Nada que verificar todavía: el primer mes objetivo "
                f"({pd.Timestamp(first_target).date()}) aún no existe en el "
                f"vintage de XM (llega hasta {actual.index.max().date()}). "
                "Descarga XM en Datos cuando publiquen el mes."
            )
        else:
            st.success(f"{len(verified)} filas verificadas.")
            st.dataframe(
                verified[["forecast_id", "target_date", "mean", "actual",
                          "error", "inside_interval"]],
                hide_index=True,
            )

# --- Historial --------------------------------------------------------------
components.section("Historial")

full = registry.load()
if full.empty:
    st.info(
        "No se ha emitido ningún pronóstico todavía. Usa Preparar y luego "
        "Confirmar y registrar."
    )
else:
    for fid, group in full.groupby("forecast_id"):
        is_verified = group["verified_at"].notna().any()
        estado = "verificado" if is_verified else "pendiente"
        season = group["season_label"].iloc[0]
        st.markdown(
            f'<div class="pt-datahead"><span class="pt-name">{fid}</span>'
            f"{components.status_led(is_verified)}"
            f'<span class="pt-stamp">{season} · {estado}</span></div>',
            unsafe_allow_html=True,
        )

    resumen = full.copy()
    resumen["estado"] = resumen["verified_at"].map(
        lambda v: "pendiente" if pd.isna(v) else "verificado"
    )
    st.dataframe(
        resumen[["forecast_id", "issued_at", "season_label", "model",
                 "target_date", "horizon", "mean", "actual", "error",
                 "inside_interval", "estado"]],
        hide_index=True,
        column_config={
            "target_date": st.column_config.DateColumn(
                "target_date", format="YYYY-MM"
            ),
            **{
                c: st.column_config.NumberColumn(c, format="%.1f")
                for c in ("mean", "actual", "error")
            },
        },
    )

    price = vintages.load(PRICE_INDEX)
    observed = price.set_index("date")["value"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=observed.index[-60:], y=observed.iloc[-60:], mode="lines",
        name="Observado", line=dict(color=PALETTE["linea"], width=1.2),
    ))
    # Código de color: teal = el real cayó dentro del intervalo,
    # naranja = al menos un paso quedó fuera, tinta = pendiente.
    for fid, group in full.groupby("forecast_id"):
        group = group.sort_values("target_date")
        verified_rows = group[group["verified_at"].notna()]
        if verified_rows.empty:
            color, band, estado = PALETTE["tinta"], PALETTE["banda_tinta"], "pendiente"
        elif (verified_rows["inside_interval"] == 0).any():
            color, band, estado = PALETTE["nino"], PALETTE["banda"], "fuera del intervalo"
        else:
            color, band, estado = PALETTE["nina"], PALETTE["banda_nina"], "dentro del intervalo"
        fig.add_trace(go.Scatter(
            x=pd.concat([group["target_date"], group["target_date"][::-1]]),
            y=pd.concat([group["upper"], group["lower"][::-1]]),
            fill="toself", fillcolor=band, mode="none",
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=group["target_date"], y=group["mean"], mode="lines+markers",
            name=f"{fid} · {estado}", line=dict(color=color, width=1.8),
        ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Precio de bolsa (COP/kWh)",
        height=420,
    )
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)

# --- Scorecard --------------------------------------------------------------
components.section("Scorecard")
card = registry.scorecard()
if card.empty:
    st.info(
        "Sin filas verificadas todavía: el scorecard se llena con la "
        "primera verificación."
    )
else:
    st.dataframe(
        card,
        hide_index=True,
        column_config={
            "mae": st.column_config.NumberColumn("mae", format="%.1f"),
            "rmse": st.column_config.NumberColumn("rmse", format="%.1f"),
            "coverage_pct": st.column_config.NumberColumn(
                "coverage_pct", format="%.0f %%"
            ),
        },
    )

# --- Boletín ----------------------------------------------------------------
components.section("Boletín")

if full.empty:
    st.markdown(
        '<p class="pt-help">Emite un pronóstico para poder exportar el '
        "boletín.</p>",
        unsafe_allow_html=True,
    )
else:
    last_id = full.sort_values("issued_at")["forecast_id"].iloc[-1]
    if st.button(f"Exportar boletín de {last_id}"):
        rows = registry.history(last_id)
        fcfg = registry.load_config(last_id)
        season = fcfg["season_label"]
        assumed_from = rows.loc[rows["assumed_exog"], "horizon"].min()

        lines = [
            f"# Boletín Proteo — pronóstico {season}",
            "",
            f"- **Emitido:** {fcfg['issued_at']}",
            f"- **forecast_id:** {last_id}",
            f"- **Modelo:** SARIMAX{tuple(fcfg['order'])}"
            f"{tuple(fcfg['seasonal_order'])} · exógena "
            f"{fcfg.get('exog') or 'ninguna'} rezago {fcfg.get('lag', 0)} · "
            f"objetivo {'log' if fcfg.get('log_target') else 'nivel'}",
            "- **Vintages usados:** "
            + ", ".join(f"{k}: {v}" for k, v in fcfg.get("vintages", {}).items()),
            f"- **Notas:** {fcfg.get('notes') or '(sin notas)'}",
            "",
            f"## Pronóstico (COP/kWh, intervalo {int((1 - fcfg.get('alpha', 0.2)) * 100)} %)",
            "",
            "| Fecha | Horizonte | Temporada | Media | Inferior | Superior | Exógena |",
            "|---|---|---|---|---|---|---|",
        ]
        first_target = pd.Timestamp(rows["target_date"].iloc[0])
        last_observed = (first_target - pd.DateOffset(months=1)).date()
        _, season_months = next_season(last_observed)
        season_set = {pd.Timestamp(m) for m in season_months}
        for _, r in rows.iterrows():
            target = pd.Timestamp(r["target_date"])
            if target in season_set:
                membership = "**objetivo**"
            elif target < min(season_set):
                membership = "intermedio"
            else:
                membership = "extendido"
            lines.append(
                f"| {target.date()} | {int(r['horizon'])} | "
                f"{membership} | {r['mean']:.1f} | {r['lower']:.1f} | "
                f"{r['upper']:.1f} | "
                f"{STEP_EXOG[bool(r['assumed_exog'])]} |"
            )
        lines += [
            "",
            "## Supuestos",
            "",
            "- La exógena futura NO se pronostica: supuesta (persistencia) "
            "del último valor observado"
            + (f" a partir del paso {int(assumed_from)}." if pd.notna(assumed_from)
               else " (no fue necesaria: todos los pasos usan valores observados)."),
            "- Pronóstico emitido con el vintage más reciente de cada serie "
            "(ver arriba); NOAA puede revisar valores hacia atrás.",
            "",
            "## Último resultado verificado",
            "",
        ]
        verified_all = full[full["verified_at"].notna()]
        if verified_all.empty:
            first_pending = pd.Timestamp(full["target_date"].min()).date()
            lines.append(
                "Ninguno todavía: todo el registro está pendiente. Primera "
                "verificación posible cuando XM publique "
                f"{first_pending.strftime('%Y-%m')} (Datos → Descargar XM → "
                "Pronósticos → Verificar pendientes)."
            )
        else:
            last_verified = verified_all.sort_values("verified_at").iloc[-1]
            estado = (
                "dentro del intervalo" if last_verified["inside_interval"]
                else "fuera del intervalo"
            )
            lines.append(
                f"- {pd.Timestamp(last_verified['target_date']).date()}: "
                f"pronóstico {last_verified['mean']:.1f}, observado "
                f"{last_verified['actual']:.1f}, error "
                f"{last_verified['error']:+.1f} ({estado})."
            )

        FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
        bulletin_path = FORECASTS_DIR / f"boletin_{season.replace(' ', '_')}.md"
        with open(bulletin_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        st.success(f"Boletín exportado: {bulletin_path.relative_to(ROOT)}")
        st.markdown("\n".join(lines))
