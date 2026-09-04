"""Página Pronósticos: emitir por temporada, registrar de forma
inmutable, verificar contra lo observado y exportar el boletín."""

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
from proteo.forecasts import registry
from proteo.forecasts.seasons import next_season
from proteo.models.sarimax import SARIMAXModel
from proteo.store import vintages

st.set_page_config(page_title="Pronósticos · Proteo", page_icon="🌊", layout="wide")

st.title("Pronósticos")
st.caption(
    "Emitir, registrar de forma inmutable y verificar cuando llegue el dato "
    "real. Una fila verificada no se toca nunca, ni con valores revisados."
)

PRICE_INDEX = "xm_precio_bolsa"
CONFIG_PATH = ROOT / "config" / "active_model.json"
FORECASTS_DIR = ROOT / "data" / "forecasts"

COLOR = {
    "obs": "#22303f", "modelo": "#1d4ed8",
    "banda": "rgba(29, 78, 216, 0.15)", "asumido": "#c2410c",
    "fuera": "#d94a3d", "pendiente": "#8a949e",
}

# --- Configuración activa ---------------------------------------------------
if not CONFIG_PATH.exists():
    st.info(
        "No hay configuración activa. Ve a la página **Entrenar**, ajusta el "
        "modelo y pulsa «Guardar como configuración activa»."
    )
    st.stop()

with open(CONFIG_PATH, encoding="utf-8") as fh:
    cfg = json.load(fh)

st.markdown(
    f"**Configuración activa:** SARIMAX{tuple(cfg['order'])}"
    f"{tuple(cfg['seasonal_order'])} · exógena **{cfg.get('exog') or 'ninguna'}** "
    f"rezago {cfg.get('lag', 0)} · objetivo "
    f"{'log' if cfg.get('log_target') else 'nivel'} · guardada {cfg.get('saved_at')}"
)

# --- Emitir -----------------------------------------------------------------
st.header("Emitir")

extend_h = st.checkbox("Extender a 6 pasos (más allá de la temporada)", value=True)

if st.button("Preparar pronóstico de la próxima temporada", type="primary"):
    with st.spinner("Entrenando con la configuración activa…"):
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

    st.subheader(f"Temporada objetivo: {prep['season']}")
    st.caption(
        f"Último dato observado: {prep['last_observed']}. Los meses previos a "
        "la temporada son pasos intermedios."
    )

    display = fc.copy()
    display["temporada"] = display["date"].map(
        lambda d: "objetivo" if d in season_months else "intermedio"
    )
    display["exógena"] = display["assumed_exog"].map(
        lambda a: "supuesta (persistencia)" if a else "observada"
    )
    st.dataframe(
        display[["date", "temporada", "mean", "lower", "upper", "exógena"]]
        .style.format({"mean": "{:.1f}", "lower": "{:.1f}", "upper": "{:.1f}"}),
        hide_index=True,
    )

    y_tail = prep["y_tail"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=y_tail.index, y=y_tail.values, mode="lines", name="Observado",
        line=dict(color=COLOR["obs"], width=1.4),
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([fc["date"], fc["date"][::-1]]),
        y=pd.concat([fc["upper"], fc["lower"][::-1]]),
        fill="toself", fillcolor=COLOR["banda"], line=dict(width=0),
        name="Intervalo", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fc["date"], y=fc["mean"], mode="lines+markers", name="Pronóstico",
        line=dict(color=COLOR["modelo"], width=2.2),
    ))
    sup = fc[fc["assumed_exog"]]
    if not sup.empty:
        fig.add_trace(go.Scatter(
            x=sup["date"], y=sup["mean"], mode="markers",
            name="Exógena supuesta",
            marker=dict(color=COLOR["asumido"], size=9, symbol="diamond"),
        ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Precio de bolsa (COP/kWh)",
        hovermode="x unified", height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30),
    )
    st.plotly_chart(fig, width="stretch")

    notes = st.text_input("Notas del pronóstico (contexto, supuestos, dudas)")
    if st.button("Confirmar y registrar"):
        forecast_id = registry.issue(
            fc,
            {**cfg, "vintages": prep["vintages"]},
            issued_at=date.today(),
            notes=notes,
        )
        del st.session_state["prepared"]
        st.success(f"Pronóstico registrado: **{forecast_id}**")
        st.rerun()

# --- Verificar --------------------------------------------------------------
st.header("Verificar")

pend = registry.pending()
st.caption(f"Filas pendientes: {len(pend)}")

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
                f"vintage de XM (llega hasta {actual.index.max().date()})."
            )
        else:
            st.success(f"{len(verified)} filas verificadas.")
            st.dataframe(
                verified[["forecast_id", "target_date", "mean", "actual",
                          "error", "inside_interval"]],
                hide_index=True,
            )

# --- Historial --------------------------------------------------------------
st.header("Historial")

full = registry.load()
if full.empty:
    st.info("Aún no se ha emitido ningún pronóstico.")
else:
    resumen = full.copy()
    resumen["estado"] = resumen["verified_at"].map(
        lambda v: "pendiente" if pd.isna(v) else "verificado"
    )
    st.dataframe(
        resumen[["forecast_id", "issued_at", "season_label", "model",
                 "target_date", "horizon", "mean", "actual", "error",
                 "inside_interval", "estado"]]
        .style.format({"mean": "{:.1f}", "actual": "{:.1f}", "error": "{:.1f}"},
                      na_rep="—"),
        hide_index=True,
    )

    price = vintages.load(PRICE_INDEX)
    observed = price.set_index("date")["value"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=observed.index[-60:], y=observed.iloc[-60:], mode="lines",
        name="Observado", line=dict(color=COLOR["obs"], width=1.2),
    ))
    for fid, group in full.groupby("forecast_id"):
        group = group.sort_values("target_date")
        verified_rows = group[group["verified_at"].notna()]
        if verified_rows.empty:
            color, estado = COLOR["pendiente"], "pendiente"
        elif (verified_rows["inside_interval"] == 0).any():
            color, estado = COLOR["fuera"], "con fallos"
        else:
            color, estado = COLOR["modelo"], "dentro"
        fig.add_trace(go.Scatter(
            x=pd.concat([group["target_date"], group["target_date"][::-1]]),
            y=pd.concat([group["upper"], group["lower"][::-1]]),
            fill="toself", fillcolor="rgba(138, 148, 158, 0.12)",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=group["target_date"], y=group["mean"], mode="lines+markers",
            name=f"{fid} ({estado})", line=dict(color=color, width=1.8),
        ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Precio de bolsa (COP/kWh)",
        hovermode="x unified", height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30),
    )
    st.plotly_chart(fig, width="stretch")

# --- Scorecard --------------------------------------------------------------
st.header("Scorecard")
card = registry.scorecard()
if card.empty:
    st.info("Sin filas verificadas todavía: el scorecard llegará con los datos.")
else:
    st.dataframe(
        card.style.format(
            {"mae": "{:.1f}", "rmse": "{:.1f}", "coverage_pct": "{:.0f} %"}
        ),
        hide_index=True,
    )

# --- Boletín ----------------------------------------------------------------
st.header("Boletín")

if full.empty:
    st.caption("Emite un pronóstico para poder exportar el boletín.")
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
                f"{'supuesta' if r['assumed_exog'] else 'observada'} |"
            )
        lines += [
            "",
            "## Supuestos",
            "",
            "- La exógena futura NO se pronostica: persistencia del último "
            "valor observado"
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
                f"Ninguno todavía. Primera verificación posible cuando XM "
                f"publique {first_pending.strftime('%Y-%m')}."
            )
        else:
            last_verified = verified_all.sort_values("verified_at").iloc[-1]
            lines.append(
                f"- {pd.Timestamp(last_verified['target_date']).date()}: "
                f"pronóstico {last_verified['mean']:.1f}, observado "
                f"{last_verified['actual']:.1f}, error "
                f"{last_verified['error']:+.1f} "
                f"({'dentro' if last_verified['inside_interval'] else 'fuera'} "
                "del intervalo)."
            )

        FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
        bulletin_path = FORECASTS_DIR / f"boletin_{season.replace(' ', '_')}.md"
        with open(bulletin_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        st.success(f"Boletín exportado: {bulletin_path.relative_to(ROOT)}")
        st.markdown("\n".join(lines))
