# Datos

Este directorio **no se versiona**. Los archivos se generan ejecutando
`notebooks/01_ingesta_y_eda.ipynb`.

| Archivo | Contenido |
|---|---|
| `demanda_horaria.parquet` | Demanda peninsular horaria (REE) |
| `meteo_diaria.parquet` | Valores climatológicos diarios (AEMET) |
| `dataset_modelado.parquet` | Dataset integrado con las variables predictoras |

El notebook detecta los archivos ya descargados y no repite las peticiones a
las APIs.
