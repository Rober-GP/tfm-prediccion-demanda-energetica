# Predicción de la demanda eléctrica peninsular mediante Machine Learning y datos abiertos

**Trabajo Fin de Máster** · Máster Universitario en Big Data y Ciencia de Datos (VIU), curso 2025–2026
**Autor:** Roberto García Peña · **Director:** Gonzalo Surribas Sayago

Sistema completo de predicción de la demanda eléctrica peninsular española a 24–48 horas,
construido exclusivamente con datos abiertos. Abarca la ingesta y el tratamiento de los
datos, el análisis exploratorio, la comparación de diez modelos y una aplicación web
local que traduce la previsión en recomendaciones para el consumidor acogido a la
tarifa PVPC.

La memoria completa está en [`memoria/`](memoria/).

---

## Resultados principales

Validación temporal de origen rodante: 14 orígenes, horizonte de 24 h y paso de 5 días (octubre–diciembre de 2024).

| Modelo | MAPE mediano | MAPE medio | MAE (MW) | Mejora sobre el ingenuo semanal |
|---|---:|---:|---:|---:|
| **XGBoost** | **1,34 %** | 1,65 % | 470 | +56,3 % |
| Random Forest | 1,47 % | 1,86 % | 520 | +52,1 % |
| LightGBM | 1,53 % | 1,67 % | 473 | +49,9 % |
| Ridge | 1,94 % | 2,55 % | 717 | +36,7 % |
| SARIMA | 2,42 % | 3,95 % | 1.120 | +20,9 % |
| Ingenuo semanal | 3,06 % | 3,92 % | 1.108 | referencia |
| Prophet | 4,78 % | 4,86 % | 1.370 | −56,4 % |
| SARIMAX + Fourier | 4,90 % | 5,66 % | 1.565 | −60,3 % |

Evaluación dirigida sobre 8 días festivos: LightGBM 3,01 %, XGBoost 3,32 % e ingenuo semanal 16,63 %.

---

## Fuentes de datos

| Fuente | Datos | Acceso |
|---|---|---|
| [REE — API REData](https://www.ree.es/es/apidatos) | Demanda peninsular (resolución de 10 min, agregada a horaria) y precio de mercado | Libre, sin credenciales |
| [AEMET OpenData](https://opendata.aemet.es/) | Climatología diaria de Madrid-Retiro (histórico) y predicción horaria municipal (aplicación) | Clave gratuita |
| [`holidays`](https://pypi.org/project/holidays/) | Festivos de las 19 subdivisiones territoriales, ponderados por población (INE) | Librería local |

**Periodo de estudio:** 1 de enero de 2022 a 31 de diciembre de 2024 (26.304 horas descargadas).
Tras descartar la primera semana, que se usa para construir el desfase de 168 h, el conjunto de modelado tiene 26.136 horas.

> **Nota sobre la API de REE.** El widget `evolucion` no admite agregación horaria
> y devuelve `400 Bad Request` con `time_trunc=hour`. La serie se obtiene del widget
> `demanda-tiempo-real` y se reagrega a frecuencia horaria. Las peticiones de periodos
> largos devuelven `502`, por lo que la descarga se fracciona en bloques.

---

## Estructura del repositorio

```
.
├── app.py                         Aplicación Streamlit (ejecución local)
├── src/
│   ├── config.py                  Rutas y carga de credenciales desde .env
│   ├── datos.py                   Acceso a REData y AEMET en tiempo real
│   └── prediccion.py              Construcción de variables y predicción (compartido
│                                  por el entrenamiento y la aplicación)
├── notebooks/                     Ver tabla de ejecución más abajo
│   └── archivo/                   Versiones previas, conservadas por trazabilidad
├── datos/                         Datos descargados (se regeneran, no versionados)
├── resultados/                    Tablas de métricas citadas en la memoria
├── modelos/                       Modelo serializado (lo genera el notebook 04)
├── figuras/                       Gráficos (se regeneran, no versionados)
├── memoria/                       Memoria del TFM en PDF
├── requirements.txt
├── .env.example                   Plantilla de credenciales
└── LICENSE
```

### Orden de ejecución de los notebooks

| # | Notebook | Contenido | Sección de la memoria |
|---|---|---|---|
| 1 | `01_ingesta_y_eda.ipynb` | Descarga, reindexado e imputación, Fourier, MSTL, ACF/PACF, anomalías, temperatura | 4.2–4.3 |
| 2 | `01b_festivos_ponderados.ipynb` | Intensidad de festivo ponderada por población | 4.4, 5.5 |
| 3 | `02_modelado_baseline_v2.ipynb` | Modelos ingenuos, SARIMA, SARIMAX + Fourier, Prophet | 4.6, 5.2 |
| 4 | `03_modelado_ml_v2.ipynb` | Fuga de información, Ridge, Random Forest, XGBoost, LightGBM, SHAP, festivos, sensibilidad meteorológica | 4.4–4.6, 5.2–5.5, 6.4 |
| 5 | `04_modelo_final.ipynb` | Entrenamiento con todo el histórico y serialización del modelo de la aplicación | 4.8, 5.6 |
| 6 | `04b_diagnostico.ipynb` | Comprobación del modelo final sobre un bloque continuo de 30 días | 5.6 |

Los notebooks de `notebooks/archivo/` (`02_modelado_baseline`, `02_celdas_corregidas`,
`03_modelado_ml` y `03b_evaluacion_festivos`) son versiones anteriores. Sus resultados
quedan sustituidos por los de la tabla anterior.

---

## Instalación

Requiere Python 3.11.

```bash
git clone https://github.com/Rober-GP/tfm-prediccion-demanda-energetica.git
cd tfm-prediccion-demanda-energetica

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Credenciales

```bash
cp .env.example .env               # Windows: copy .env.example .env
```

Rellena `AEMET_API_KEY` con la clave gratuita que se solicita en
<https://opendata.aemet.es/centrodedescargas/altaUsuario>. El archivo `.env` está
excluido del control de versiones.

---

## Reproducir los resultados

Ejecuta los notebooks en el orden de la tabla anterior. El notebook 01 descarga los datos
en `datos/`; los siguientes generan las tablas de `resultados/` y las figuras de
`figuras/`. Todo el proceso se ejecuta en un ordenador personal, sin GPU, en unos
pocos minutos.

## Ejecutar la aplicación (local)

La aplicación necesita el modelo serializado. Si `modelos/modelo.joblib` no existe,
ejecuta antes `04_modelo_final.ipynb`.

```bash
streamlit run app.py
```

Se abre en `http://localhost:8501`. La aplicación:

- descarga la demanda reciente de REData;
- predice las próximas 24 h y extiende la predicción a 48 h de forma recursiva;
- identifica las franjas de menor demanda y genera una recomendación en lenguaje natural;
- muestra el precio de mercado cuando REData lo publica.

Sin clave de AEMET funciona igualmente: usa una estimación climatológica de la
temperatura y lo indica en pantalla. Solo la serie de demanda es imprescindible.

---

## Limitaciones

- La temperatura es diaria y procede de una sola estación (Madrid-Retiro).
- La evaluación retrospectiva usa temperaturas observadas, no previsiones.
- La aplicación predice demanda, no precio. La demanda se emplea como indicador
  aproximado del precio.
- Más allá de 24 h la predicción es recursiva y el error aumenta.

Detalle completo en la sección 6.4 de la memoria.

## Uso de IA generativa

El uso de herramientas de IA generativa durante el trabajo está documentado en el
repositorio de transparencia <https://github.com/Rober-GP/repositorio-ia-TFM>.

## Licencia

[MIT](LICENSE) © 2026 Roberto García Peña
