# Como partir - Actividad 4

## 1. Preparar las entregas

El zip de Blackboard esta en `4_Correcciones/Seccion_3/Actividad 4/`.
Extraelo y deja las fotos y PDF de cada alumno en:

    Actividad 4/entradas/entregas/<usuario>/

Un `<usuario>` es la parte del correo antes de la arroba. Los PDF conviene
rasterizarlos a PNG antes (150 dpi basta).

## 2. Opcion automatica

    cd rectificador
    python rectificar.py --entradas ../entradas/entregas --pautas ../entradas/pautas_escaneadas --salida ../salida

Necesita Python 3.10 con cv2, numpy y PIL. Deja `salida/manifest.json`, los
recortes en `salida/celdas/` y las imagenes de control en `salida/_qa/`.

Estado conocido: de 47 paginas procesadas en la prueba, 28 salieron por
deteccion de contornos, 18 por metodos de respaldo y 1 fallida. Pendiente
sin resolver: las dos pautas quedaron rectificadas rotadas 180 grados, asi
que la numeracion de sus cuadros sale invertida (el c1 trae el ejercicio 6).
Mientras eso no se arregle, rectifica las pautas a mano con el escaner.

## 3. Opcion manual, que es la recomendada por ahora

Doble clic en `Visor.bat`. Se levanta el servidor local y se abre el navegador.

- Boton **Escanear**: cargas una foto, marcas las 4 esquinas, refinas los
  bordes, rectificas y guardas. Dos modos: hoja completa, que corta los 6
  cuadros solo, y cuadro suelto.
- Lo que guardas queda en `salida/celdas/` y el visor lo toma con el boton
  **Recargar datos**.
- En el visor comparas contra la pauta en cuatro modos y pones el veredicto
  por cuadro. Exporta CSV y JSON.

Detalle de uso y atajos en `visor/LEEME.md` y `visor/LEEME_ESCANER.md`.
El informe de la revision de codigo esta en `REVISION.md`.

---

## 4. Pauta vectorial y comparacion automatica (agregado despues)

### Dependencias

    C:\Python313\python.exe -m pip install opencv-python numpy pillow ezdxf openpyxl

### Generar la pauta vectorial

    cd pauta_vectorial
    python generar_pauta.py --datos . --salida ../salida/pautas --dxf ./dxf

Los datos de cada cuadro son los JSON de esa carpeta, con la geometria en
coordenadas de reticula. Si un ejercicio quedo mal leido, se corrige editando
el JSON y volviendo a generar. Los DXF ya generados estan en `pauta_vectorial/dxf/`
y se abren en AutoCAD o Inventor.

REVISAR ANTES DE CALIFICAR: `vistas` cuadro 2 y los seis cuadros de
`isometricos` quedaron marcados como dudosos en sus JSON. Los isometricos
hubo que reconstruirlos desde las vistas del enunciado y solo se verifico la
silueta general, no cada interseccion.

### Pagina de comparacion

Con `Visor.bat` corriendo, el boton Comparacion abre la pagina nueva.
Se elige alumno y pagina, se comparan los 6 cuadros de una pasada, y cada
cuadro muestra su porcentaje de parecido y el mapa de diferencia.
El panel de nota propone un valor de 0 a 100 y deja editable la nota final
y las observaciones. El boton Registrar en Excel escribe la fila en
`salida/Notas_Actividad4.xlsx`, una fila por alumno, actualizando si ya existe.

El metodo de similitud y los pesos estan en `comparador/LEEME.md`.
Para ajustar cuan estricto es, se editan los pesos al inicio de
`comparador/similitud.py`. Prueba de referencia:

    python comparador/pruebas.py

Valores esperados: pauta contra si misma 100, desplazada 20 px 100,
con 35 por ciento del trazo borrado 71.6, contra otra figura 31.2.
