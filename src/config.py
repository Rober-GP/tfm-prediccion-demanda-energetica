"""Configuración del proyecto y carga de credenciales.

Centraliza las rutas y las claves de API para que no aparezcan escritas
en los notebooks.

Uso desde un notebook:

    import sys
    sys.path.append("../src")
    from config import AEMET_API_KEY, DIR_DATOS, DIR_FIGURAS
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    _RAIZ = Path(__file__).resolve().parent.parent
    load_dotenv(_RAIZ / ".env")
except ImportError:  # python-dotenv no instalado
    _RAIZ = Path(__file__).resolve().parent.parent


# ── Rutas ────────────────────────────────────────────────────────────────────
DIR_RAIZ      = _RAIZ
DIR_DATOS     = _RAIZ / "datos"
DIR_FIGURAS   = _RAIZ / "figuras"
DIR_NOTEBOOKS = _RAIZ / "notebooks"

for _d in (DIR_DATOS, DIR_FIGURAS):
    _d.mkdir(exist_ok=True)


# ── Credenciales ─────────────────────────────────────────────────────────────
AEMET_API_KEY = os.getenv("AEMET_API_KEY", "")
ESIOS_TOKEN   = os.getenv("ESIOS_TOKEN", "")


# ── Parámetros del estudio ───────────────────────────────────────────────────
FECHA_INICIO = "2022-01-01"
FECHA_FIN    = "2024-12-31"

ESTACION_AEMET       = "3195"   # Madrid-Retiro
SUBDIVISION_FESTIVOS = "MD"     # Comunidad de Madrid

# API REData de REE
WIDGET_DEMANDA = "demanda-tiempo-real"   # 'evolucion' no admite time_trunc=hour
TIME_TRUNC     = "hour"
USAR_GEO       = True


def comprobar_credenciales(requiere_aemet: bool = True) -> bool:
    """Verifica que las claves necesarias estén configuradas.

    Devuelve True si todo está en orden; en caso contrario imprime
    instrucciones y devuelve False.
    """
    if requiere_aemet and not AEMET_API_KEY:
        print("Falta AEMET_API_KEY.")
        print("  1. Solicítala en https://opendata.aemet.es/centrodedescargas/altaUsuario")
        print("  2. cp .env.example .env")
        print("  3. Añade la clave en el archivo .env")
        return False
    return True


if __name__ == "__main__":
    print(f"Raíz del proyecto : {DIR_RAIZ}")
    print(f"Periodo           : {FECHA_INICIO} a {FECHA_FIN}")
    print(f"Estación AEMET    : {ESTACION_AEMET}")
    print(f"AEMET_API_KEY     : {'configurada' if AEMET_API_KEY else 'NO configurada'}")
    print(f"ESIOS_TOKEN       : {'configurado' if ESIOS_TOKEN else 'no configurado (opcional)'}")
