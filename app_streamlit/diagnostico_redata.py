"""
Diagnóstico de la conexión con la API REData de Red Eléctrica.

Ejecutar desde la raíz del proyecto:

    python diagnostico_redata.py

Prueba varias combinaciones y muestra el código de estado y el cuerpo de la
respuesta, información que la aplicación estaba ocultando.
"""

import json
from datetime import date, timedelta

import requests

BASE = "https://apidatos.ree.es/es/datos"
TIMEOUT = 30

# Cabeceras de navegador: algunas APIs rechazan el agente por defecto de requests
CABECERAS_NAVEGADOR = {
    "Accept": "application/json",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "es-ES,es;q=0.9",
}

CABECERAS_SIMPLES = {"Accept": "application/json"}


def separador(titulo):
    print("\n" + "=" * 74)
    print(f"  {titulo}")
    print("=" * 74)


def probar(nombre, url, params, cabeceras):
    """Ejecuta una petición y describe el resultado con detalle."""
    print(f"\n▸ {nombre}")
    try:
        r = requests.get(url, params=params, headers=cabeceras, timeout=TIMEOUT)
    except Exception as e:
        print(f"   FALLO DE RED: {type(e).__name__}: {e}")
        return None

    print(f"   HTTP {r.status_code}")

    if r.status_code != 200:
        # Aquí está la información que la aplicación no mostraba
        cuerpo = r.text[:400].replace("\n", " ")
        print(f"   Respuesta: {cuerpo}")
        try:
            err = r.json()
            if "errors" in err:
                for e in err["errors"][:2]:
                    print(f"   -> {e.get('title', '')}: {e.get('detail', '')}")
        except Exception:
            pass
        return None

    try:
        datos = r.json()
        incluidos = datos.get("included", [])
        if not incluidos:
            print("   200 pero sin bloque 'included' (respuesta vacía)")
            return None
        valores = incluidos[0]["attributes"]["values"]
        print(f"   OK — {len(valores)} valores")
        if valores:
            print(f"   primero: {valores[0]['datetime']}  =  {valores[0]['value']}")
            print(f"   último : {valores[-1]['datetime']} =  {valores[-1]['value']}")
        return valores
    except Exception as e:
        print(f"   200 pero estructura inesperada: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
hoy = date.today()
ayer = hoy - timedelta(days=1)
hace_semana = hoy - timedelta(days=7)

print(f"Fecha del sistema: {hoy}")
print(f"requests {requests.__version__}")

# ── 1. La petición exacta que falla en la aplicación ──────────────────────
separador("1. La petición que emplea la aplicación")

probar(
    "demanda-tiempo-real, 5 días, con geo, cabecera simple",
    f"{BASE}/demanda/demanda-tiempo-real",
    {"start_date": f"{hace_semana}T00:00",
     "end_date":   f"{ayer}T23:59",
     "time_trunc": "hour",
     "geo_trunc":  "electric_system",
     "geo_limit":  "peninsular",
     "geo_ids":    8741},
    CABECERAS_SIMPLES,
)

# ── 2. ¿Es cuestión del User-Agent? ──────────────────────────────────────
separador("2. ¿Influye la cabecera User-Agent?")

probar(
    "misma petición, con cabeceras de navegador",
    f"{BASE}/demanda/demanda-tiempo-real",
    {"start_date": f"{hace_semana}T00:00",
     "end_date":   f"{ayer}T23:59",
     "time_trunc": "hour",
     "geo_trunc":  "electric_system",
     "geo_limit":  "peninsular",
     "geo_ids":    8741},
    CABECERAS_NAVEGADOR,
)

# ── 3. ¿Son los parámetros geográficos? ──────────────────────────────────
separador("3. ¿Estorban los parámetros geográficos?")

probar(
    "sin geo_trunc / geo_limit / geo_ids",
    f"{BASE}/demanda/demanda-tiempo-real",
    {"start_date": f"{hace_semana}T00:00",
     "end_date":   f"{ayer}T23:59",
     "time_trunc": "hour"},
    CABECERAS_NAVEGADOR,
)

# ── 4. ¿Es el rango de fechas? ───────────────────────────────────────────
separador("4. ¿Influye la amplitud del rango?")

for etiqueta, ini, fin in [
    ("un solo día (ayer)",        ayer,  ayer),
    ("dos días",                  hoy - timedelta(days=2), ayer),
    ("hoy mismo",                 hoy,   hoy),
]:
    probar(
        etiqueta,
        f"{BASE}/demanda/demanda-tiempo-real",
        {"start_date": f"{ini}T00:00", "end_date": f"{fin}T23:59",
         "time_trunc": "hour"},
        CABECERAS_NAVEGADOR,
    )

# ── 5. ¿Funciona con datos antiguos? ─────────────────────────────────────
separador("5. ¿Funciona con fechas del histórico?")

probar(
    "un día de 2024 (el notebook 01 sí lo descargó)",
    f"{BASE}/demanda/demanda-tiempo-real",
    {"start_date": "2024-06-10T00:00", "end_date": "2024-06-10T23:59",
     "time_trunc": "hour"},
    CABECERAS_NAVEGADOR,
)

# ── 6. Otros widgets ─────────────────────────────────────────────────────
separador("6. ¿Responden otros widgets?")

probar(
    "demanda/evolucion con granularidad diaria",
    f"{BASE}/demanda/evolucion",
    {"start_date": f"{hace_semana}T00:00", "end_date": f"{ayer}T23:59",
     "time_trunc": "day"},
    CABECERAS_NAVEGADOR,
)

probar(
    "mercados/precios-mercados-tiempo-real",
    f"{BASE}/mercados/precios-mercados-tiempo-real",
    {"start_date": f"{ayer}T00:00", "end_date": f"{ayer}T23:59",
     "time_trunc": "hour"},
    CABECERAS_NAVEGADOR,
)

# ── 7. Conectividad general ──────────────────────────────────────────────
separador("7. Conectividad general")

for nombre, url in [("apidatos.ree.es (raíz)", "https://apidatos.ree.es/"),
                    ("www.ree.es", "https://www.ree.es/")]:
    try:
        r = requests.get(url, headers=CABECERAS_NAVEGADOR, timeout=15)
        print(f"▸ {nombre}: HTTP {r.status_code}")
    except Exception as e:
        print(f"▸ {nombre}: {type(e).__name__}: {e}")

separador("FIN")
print("""
Cómo leer el resultado:

  Si la prueba 2 funciona y la 1 no  -> es el User-Agent
  Si la 3 funciona y la 1 no         -> estorban los parámetros geográficos
  Si la 4 funciona y la 1 no         -> es la amplitud del rango
  Si la 5 funciona y las demás no    -> el servicio no sirve fechas recientes
  Si todas dan 403                   -> tu IP está bloqueada o hay un proxy
  Si todas dan 429                   -> límite de peticiones; espera un rato
  Si la 7 también falla              -> es cortafuegos, red o proxy local
""")
