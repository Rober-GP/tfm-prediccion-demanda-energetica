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

\---

## Metodología

### Tratamiento de valores ausentes

De los 26.304 registros esperados se obtuvieron 26.214, con 90 ausencias
(0,34 %). Estas ausencias no figuraban como valores nulos sino como **filas
inexistentes en el índice temporal**, por lo que una interpolación directa no
habría tenido efecto alguno. La serie se reindexa previamente sobre una malla
horaria completa y a continuación se imputa siguiendo un criterio escalonado:

|Longitud del hueco|Estrategia|
|-|-|
|≤ 3 h|Interpolación temporal lineal|
|> 3 h|Valor de la misma hora de la semana anterior (desfase de 168 h)|
|Residual|Mediana del perfil mes × día de la semana × hora|

El desfase semanal preserva el perfil diario, que una interpolación lineal
destruiría al trazar una recta a través de un ciclo completo. La equivalencia de
distribuciones antes y después se verifica mediante el test de
Kolmogorov-Smirnov.

### Análisis espectral

La transformada rápida de Fourier identifica los periodos dominantes de forma
objetiva:

|Periodo|Interpretación|
|-|-|
|24 h|Ciclo diario|
|12 h|Armónico del diario (doble pico mediodía/tarde)|
|168 h|Ciclo semanal|

Los desfases temporales empleados como variables predictoras se derivan de estos
periodos, no de una elección por convención.

### Detección de anomalías

La regla del rango intercuartílico aplicada a la serie completa no identifica
ningún valor atípico: la propia variación estacional ensancha el rango hasta
privarlo de capacidad discriminante. Se emplea en su lugar un z-score robusto
sobre el residuo respecto al perfil mes × día de la semana × hora.

El procedimiento identifica 555 horas anómalas, de las cuales cerca del 70 % se
concentra en días festivos o en su entorno, con una desviación mediana próxima a
−7.000 MW. Esta evidencia justifica cuantitativamente la inclusión de variables
de calendario entre los predictores.

### Progresión de modelos

|Fase|Modelos|Estado|
|-|-|-|
|Línea base|ARIMA, SARIMA, Prophet|En curso|
|Machine learning|Random Forest, XGBoost, LightGBM|Pendiente|
|Deep learning|LSTM|Opcional|

La validación se realiza mediante *walk-forward* (`TimeSeriesSplit`), nunca
validación cruzada aleatoria.

\---

## Estado del proyecto

* \[x] Ingesta de datos (REE, AEMET, calendario)
* \[x] Tratamiento de valores ausentes y verificación estadística
* \[x] Análisis exploratorio y espectral
* \[x] Ingeniería de características
* \[ ] Modelos baseline (ARIMA, SARIMA, Prophet)
* \[ ] Modelos de machine learning
* \[ ] Aplicación web (Streamlit)
* \[ ] Memoria

\---

## Memoria

La memoria del trabajo se redacta en Overleaf. Enlace disponible en
[`memoria/README.md`](memoria/README.md).

\---

## Autor

Roberto García Peña — Máster en Big Data y Ciencia de Datos
Dirección: Gonzalo Surribas Sayago
Curso 2025–2026

## Licencia

MIT — ver [LICENSE](LICENSE).

