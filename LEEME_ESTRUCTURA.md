# Sistemas de Representación · PCI1119

Cómo está organizada esta carpeta y dónde va cada cosa.

## Las seis carpetas

| Carpeta | Qué guarda |
|---|---|
| **1_Curso** | Programa, planificación, temario, contexto y las nóminas de ambas secciones |
| **2_Clases** | Presentaciones por capítulo, apuntes, y las plantillas de diseño (Cajetín y Filete) |
| **3_Actividades** | Material que reciben los alumnos: plantillas isométricas y el generador de ejercicios |
| **4_Correcciones** | Entregas, resultados y planillas de notas, separados por sección |
| **5_Herramientas** | El corrector automático y la pauta procesada. Una sola copia para todo |
| **6_Referencias** | Bibliografía, material de colegas y escaneos. Sin ordenar, a propósito |

## La regla de oro

**Las herramientas no se duplican por sección.** Antes había tres copias del
corrector y empezaron a divergir. Ahora hay una sola, en `5_Herramientas`, y se
le indica sobre qué carpeta trabajar:

```
cd 5_Herramientas\corrector
python 01_extraer.py --carpeta "..\..\4_Correcciones\Seccion 4\Actividad 1"
```

O se fija una vez y no se repite más:

```
python fijar_carpeta.py "..\..\4_Correcciones\Seccion_4\Actividad 1"
python 01_extraer.py
python 08_corregir_curso.py
python 05_excel.py
```

`python contexto.py` muestra sobre qué carpeta está trabajando y qué archivos
encontró o le faltan.

## Cómo se agrega una sección o una actividad

1. Crear `4_Correcciones\Seccion_N\`
2. Dejar ahí la nómina, con nombre que empiece por `Nomina_`
3. Crear `4_Correcciones\Seccion_N\Actividad X\`
4. Dejar ahí el ZIP de Moodle, con su nombre original que empieza por `gradebook_`
5. Apuntar el corrector a esa carpeta

No hay que copiar scripts ni editar rutas. El código lee el código de sección y
el semestre desde el nombre de la nómina.

## Dónde está cada cosa importante

- **Notas**: `4_Correcciones\Seccion_N\Notas_ActividadX_PCI1119-N.xlsx`
- **Observaciones de corrección**: `4_Correcciones\OBSERVACIONES.md`
- **Detalle cara por cara**: `4_Correcciones\Seccion_N\Actividad X\salida\curso_resultados.csv`
- **Corrector por portapapeles**: `5_Herramientas\corrector\Corregir.bat`
- **Cómo funciona el corrector**: `5_Herramientas\corrector\LEEME.md`

## Detalles que conviene saber

`2_Clases\_historico` guarda las versiones antiguas de Cap01 y Cap02, que fueron
reemplazadas por las `_v2`. Cap03 no tiene v2, así que la versión que está en
`Presentaciones` es la vigente.

`2_Clases\Presentaciones` tiene dos series de nombres conviviendo: la numerada
`00_` a `10_` y las `Cap0X_v2`. Puede que se solapen en contenido. Está pendiente
revisarlo.

Las carpetas `salida\` dentro de cada actividad son resultado de los scripts: se
regeneran corriéndolos de nuevo. Si hace falta espacio, se pueden borrar.

`4_Correcciones\Seccion_3\Actividad 1\gradebook_..._14-46-26\` es la extracción
manual original hecha desde Windows. Está duplicada con `salida\entregas` y ocupa
60 MB. Se puede borrar sin perder nada, el ZIP sigue ahí.
