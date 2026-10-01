"""
Aplicación web de predicción de demanda energética.

Ejecutar con:   streamlit run app.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ / "src"))

from datos import cargar_contexto                                 # noqa: E402
from prediccion import (cargar_modelo, predecir, franjas_optimas,  # noqa: E402
                        redactar_recomendacion, fecha_es)

# ── Configuración de la página ───────────────────────────────────────────────

st.set_page_config(
    page_title="Predicción de demanda energética",
    page_icon="⚡",
    layout="wide",
)

COLOR_PRINCIPAL = "#2E5C8A"
COLOR_BUENO     = "#55A868"
COLOR_MALO      = "#C44E52"


# ── Carga de datos con caché ─────────────────────────────────────────────────

@st.cache_resource
def _cargar_modelo():
    return cargar_modelo(RAIZ / "modelos")


@st.cache_data(ttl=1800, show_spinner=False)
def _cargar_datos(dias):
    return cargar_contexto(dias_historico=dias)


# ── Encabezado ───────────────────────────────────────────────────────────────

st.title("⚡ Predicción de demanda energética")
st.caption(
    "Previsión de la demanda eléctrica peninsular y recomendación de las "
    "franjas horarias más favorables para el consumo doméstico."
)

# ── Barra lateral ────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuración")

    horizonte = st.radio(
        "Horizonte de predicción",
        [24, 48],
        format_func=lambda h: f"{h} horas",
        help="Más allá de 24 h la predicción es recursiva y el error aumenta.",
    )

    dias_hist = st.slider("Días de histórico a mostrar", 3, 30, 7)

    if st.button("Actualizar datos", width='stretch'):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(
        "**Fuentes**  \n"
        "Demanda y precio: Red Eléctrica (REData)  \n"
        "Meteorología: AEMET OpenData"
    )

# ── Obtención de datos ───────────────────────────────────────────────────────

try:
    modelo, info = _cargar_modelo()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

with st.spinner("Obteniendo datos de Red Eléctrica y AEMET…"):
    try:
        ctx = _cargar_datos(max(dias_hist, 15))
    except Exception as e:
        st.error(f"No se han podido obtener los datos: {e}")
        st.info("Comprueba tu conexión y vuelve a intentarlo en unos minutos.")
        st.stop()

serie   = ctx["serie"]
meteo   = ctx["meteo"]
precio  = ctx["precio"]

for aviso in ctx["avisos"]:
    st.warning(aviso, icon="⚠️")

if len(serie) < 168:
    st.error(
        f"Solo hay {len(serie)} horas de histórico y se necesitan al menos 168 "
        "para calcular los desfases semanales."
    )
    st.stop()

# ── Predicción ───────────────────────────────────────────────────────────────

try:
    pred = predecir(modelo, info["columnas"], serie,
                    meteo_futura=meteo, horas=horizonte)
except Exception as e:
    st.error(f"Error al generar la predicción: {e}")
    st.stop()

demanda_prevista = pred["demanda_prevista"]
franjas = franjas_optimas(demanda_prevista, n_horas=4)

# ── Indicadores ──────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)

ultimo = serie.iloc[-1]
col1.metric(
    "Demanda actual",
    f"{ultimo:,.0f} MW",
    help=f"Último dato disponible: {serie.index[-1]:%d/%m %H:%M}",
)

pico = demanda_prevista.max()
col2.metric(
    "Pico previsto",
    f"{pico:,.0f} MW",
    f"{(pico - ultimo) / ultimo * 100:+.1f} %",
    delta_color="inverse",
)

valle = demanda_prevista.min()
col3.metric(
    "Mínimo previsto",
    f"{valle:,.0f} MW",
    f"{(valle - ultimo) / ultimo * 100:+.1f} %",
    delta_color="inverse",
)

if franjas:
    mejor = franjas[0]
    col4.metric(
        "Mejor franja",
        f"{mejor['inicio']:%H:%M}",
        f"−{mejor['ahorro_pct']:.0f} % vs media",
        delta_color="normal",
    )

# ── Recomendación ────────────────────────────────────────────────────────────

st.subheader("Recomendación")
st.info(redactar_recomendacion(demanda_prevista, franjas), icon="💡")

if pred.attrs.get("recursivo"):
    st.caption(
        "Las horas posteriores a la 24 se obtienen de forma recursiva, "
        "realimentando las predicciones anteriores. Su error es mayor."
    )

# ── Gráfico principal ────────────────────────────────────────────────────────

st.subheader("Demanda prevista")

historico = serie.iloc[-dias_hist * 24:]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=historico.index, y=historico.values,
    name="Histórico", mode="lines",
    line=dict(color="#888780", width=1.5),
))

fig.add_trace(go.Scatter(
    x=demanda_prevista.index, y=demanda_prevista.values,
    name="Predicción", mode="lines",
    line=dict(color=COLOR_PRINCIPAL, width=2.5),
))

# Sombrear las franjas recomendadas
for f in franjas[:2]:
    fig.add_vrect(
        x0=f["inicio"], x1=f["fin"],
        fillcolor=COLOR_BUENO, opacity=0.18, line_width=0,
        annotation_text="franja favorable",
        annotation_position="top left",
        annotation_font_size=10,
    )

fig.add_vline(x=serie.index[-1], line_dash="dot",
              line_color="#666666", line_width=1)

fig.update_layout(
    height=430,
    hovermode="x unified",
    margin=dict(l=10, r=10, t=30, b=10),
    yaxis_title="MW",
    xaxis_title=None,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    plot_bgcolor="rgba(0,0,0,0)",
)
fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")

st.plotly_chart(fig, width='stretch')

# ── Detalle en dos columnas ──────────────────────────────────────────────────

izda, dcha = st.columns([3, 2])

with izda:
    st.subheader("Franjas ordenadas por demanda")

    tabla = pd.DataFrame({
        "Hora": demanda_prevista.index.strftime("%d/%m %H:%M"),
        "Demanda (MW)": demanda_prevista.values.round(0),
        "Frente a la media": (
            (demanda_prevista.values - demanda_prevista.mean())
            / demanda_prevista.mean() * 100
        ).round(1),
    })

    if len(precio):
        comunes = demanda_prevista.index.intersection(precio.index)
        if len(comunes):
            tabla["Precio (€/MWh)"] = (
                precio.reindex(demanda_prevista.index).values.round(1)
            )

    st.dataframe(
        tabla.sort_values("Demanda (MW)").head(12),
        width='stretch', hide_index=True,
        column_config={
            "Frente a la media": st.column_config.NumberColumn(format="%+.1f %%"),
        },
    )
    st.caption("Las doce horas de menor demanda prevista.")

with dcha:
    st.subheader("Contexto meteorológico")

    if "tmed" in pred.columns and pred["tmed"].notna().any():
        temp = pred["tmed"].dropna()
        st.metric("Temperatura media prevista", f"{temp.mean():.1f} °C")

        ft = go.Figure()
        ft.add_trace(go.Scatter(
            x=temp.index, y=temp.values, mode="lines",
            line=dict(color="#DD8452", width=2), name="Temperatura",
        ))
        ft.update_layout(
            height=200, margin=dict(l=10, r=10, t=10, b=10),
            yaxis_title="°C", showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(ft, width='stretch')

        st.caption(f"Origen: {ctx['origen_meteo']}.")
    else:
        st.info("Sin datos meteorológicos disponibles.")

    if franjas:
        st.markdown("**Bloques recomendados**")
        for f in franjas[:3]:
            st.markdown(
                f"- {fecha_es(f['inicio'])}, de las {f['inicio']:%H:%M} "
                f"a las {f['fin']:%H:%M} "
                f"(−{f['ahorro_pct']:.0f} %)"
            )

# ── Metodología ──────────────────────────────────────────────────────────────

with st.expander("Sobre el modelo y sus limitaciones"):
    st.markdown(f"""
**Modelo empleado:** {info.get('modelo', 'no especificado')}

**Variables:** {len(info['columnas'])} predictores, entre ellos desfases de la
propia demanda (24, 25, 48 y 168 horas), codificación cíclica del calendario,
intensidad de festivo ponderada por población y variables de temperatura.

**Horizonte nativo:** {info['horizonte']} horas. Las predicciones más allá se
generan de forma recursiva.

**Comprobación sobre el último mes de datos (bloque continuo de 30 días):**
""")

    metricas = {k: v for k, v in info.items()
                if k in ("mape", "mae", "rmse", "mape_festivos")}
    if metricas:
        st.json(metricas)

    st.markdown("""
**Limitaciones**

* La temperatura procede de la previsión de AEMET para Madrid, que se emplea
  como aproximación de las condiciones peninsulares.
* El modelo no incorpora información sobre generación renovable ni sobre
  incidencias de la red.
* Las franjas de menor demanda son un indicador orientativo del precio, no el
  precio contratado, que depende de la comercializadora y del peaje aplicable.
""")

st.divider()
st.caption(
    "Trabajo Fin de Máster — Máster en Big Data y Ciencia de Datos  ·  "
    "Datos de Red Eléctrica de España y AEMET"
)
