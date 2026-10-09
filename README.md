# sistemas_representacion

Material y herramientas para el ramo PCI 1119 Sistemas de Representación (UCT, Ingeniería Civil Industrial). Docente: Miguel Godoy Díaz.

## Estructura

| Carpeta | Contenido |
|---|---|
| `1_Curso` | Planificación, contexto y programa del ramo |
| `2_Clases` | Apuntes, presentaciones propias y plantillas de diseño (Cajetín y Filete) |
| `3_Actividades` | Plantillas isométricas, Tarea 1 y brief del generador de ejercicios |
| `5_Herramientas` | Código del corrector automático y del visor de la Actividad 4 (sin datos) |
| `propuestas` | Cierre del semestre 2026-2: criterios de evaluación, apuntes nuevos, Proyecto 2, presentación, guía de uso de IA y bibliografía. Partir por `propuestas/LEEME.md` |

`LEEME_ESTRUCTURA.md` describe la carpeta local completa, que tiene además `4_Correcciones` y `6_Referencias`.

## Qué no está aquí, y por qué

Este repositorio es público. Quedan fuera, y están en `.gitignore`:

- Nóminas, entregas, notas y observaciones de corrección (datos de estudiantes).
- Libros y material de terceros (`6_Referencias` y las presentaciones heredadas `00_` a `10_`).
- Archivos con nombres de estudiantes detectados en una revisión automática: `1_Curso/TEMARIO_CURSO_SR.md`, `2_Clases/Apuntes/Nuevo_Cajetin_Vistas_Cortes/investigacion/normas_cajetin_auxiliares_cortes.md`, `5_Herramientas/Actividad 4/visor/js/escaner/app.js`, `5_Herramientas/corrector/NOTA_ERROR_ZIP.md` y `3_Actividades/Enunciados/ENUNCIADOS.md`. Algunos pueden ser falsos positivos: revisar antes de subirlos.

Las actividades y sus pautas sí están publicadas, por decisión del docente.

## Regenerar documentos

Los scripts `build_*.py` usan la plantilla de documentos del docente (`plantilla.py`), python-docx, matplotlib y LibreOffice. El Proyecto 2 requiere además `cadquery` y `shapely`.
