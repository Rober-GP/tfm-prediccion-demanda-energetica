# Aplicación web — guía de uso

## Estructura

```
app.py                          Aplicación Streamlit
src/prediccion.py               Variables, predicción y recomendaciones
src/datos.py                    Acceso a REData y AEMET
notebooks/04_modelo_final.ipynb Entrena y serializa el modelo
modelos/                        Modelo serializado (lo genera el notebook 04)
```

## Puesta en marcha

```bash
pip install -r requirements.txt
```

Copia los tres archivos (`app.py`, `src/`, `notebooks/04_modelo_final.ipynb`)
a la raíz de tu proyecto, junto a `datos/` y `notebooks/`.

**1. Entrena y guarda el modelo**

Ejecuta `notebooks/04_modelo_final.ipynb`. Antes, ajusta la línea:

```python
MODELO_ELEGIDO = "XGBoost"     # o "LightGBM"
```

Genera `modelos/modelo.joblib` y `modelos/modelo_info.json`.

**2. Arranca la aplicación**

```bash
streamlit run app.py
```

Se abre en `http://localhost:8501`.

## Sobre las claves

La aplicación funciona **sin ninguna clave**: la demanda y el precio se obtienen
de REData, que es de acceso libre.

Con `AEMET_API_KEY` en el archivo `.env` se usa la previsión meteorológica real.
Sin ella, se recurre a una estimación climatológica y la aplicación lo advierte
en pantalla.

## Decisiones de diseño que conviene poder explicar

**Código compartido entre entrenamiento y producción.** Las variables se
construyen en `src/prediccion.py`, que usan tanto el notebook 04 como la
aplicación. Es la protección frente al *training/serving skew*: si el
entrenamiento y el despliegue generan las variables de forma distinta, el
modelo se degrada sin que nada falle de manera visible.

**Predicción recursiva más allá de 24 horas.** El modelo tiene un horizonte
nativo de 24 h porque los desfases de 24 y 48 horas solo están disponibles
dentro de esa ventana. Para llegar a 48 h se realimentan las predicciones del
primer tramo. La celda 6 del notebook 04 cuantifica la degradación resultante.

**Degradación controlada.** Si AEMET no responde, se usa climatología. Si falla
el precio, la aplicación sigue funcionando. Solo la demanda es imprescindible,
y su ausencia se comunica con un mensaje claro.

## Despliegue público

Para la defensa conviene tener una URL accesible:

1. Sube el repositorio a GitHub (sin `.env`).
2. Entra en [share.streamlit.io](https://share.streamlit.io) y conecta el repo.
3. Indica `app.py` como archivo principal.
4. Añade `AEMET_API_KEY` en **Advanced settings → Secrets**.

El archivo `modelos/modelo.joblib` **sí debe subirse**, porque la aplicación lo
necesita. Comprueba que no esté excluido en `.gitignore`.
