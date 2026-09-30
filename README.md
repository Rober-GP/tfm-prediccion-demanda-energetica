# Predicción de demanda energética mediante Machine Learning y datos abiertos

Trabajo Fin de Máster — Máster en Big Data y Ciencia de Datos

Sistema de predicción de la demanda eléctrica peninsular española a partir de
fuentes de datos abiertas, con una aplicación web que traduce las previsiones en
recomendaciones para el consumidor doméstico acogido a la tarifa PVPC.

\---

## Objetivo

Construir un pipeline completo que abarque desde la ingesta y el tratamiento de
los datos hasta el despliegue de una aplicación funcional, siguiendo una
progresión metodológica que parte de modelos estadísticos clásicos y escala
hacia técnicas de aprendizaje automático.

**Objetivos específicos**

1. Caracterizar el comportamiento histórico de la demanda mediante análisis
exploratorio y análisis espectral.
2. Incorporar variables exógenas: meteorología y calendario laboral.
3. Comparar tres familias de modelos sobre el mismo conjunto de test.
4. Evaluar con métricas de entrenamiento y producción para controlar el
sobreajuste.
5. Desplegar el modelo ganador en un dashboard accesible públicamente.

\---

## Fuentes de datos

|Fuente|Datos|Acceso|
|-|-|-|
|[REE — API REData](https://www.ree.es/es/apidatos)|Demanda eléctrica peninsular horaria|Libre, sin credenciales|
|[AEMET OpenData](https://opendata.aemet.es/)|Temperatura media, máxima y mínima diarias|Requiere API key gratuita|
|[`holidays`](https://pypi.org/project/holidays/)|Festivos nacionales y de la Comunidad de Madrid|Librería local|

**Periodo de estudio:** 2022–2024 (26.304 registros horarios)

> \\\*\\\*Nota sobre la API de REE.\\\*\\\* El widget `evolucion` no admite agregación
> horaria y devuelve `400 Bad Request` con `time\\\_trunc=hour`. La serie horaria
> se obtiene mediante el widget `demanda-tiempo-real`, cuya resolución nativa es
> de 10 minutos, reagregando después a frecuencia horaria.

\---

## Estructura del repositorio

```
.
├── notebooks/
│   ├── 01\\\_ingesta\\\_y\\\_eda.ipynb      Ingesta, tratamiento y análisis exploratorio
│   └── 02\\\_modelado.ipynb           Modelos baseline y machine learning (en curso)
├── src/
│   └── config.py                   Carga de credenciales desde .env
├── datos/                          Datos descargados (no versionados)
├── figuras/                        Gráficos generados (no versionados)
├── memoria/                        Enlace a la memoria en Overleaf
├── requirements.txt
├── .env.example                    Plantilla de credenciales
└── .gitignore
```

\---

## Instalación

```bash
git clone https://github.com/USUARIO/REPOSITORIO.git
cd REPOSITORIO

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\\\Scripts\\\\activate

pip install -r requirements.txt
```

### Credenciales

La API de AEMET requiere una clave gratuita, que se solicita en
[opendata.aemet.es/centrodedescargas/altaUsuario](https://opendata.aemet.es/centrodedescargas/altaUsuario).

```bash
cp .env.example .env
```

Edita `.env` y añade tu clave. **El archivo `.env` está excluido del control de
versiones y no debe subirse nunca al repositorio.**

\---

## Uso

```bash
jupyter notebook notebooks/01\\\_ingesta\\\_y\\\_eda.ipynb
```

Ejecuta las celdas en orden. El notebook descarga los datos, los almacena en
`datos/` en formato Parquet y genera las figuras en `figuras/`. En ejecuciones
posteriores detecta los archivos ya descargados y no repite las peticiones.

> \\\*\\\*El orden importa.\\\*\\\* Las secciones 5.2 y 5.3 deben ejecutarse antes que
> cualquier gráfico: la primera materializa los huecos del índice temporal y los
> rellena, y la segunda regenera las variables de calendario y meteorológicas
> que el reindexado deja incompletas.

## Autor

Roberto García Peña — Máster en Big Data y Ciencia de Datos
Dirección: Gonzalo Surribas Sayago
Curso 2025–2026

## Licencia

MIT — ver [LICENSE](LICENSE).

