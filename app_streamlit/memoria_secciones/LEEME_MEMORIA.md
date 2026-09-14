# Secciones redactadas — cómo integrarlas

## Archivos

| Archivo | Contenido |
|---|---|
| `parte1.tex` | Capítulo 1 completo (1.1–1.3) y capítulo 3 completo (3.1–3.5) |
| `parte2.tex` | Metodología: 4.1, 4.5, 4.6, 4.7, 4.8 + correcciones a 4.2.1 y 4.4.3 |
| `parte3.tex` | Discusión: 5.2–5.6 y capítulo 6 completo |
| `referencias_nuevas.bib` | 4 entradas nuevas para añadir a `referencias.bib` |

Cada bloque lleva una cabecera que indica qué sección sustituye. Copia y pega en
`main.tex` sobre los `[PENDIENTE DE REDACTAR]` correspondientes.

Todo el LaTeX compila sin errores (probado: 34 páginas de contenido nuevo).

---

## Antes de compilar

**1. Añade las referencias nuevas**

Copia el contenido de `referencias_nuevas.bib` al final de tu `referencias.bib`.

**2. Añade estas etiquetas**

En la sección 4.4 (Ingeniería de características), justo después del `\section`:

```latex
\label{sec:features}
```

**3. Renumera el capítulo 5**

La sección 5.5 actual («Aplicación desarrollada») pasa a ser 5.6, porque se
inserta antes la nueva 5.5 («Evaluación en días festivos»).

**4. Elimina `\nocite{*}`**

Ahora el documento cita más de quince referencias reales. Busca «NOTA TEMPORAL»
en `main.tex` y borra la línea `\nocite{*}`, para que la bibliografía refleje
solo lo efectivamente citado.

---

## Lo que falta completar

Busca `PENDIENTE` y `COMPLETAR` en los tres archivos. Son seis huecos:

| Dónde | Qué falta | De dónde sacarlo |
|---|---|---|
| 3.5 | Referencias de Surribas Sayago | **Pídeselas a él: es tu director** |
| 4.1 | Diagrama de arquitectura | draw.io o Excalidraw |
| 5.3 | Ranking de importancia de variables | Notebook 03, sección 6 |
| 5.3 | Interpretación de los SHAP | Notebook 03, figura 16 |
| 5.6 | Degradación recursiva a 48 h | Notebook 04, celda 6 |
| 5.6 | Captura de la aplicación | Ejecutar la app y capturar |
| Anexos | URLs de GitHub y de la app | Cuando despliegues |

Dos datos menores que también convendría poner, si los tienes a mano:

- Sección 4.3.2: el estadístico D y el p-valor del test de Kolmogorov-Smirnov
- Sección 4.3.4: los valores de fuerza de las componentes del MSTL

---

## Correcciones a texto ya escrito

**Sección 4.2.1, último párrafo.** Dice que la descarga se ejecuta «mes a mes»,
pero la implementación final trocea en bloques de cinco días para evitar los
errores 502. El texto corregido está comentado al final de `parte2.tex`.

**Sección 4.4, Tabla 4.4.** Lista `lag_1h`, `lag_2h`, `lag_3h`, `media_24h` y
`std_24h` como variables predictoras. Se construyen en el análisis exploratorio,
pero **se descartan** por fuga de información. Añade una nota a pie de tabla:

> Los desfases de orden inferior al horizonte y los estadísticos móviles
> calculados con desplazamiento unitario se descartan posteriormente por fuga de
> información (sección 4.4.3).

**Tabla 2.1 (alcance).** Menciona ESIOS, que finalmente no se utilizó. Sustituye
«REE/ESIOS» por «REE (API REData)».

---

## Sobre las referencias de tu director

Gonzalo Surribas Sayago dirige tu TFM y te recomendó citar sus trabajos. Son
suyos, así que la vía directa es pedírselos. Puede ser además una buena excusa
para retomar el contacto:

> Estoy redactando el estado del arte y me gustaría incluir los trabajos que me
> recomendaste en la primera reunión. ¿Podrías pasarme las referencias completas?

---

## Estado de la memoria tras integrar esto

| Capítulo | Estado |
|---|---|
| Resumen / Abstract | Completo |
| 1. Introducción | **Completo** |
| 2. Objetivos | Completo |
| 3. Estado del arte | **Completo** (falta Surribas) |
| 4. Metodología | **Completo** (falta el diagrama) |
| 5. Discusión | **Completo** (faltan 3 figuras) |
| 6. Conclusiones | **Completo** |
| Referencias | Automático |
| Anexos | Faltan las URLs |

De doce secciones pendientes pasas a seis huecos menores, casi todos figuras.

---

## Diagrama de arquitectura (`diagrama_arquitectura.tex`)

Está hecho en **TikZ**, no como imagen: es vectorial, usa la tipografía del
documento y no depende de ningún archivo externo.

**1. Añade al preámbulo de `main.tex`**, junto a los demás `\usepackage`:

```latex
\usepackage{tikz}
\usetikzlibrary{positioning, arrows.meta, fit, backgrounds, calc}
```

**2. En la sección 4.1**, sustituye el bloque `\framebox` por el contenido de
`diagrama_arquitectura.tex` (o usa `\input{diagrama_arquitectura}` si prefieres
mantenerlo en un archivo aparte).

Usa el color `azultfm`, que ya está definido en tu preámbulo.

### Qué muestra

Las tres capas del sistema y, en naranja, el elemento que conviene destacar en la
defensa: `prediccion.py` es **compartido** por el entrenamiento y por la
aplicación. Esa flecha discontinua etiquetada «mismo código» representa la
protección frente al *training/serving skew*.

Obsérvese también que entrenamiento y validación tienen salidas distintas: el
primero produce el modelo serializado, la segunda las métricas. Es una distinción
menor pero correcta, y evita sugerir que la validación interviene en la
construcción del modelo final.

### Sobre babel y los caracteres `<` y `>`

Babel con la opción `spanish` convierte `<` y `>` en caracteres activos, porque
los emplea como atajo para las comillas angulares «». Eso rompe la sintaxis
habitual de TikZ, donde `->` y `>=` aparecen constantemente, y produce errores en
todos los `\draw`.

El diagrama que se incluye **evita deliberadamente ambos caracteres**: en lugar de
`->` emplea `-{Stealth[length=2.2mm]}`, que es equivalente. No tienes que hacer
nada, pero conviene saberlo si más adelante añades tikz por tu cuenta.

Si necesitas usar `->` en algún otro diagrama, envuelve la figura así:

```latex
\shorthandoff{<>}
\begin{tikzpicture}
  ...
\end{tikzpicture}
\shorthandon{<>}
```

### Si quieres ajustarlo

- Separación entre capas: el `right=4.2cm of feat` del nodo `vivo`
- Tamaño de letra: el `font=\small` de las opciones de `tikzpicture`
- El MAPE del nodo «Métricas»: actualízalo si vuelves a entrenar
