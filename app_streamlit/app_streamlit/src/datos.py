"""
Acceso a datos en tiempo real para la aplicación.

Tres fuentes, todas de acceso abierto:

* **Demanda**   REData de Red Eléctrica (sin credenciales)
* **Precio**    REData, categoría de mercados (sin credenciales)
* **Meteorología** AEMET OpenData, predicción horaria municipal (requiere clave)
"""

from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd
import requests

# ── Constantes ───────────────────────────────────────────────────────────────

URL_REDATA = "https://apidatos.ree.es/es/datos"

# Algunos servicios rechazan el agente de usuario por defecto de la librería
# requests. Se identifica la petición como procedente de un navegador.
CABECERAS = {
    "Accept": "application/json",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "es-ES,es;q=0.9",
}
MUNICIPIO_MADRID = "28079"          # código INE
TIMEOUT = 30


# ── Demanda ──────────────────────────────────────────────────────────────────

def _peticion_demanda(inicio, fin, reintentos=3):
    """Una sola petición al widget de demanda. Devuelve DataFrame (puede ir vacío)."""
    url = f"{URL_REDATA}/demanda/demanda-tiempo-real"
    # Los parámetros geográficos (geo_trunc, geo_limit, geo_ids) provocan un
    # error 502 del servidor en este widget, aun cuando la petición es correcta
    # por lo demás. Sin ellos el servicio responde con normalidad y devuelve la
    # demanda peninsular, que es la serie buscada.
    params = {
        "start_date": f"{inicio}T00:00",
        "end_date":   f"{fin}T23:59",
        "time_trunc": "hour",
    }

    ultimo_error = None
    for intento in range(reintentos):
        try:
            r = requests.get(url, params=params,
                             headers=CABECERAS, timeout=TIMEOUT)
            r.raise_for_status()

            valores = r.json()["included"][0]["attributes"]["values"]
            if not valores:
                return pd.DataFrame(columns=["datetime", "demanda_mw"])

            df = pd.DataFrame(valores)
            df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
            return df.rename(columns={"value": "demanda_mw"})[["datetime", "demanda_mw"]]

        except requests.HTTPError as e:
            # Se conserva el código de estado y el motivo: un 403 (acceso
            # denegado), un 429 (exceso de peticiones) y un 502 (error del
            # servidor) exigen actuaciones distintas, y un mensaje genérico
            # impide distinguirlos.
            resp = e.response
            detalle = ""
            if resp is not None:
                try:
                    cuerpo = resp.json()
                    errores = cuerpo.get("errors", [])
                    if errores:
                        detalle = errores[0].get("detail") or errores[0].get("title", "")
                except Exception:
                    detalle = resp.text[:120].replace("\n", " ")
                ultimo_error = RuntimeError(
                    f"HTTP {resp.status_code}"
                    + (f" — {detalle}" if detalle else ""))
            else:
                ultimo_error = e
            time.sleep(2 * (intento + 1))

        except Exception as e:
            ultimo_error = RuntimeError(f"{type(e).__name__}: {e}")
            time.sleep(2 * (intento + 1))

    raise ultimo_error


def descargar_demanda(inicio, fin, dias_por_bloque=7) -> pd.DataFrame:
    """Demanda peninsular horaria desde REData.

    El widget ``evolucion`` no admite ``time_trunc=hour``; se emplea
    ``demanda-tiempo-real``, cuya resolución nativa es de 10 minutos, y se
    reagrega a frecuencia horaria.

    La petición se trocea en bloques de una semana: el widget publica con
    resolución de cinco minutos (288 registros diarios) y las peticiones muy
    extensas resultan lentas o son rechazadas.
    """
    fechas = pd.date_range(inicio, fin, freq=f"{dias_por_bloque}D")
    if fechas[-1] < pd.Timestamp(fin):
        fechas = fechas.append(pd.DatetimeIndex([pd.Timestamp(fin)]))

    trozos, fallos = [], []

    for i in range(len(fechas) - 1):
        ini_b = fechas[i].strftime("%Y-%m-%d")
        fin_b = (fechas[i + 1] - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if fin_b < ini_b:
            fin_b = ini_b
        try:
            trozos.append(_peticion_demanda(ini_b, fin_b))
        except Exception as e:
            fallos.append(f"{ini_b}: {e}")
        time.sleep(0.5)

    # Último bloque hasta la fecha final incluida
    try:
        trozos.append(_peticion_demanda(fechas[-1].strftime("%Y-%m-%d"), fin))
    except Exception as e:
        fallos.append(f"{fechas[-1].date()}: {e}")

    trozos = [t for t in trozos if len(t)]

    if not trozos:
        raise RuntimeError(
            "REData no ha devuelto datos en ninguno de los bloques solicitados. "
            f"Errores: {'; '.join(fallos) if fallos else 'respuestas vacías'}"
        )

    df = (pd.concat(trozos, ignore_index=True)
            .drop_duplicates("datetime")
            .sort_values("datetime"))

    salida = (df.set_index("datetime")
                .resample("h")["demanda_mw"].mean()
                .dropna().reset_index())

    salida.attrs["bloques_fallidos"] = fallos
    return salida


def descargar_precio_pvpc(inicio, fin, reintentos=3) -> pd.DataFrame:
    """Precio horario del mercado desde REData.

    Devuelve un DataFrame vacío si la fuente no responde: el precio es
    información complementaria y su ausencia no debe impedir la predicción.
    """
    url = f"{URL_REDATA}/mercados/precios-mercados-tiempo-real"
    params = {
        "start_date": f"{inicio}T00:00",
        "end_date":   f"{fin}T23:59",
        "time_trunc": "hour",
    }

    for intento in range(reintentos):
        try:
            r = requests.get(url, params=params,
                             headers=CABECERAS, timeout=TIMEOUT)
            r.raise_for_status()

            bloques = r.json().get("included", [])
            if not bloques:
                return pd.DataFrame(columns=["datetime", "precio"])

            valores = bloques[0]["attributes"]["values"]
            df = pd.DataFrame(valores)
            df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
            return df.rename(columns={"value": "precio"})[["datetime", "precio"]]

        except Exception:
            if intento == reintentos - 1:
                return pd.DataFrame(columns=["datetime", "precio"])
            time.sleep(2 * (intento + 1))


# ── Meteorología ─────────────────────────────────────────────────────────────

def prevision_aemet(api_key=None, municipio=MUNICIPIO_MADRID) -> pd.DataFrame:
    """Previsión horaria de temperatura para las próximas 48 h.

    AEMET responde en dos pasos: la primera petición devuelve una URL temporal
    y la segunda los datos. Se agregan a valores diarios porque el modelo se
    entrenó con temperatura diaria.

    Returns
    -------
    DataFrame con ``fecha``, ``tmed``, ``tmax``, ``tmin``. Vacío si falla.
    """
    api_key = api_key or os.getenv("AEMET_API_KEY", "")
    if not api_key:
        return pd.DataFrame(columns=["fecha", "tmed", "tmax", "tmin"])

    base = "https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio"
    url = f"{base}/horaria/{municipio}"

    try:
        r1 = requests.get(url, params={"api_key": api_key}, timeout=TIMEOUT)
        r1.raise_for_status()
        meta = r1.json()
        if meta.get("estado") != 200:
            return pd.DataFrame(columns=["fecha", "tmed", "tmax", "tmin"])

        r2 = requests.get(meta["datos"], timeout=TIMEOUT)
        r2.encoding = "ISO-8859-15"          # AEMET no sirve UTF-8
        datos = r2.json()

        filas = []
        for dia in datos[0].get("prediccion", {}).get("dia", []):
            fecha = pd.to_datetime(dia["fecha"]).normalize()
            for t in dia.get("temperatura", []):
                filas.append({"fecha": fecha,
                              "hora": int(t["periodo"]),
                              "temp": float(t["value"])})

        if not filas:
            return pd.DataFrame(columns=["fecha", "tmed", "tmax", "tmin"])

        horario = pd.DataFrame(filas)
        return (horario.groupby("fecha")["temp"]
                       .agg(tmed="mean", tmax="max", tmin="min")
                       .reset_index())

    except Exception:
        return pd.DataFrame(columns=["fecha", "tmed", "tmax", "tmin"])


def meteo_climatologica(fechas) -> pd.DataFrame:
    """Temperatura estimada a partir del ciclo anual.

    Alternativa cuando AEMET no está disponible. Es una aproximación burda y
    debe advertirse al usuario cuando se emplea.
    """
    fechas = pd.to_datetime(pd.Index(fechas)).normalize().unique()
    dia_anio = pd.Index(fechas).dayofyear

    # Ciclo sinusoidal ajustado al clima de Madrid: mínimo en enero, máximo en julio
    tmed = 14.5 - 9.5 * np.cos(2 * np.pi * (dia_anio - 20) / 365.25)

    return pd.DataFrame({
        "fecha": fechas,
        "tmed": tmed,
        "tmax": tmed + 7.5,
        "tmin": tmed - 6.0,
    })


# ── Carga combinada ──────────────────────────────────────────────────────────

def cargar_contexto(dias_historico=30, api_key=None):
    """Reúne todo lo necesario para generar una predicción.

    Returns
    -------
    dict con ``serie``, ``meteo``, ``precio``, ``origen_meteo`` y ``avisos``.
    """
    avisos = []
    hoy = pd.Timestamp.now().normalize()
    inicio = (hoy - pd.Timedelta(days=dias_historico)).strftime("%Y-%m-%d")
    fin = hoy.strftime("%Y-%m-%d")

    # Demanda: imprescindible
    demanda = descargar_demanda(inicio, fin)
    if demanda.empty:
        raise RuntimeError("No se han podido obtener datos de demanda de REE.")

    fallidos = demanda.attrs.get("bloques_fallidos", [])
    if fallidos:
        avisos.append(
            f"REData no ha respondido en {len(fallidos)} de los bloques "
            "solicitados. La serie puede tener huecos."
        )

    serie = (demanda.set_index("datetime")["demanda_mw"]
                    .tz_convert("Europe/Madrid").tz_localize(None)
                    .sort_index())

    if len(serie) < 200:
        avisos.append(
            f"Solo se han recuperado {len(serie)} horas de histórico. "
            "El modelo necesita al menos 168 h para calcular los desfases."
        )

    # Meteorología: preferente AEMET, alternativa climatológica
    meteo = prevision_aemet(api_key)
    origen = "AEMET"
    if meteo.empty:
        futuras = pd.date_range(hoy, periods=4, freq="D")
        meteo = meteo_climatologica(list(serie.index) + list(futuras))
        origen = "climatología"
        avisos.append(
            "Sin previsión de AEMET. Se emplea una estimación a partir del "
            "ciclo anual, menos precisa."
        )

    # Precio: complementario
    precio = descargar_precio_pvpc(fin, (hoy + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    if not precio.empty:
        precio = precio.set_index("datetime")["precio"] \
                       .tz_convert("Europe/Madrid").tz_localize(None)
    else:
        precio = pd.Series(dtype=float)
        avisos.append("No hay datos de precio disponibles en este momento.")

    return {"serie": serie, "meteo": meteo, "precio": precio,
            "origen_meteo": origen, "avisos": avisos}
