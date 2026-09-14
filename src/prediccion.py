"""
Lógica de predicción compartida entre el entrenamiento y la aplicación.

Mantener la construcción de variables en un único módulo evita el error más
habitual al desplegar un modelo: que las variables se generen de forma distinta
en entrenamiento y en producción (*training/serving skew*).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ── Configuración ────────────────────────────────────────────────────────────

HORIZONTE = 24          # horas que el modelo predice hacia delante
LAGS = [24, 25, 48, 168]
VENTANAS_MOVILES = [24, 168]

# Población por comunidad autónoma (INE, millones). Pondera el alcance real de
# cada festividad sobre la demanda peninsular.
POBLACION = {
    "AN": 8.63, "AR": 1.35, "AS": 1.01, "CB": 0.59, "CE": 0.08,
    "CL": 2.38, "CM": 2.10, "CN": 2.24, "CT": 8.01, "EX": 1.06,
    "GA": 2.70, "IB": 1.23, "MC": 1.57, "MD": 6.95, "ML": 0.09,
    "NC": 0.67, "PV": 2.22, "RI": 0.32, "VC": 5.32,
}
TOTAL_POBLACION = sum(POBLACION.values())


# ── Calendario ───────────────────────────────────────────────────────────────

def intensidad_festivos(anios) -> dict:
    """Devuelve {fecha: fracción de población con festivo}."""
    import holidays

    calendarios = {s: holidays.Spain(years=anios, subdiv=s) for s in POBLACION}
    fechas = {d for c in calendarios.values() for d in c}

    return {
        d: sum(p for s, p in POBLACION.items() if d in calendarios[s]) / TOTAL_POBLACION
        for d in fechas
    }


# ── Construcción de variables ────────────────────────────────────────────────

def construir_variables(serie: pd.Series,
                        meteo: pd.DataFrame | None = None,
                        intensidad: dict | None = None) -> pd.DataFrame:
    """Genera el conjunto de variables predictoras a partir de la serie histórica.

    Parameters
    ----------
    serie : pd.Series
        Demanda horaria indexada por fecha (sin zona horaria).
    meteo : pd.DataFrame, optional
        Columnas ``fecha``, ``tmed``, ``tmax``, ``tmin``.
    intensidad : dict, optional
        Salida de :func:`intensidad_festivos`. Se calcula si no se pasa.

    Returns
    -------
    pd.DataFrame con el mismo índice que ``serie``.
    """
    df = pd.DataFrame(index=serie.index)
    df["demanda_mw"] = serie.values

    # ── Desfases: solo iguales o superiores al horizonte ────────────────────
    for lag in LAGS:
        if lag < HORIZONTE:
            raise ValueError(f"lag_{lag}h es menor que el horizonte {HORIZONTE}")
        df[f"lag_{lag}h"] = serie.shift(lag)

    # ── Estadísticos móviles desplazados el horizonte completo ──────────────
    # La ventana debe cerrarse antes del instante de predicción.
    base = serie.shift(HORIZONTE)
    for v in VENTANAS_MOVILES:
        df[f"media{v}_h{HORIZONTE}"] = base.rolling(v).mean()
        df[f"std{v}_h{HORIZONTE}"]   = base.rolling(v).std()

    # ── Calendario ──────────────────────────────────────────────────────────
    idx = df.index
    df["hora"]    = idx.hour
    df["dia_sem"] = idx.dayofweek
    df["dia_mes"] = idx.day
    df["mes"]     = idx.month

    for col, periodo in [("hora", 24), ("dia_sem", 7), ("mes", 12)]:
        df[f"{col}_sin"] = np.sin(2 * np.pi * df[col] / periodo)
        df[f"{col}_cos"] = np.cos(2 * np.pi * df[col] / periodo)

    # ── Festivos ponderados por población ───────────────────────────────────
    if intensidad is None:
        intensidad = intensidad_festivos(range(idx.year.min(), idx.year.max() + 2))

    serie_int = pd.Series(intensidad)
    serie_int.index = pd.to_datetime(serie_int.index)

    fechas = pd.Series(idx.normalize(), index=idx)
    df["intensidad_festivo"]  = fechas.map(serie_int).fillna(0.0).astype(float)
    df["intensidad_vispera"]  = (fechas + pd.Timedelta(days=1)).map(serie_int).fillna(0.0)
    df["intensidad_post"]     = (fechas - pd.Timedelta(days=1)).map(serie_int).fillna(0.0)

    df["festivo_nacional"] = (df["intensidad_festivo"] >= 0.90).astype("int8")
    df["finde"]            = (df["dia_sem"] >= 5).astype("int8")
    df["laborable_efectivo"] = ((idx.dayofweek < 5).astype(float)
                                * (1 - df["intensidad_festivo"]))

    # ── Meteorología ────────────────────────────────────────────────────────
    if meteo is not None and len(meteo):
        m = meteo.copy()
        m["fecha"] = pd.to_datetime(m["fecha"]).dt.normalize()
        m = m.drop_duplicates("fecha").set_index("fecha")

        for c in ("tmed", "tmax", "tmin"):
            if c in m.columns:
                # Se interpolan las tres: si la previsión no alcanza el final
                # del horizonte, se prolonga el último valor conocido en lugar
                # de dejar nulos que impedirían predecir.
                df[c] = fechas.map(m[c]).interpolate(limit_direction="both")

        if "tmed" in df.columns:
            df["tmed_sq"]      = df["tmed"] ** 2
            df["grados_frio"]  = (18 - df["tmed"]).clip(lower=0)
            df["grados_calor"] = (df["tmed"] - 22).clip(lower=0)

    return df


def columnas_predictoras(df: pd.DataFrame) -> list[str]:
    """Columnas utilizables como entrada del modelo."""
    return [c for c in df.columns
            if c != "demanda_mw" and pd.api.types.is_numeric_dtype(df[c])]


# ── Persistencia del modelo ──────────────────────────────────────────────────

def guardar_modelo(modelo, columnas, metadatos, directorio) -> Path:
    """Serializa el modelo junto con sus columnas y metadatos."""
    import joblib

    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    joblib.dump(modelo, directorio / "modelo.joblib")

    info = {"columnas": list(columnas), "horizonte": HORIZONTE, **metadatos}
    (directorio / "modelo_info.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")

    return directorio


def cargar_modelo(directorio):
    """Devuelve (modelo, info). Lanza FileNotFoundError si no existe."""
    import joblib

    directorio = Path(directorio)
    ruta = directorio / "modelo.joblib"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encuentra {ruta}. Ejecuta antes notebooks/04_modelo_final.ipynb"
        )

    modelo = joblib.load(ruta)
    info = json.loads((directorio / "modelo_info.json").read_text(encoding="utf-8"))
    return modelo, info


# ── Predicción ───────────────────────────────────────────────────────────────

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS_ES = ["lunes", "martes", "miércoles", "jueves",
           "viernes", "sábado", "domingo"]


def fecha_es(ts: pd.Timestamp, con_dia=False) -> str:
    """Formatea una fecha en castellano (el locale del sistema no es fiable)."""
    texto = f"{ts.day} de {MESES_ES[ts.month - 1]}"
    return f"{DIAS_ES[ts.dayofweek]} {texto}" if con_dia else texto


def predecir(modelo, columnas, serie, meteo_futura=None, horas=24,
             intensidad=None) -> pd.DataFrame:
    """Predice las próximas ``horas`` a partir del final de ``serie``.

    El modelo está entrenado para un horizonte de 24 h. Para horizontes
    superiores se aplica un esquema **recursivo**: las predicciones del primer
    tramo se incorporan a la serie para calcular los desfases del siguiente.
    Esto permite llegar a 48 h a costa de acumular error, circunstancia que se
    señala en ``salida.attrs["recursivo"]``.

    Returns
    -------
    pd.DataFrame con ``demanda_prevista`` y, si hay datos, ``tmed``.
    """
    tramos = []
    serie_trabajo = serie.copy()
    restantes = horas
    n_pasos = 0

    while restantes > 0:
        paso = min(HORIZONTE, restantes)
        ultima = serie_trabajo.index[-1]
        futuro = pd.date_range(ultima + pd.Timedelta(hours=1),
                               periods=paso, freq="h")

        extendida = pd.concat([serie_trabajo, pd.Series(np.nan, index=futuro)])
        variables = construir_variables(extendida, meteo=meteo_futura,
                                        intensidad=intensidad)
        X = variables.loc[futuro, columnas]

        if X.isna().any().any():
            raise ValueError(
                "Faltan variables para predecir. Comprueba que la serie "
                "histórica cubre al menos 168 h antes del inicio."
            )

        pred = pd.Series(modelo.predict(X), index=futuro)
        tramos.append(pd.DataFrame({"demanda_prevista": pred.values,
                                    "tmed": variables.loc[futuro].get("tmed")},
                                   index=futuro))

        # Realimentar para el tramo siguiente
        serie_trabajo = pd.concat([serie_trabajo, pred])
        restantes -= paso
        n_pasos += 1

    salida = pd.concat(tramos)
    salida.attrs["recursivo"] = n_pasos > 1
    salida.attrs["n_pasos"] = n_pasos
    return salida


# ── Recomendaciones ──────────────────────────────────────────────────────────

def franjas_optimas(prediccion: pd.Series, n_horas=3, min_bloque=2):
    """Identifica los bloques horarios de menor demanda prevista.

    Returns
    -------
    list[dict] con ``inicio``, ``fin``, ``demanda_media`` y ``ahorro_pct``.
    """
    if len(prediccion) < min_bloque:
        return []

    media = prediccion.mean()
    orden = prediccion.sort_values().index[:n_horas]

    # Agrupar horas consecutivas en bloques
    bloques, actual = [], [orden[0]]
    for h in sorted(orden)[1:]:
        if (h - actual[-1]) == pd.Timedelta(hours=1):
            actual.append(h)
        else:
            bloques.append(actual)
            actual = [h]
    bloques.append(actual)

    resultado = []
    for b in bloques:
        valores = prediccion.loc[b]
        resultado.append({
            "inicio": b[0],
            "fin": b[-1] + pd.Timedelta(hours=1),
            "horas": len(b),
            "demanda_media": float(valores.mean()),
            "ahorro_pct": float((media - valores.mean()) / media * 100),
        })

    return sorted(resultado, key=lambda x: x["demanda_media"])


def redactar_recomendacion(prediccion: pd.Series, franjas: list) -> str:
    """Genera un texto explicativo para el usuario final."""
    if not franjas:
        return "No hay datos suficientes para generar una recomendación."

    mejor = franjas[0]
    pico_hora = prediccion.idxmax()

    dia = fecha_es(mejor["inicio"], con_dia=True)
    if mejor["horas"] > 1:
        cuando = (f"entre las {mejor['inicio']:%H:%M} y las {mejor['fin']:%H:%M} "
                  f"del {dia}")
    else:
        cuando = f"hacia las {mejor['inicio']:%H:%M} del {dia}"

    return (
        f"El momento más favorable para consumir es **{cuando}**, "
        f"con una demanda un {mejor['ahorro_pct']:.0f} % inferior a la media "
        f"del periodo.\n\n"
        f"Conviene evitar las **{pico_hora:%H:%M}**, cuando se espera el máximo "
        f"de demanda y, previsiblemente, el precio más alto."
    )
