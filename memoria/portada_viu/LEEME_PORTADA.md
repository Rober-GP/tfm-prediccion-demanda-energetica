# Portada oficial VIU

Reproduce la plantilla `P11_06_F08b_Plantilla_TFT_individual_v02`.

## Qué contiene

```
figuras/portada_viu.jpg    Fondo de página completa (408 KB)
portada.tex                Maquetación del texto sobre el fondo
```

## Instalación

**1. Sube la imagen** a la carpeta `figuras/` de tu proyecto en Overleaf.

**2. Añade al preámbulo** (ya tienes `tikz`; falta solo esta línea):

```latex
\usepackage{eso-pic}
```

**3. Sustituye tu portada actual.** Borra todo el bloque
`\begin{titlepage} ... \end{titlepage}` y pon en su lugar el contenido de
`portada.tex`, o bien:

```latex
\input{portada}
```

**4. Compila dos veces.** Es imprescindible: TikZ necesita una primera pasada
para conocer las coordenadas de la página. Si compilas solo una vez, verás el
fondo naranja pero **sin ningún texto encima**.

## Datos a revisar

Ya están rellenados con tus datos, pero verifica:

| Campo | Valor actual |
|---|---|
| Titulación | Máster Universitario en Big Data y Ciencia de Datos |
| Alumno | García Peña, Roberto |
| D.N.I. | 17458202Y |
| Director | Gonzalo Surribas Sayago |
| Curso | 2025 – 2026 |
| Convocatoria | Primera |
| Fecha | **00 Mes 2026** ← poner la fecha de entrega |

## Sobre las medidas

Las posiciones no son aproximadas: están medidas sobre la plantilla original.

| Elemento | Posición |
|---|---|
| Barras verticales | x = 28,1 / 81,9 / 140,0 mm |
| Altura de las barras | 205,9 a 256,9 mm |
| Ancho de barra | 1,7 mm |

**Dos ajustes respecto al original**, ambos por legibilidad:

El **título** tiene el ancho limitado a 7 cm. El fondo blanco invade por la
derecha, y a la altura de 42 mm el naranja solo llega hasta 111 mm: un título
más ancho quedaría en blanco sobre blanco y sería ilegible. Si el tuyo fuese
más corto, puedes ampliar `text width` y subir `fontsize`.

El **bloque de datos** empieza a 212 mm en lugar de a 206 mm. A la altura
original, la columna de convocatoria cae sobre la zona blanca. Es un defecto de
la plantilla oficial: al renderizarla, su propio encabezado «Convocatoria:»
resulta invisible. Bajando el bloque 6 mm se ve todo.

## Si quieres retocarlo

- Tamaño del título: el `\fontsize{17}{21}` del primer nodo
- Posición vertical de cualquier elemento: el segundo valor de `(x,-y)`
- Altura del bloque de datos: los tres `-21.2cm`
