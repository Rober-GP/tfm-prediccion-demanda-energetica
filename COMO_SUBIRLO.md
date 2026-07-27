# Cómo publicar este repositorio en GitHub

> Este archivo es para ti. **Bórralo antes de subir** o déjalo, da igual, pero
> no aporta nada al profesor.

---

## AVISO IMPORTANTE — tu clave de AEMET

El notebook que tenías **contenía tu clave real de AEMET escrita dentro**, en la
celda de configuración. Esa clave es un token JWT que incluye tu dirección de
correo electrónico codificada.

Ya la he eliminado de la copia que hay en este paquete, y he sustituido esa
parte por una carga desde archivo `.env`. Pero ten en cuenta dos cosas:

1. **No subas tu notebook antiguo.** Usa el de `notebooks/` de este paquete.
2. Si en algún momento llegaste a subir la clave a algún sitio público,
   solicita una nueva a AEMET.

De ahora en adelante la clave vive en `.env`, que está excluido en `.gitignore`
y nunca llegará al repositorio.

---

## 1. Configurar tu clave en local

```bash
cp .env.example .env
```

Abre `.env` y pega tu clave de AEMET:

```
AEMET_API_KEY=aqui_tu_clave_completa_de_aemet
ESIOS_TOKEN=
```

Instala la dependencia nueva:

```bash
pip install python-dotenv
```

---

## 2. Personalizar antes de publicar

Busca y sustituye en estos archivos:

| Archivo | Qué cambiar |
|---|---|
| `README.md` | `[Nombre y apellidos]`, `[Nombre del tutor]`, `USUARIO/REPOSITORIO` |
| `LICENSE` | `[Nombre y apellidos]` |
| `memoria/README.md` | `[PEGAR AQUÍ EL ENLACE DE OVERLEAF]` |

---

## 3. Crear el repositorio en GitHub

1. Entra en [github.com/new](https://github.com/new).
2. Nombre sugerido: `tfm-prediccion-demanda-energetica`
3. Descripción: *Predicción de demanda energética mediante Machine Learning y
   datos abiertos — TFM Máster en Big Data y Ciencia de Datos*
4. Visibilidad: **Public** (es un punto a favor de cara a la defensa; si
   prefieres, ponlo privado e invita al profesor como colaborador).
5. **No marques** ninguna casilla de inicialización: ya tienes README,
   `.gitignore` y `LICENSE`.

---

## 4. Subirlo

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Ingesta de datos, tratamiento y análisis exploratorio"
git branch -M main
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

### Antes del push, comprueba qué vas a subir

```bash
git status
```

En la lista **no debe aparecer**: `.env`, ningún `.parquet`, ninguna imagen de
`figuras/`. Si aparecen, para y revisa el `.gitignore`.

Comprobación específica de la clave:

```bash
git ls-files | xargs grep -lE "eyJ[A-Za-z0-9]{15,}" 2>/dev/null
```

Si no devuelve nada, está limpio.

---

## 5. Flujo de trabajo posterior

```bash
git add .
git commit -m "Modelos baseline ARIMA y SARIMA"
git push
```

Haz un commit por cada bloque de trabajo terminado, con un mensaje que describa
qué has hecho. El historial de commits es una prueba del progreso del trabajo, y
al tribunal le da una imagen muy distinta ver veinte commits repartidos en meses
que uno solo el día antes de entregar.

---

## Nota sobre el tamaño del notebook

El notebook pesa unos 2,6 MB porque conserva las figuras generadas en sus
salidas. Es intencionado: así el profesor puede verlas directamente en GitHub
sin ejecutar nada.

El inconveniente es que los `diff` entre versiones son ilegibles. Si te molesta,
puedes limpiar las salidas antes de cada commit:

```bash
pip install nbstripout
nbstripout --install        # se ejecuta automáticamente en cada commit
```

Para un TFM yo mantendría las salidas: el valor de que se vean los resultados
supera el inconveniente de los diffs.
