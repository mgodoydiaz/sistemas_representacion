# Contrato de interfaces — Corrector Actividad 1 (PCI1119-3)

Raíz: `Sección 3/Corrección Actividad 1/`
Todos los scripts viven en `corrector/` y se ejecutan desde ahí con rutas relativas a `RAIZ = Path(__file__).resolve().parent.parent`.

## Entradas fijas
- `Pauta/imagen1.png` ... `imagen5.png`  (capturas del applet, 921x639 aprox)
- `gradebook_...zip`                      (entregas crudas)
- `../Nomina_PCI1119-3_Sistemas_de_Representacion_Semestre_2-2026.xlsx`

## Salidas por etapa

### E1 — extraccion (script `01_extraer.py`)
- `salida/entregas/<usuario>/` una carpeta por usuario (parte antes de @ del correo)
  con los archivos originales renombrados cortos: `01_<nombre_original_truncado>.<ext>`
- `salida/inventario.csv` columnas:
  `usuario,correo,nombre_completo,fecha_envio,n_archivos,archivos,tipo_entrega,observacion`

### E2 — pauta (script `02_pauta.py`)
- `salida/pauta/lamina<N>.json`:
```json
{"lamina":1,"tam":[W,H],"leyenda":{"rojo":"Alzado","amarillo":"Planta","cyan":"Perfil"},
 "piezas":[{"pieza":1,"bbox":[x,y,w,h],
   "caras":[{"id":"P1-C01","color":"rojo","rgb":[255,0,0],"area":1234,
             "centroide":[x,y],"punto_seguro":[x,y],"bbox":[x,y,w,h]}]}]}
```
  `punto_seguro` = punto interior alejado de bordes (erosion max).
- `salida/pauta/lamina<N>_mask.png`  (PNG 16-bit o paleta: valor = índice global de cara, 0 = fondo)
- `salida/pauta/lamina<N>_anotada.png` (pauta con el id de cada cara dibujado)
- `salida/pauta/lamina<N>_ref.png`  (recorte SOLO del área de las 4 piezas, sin panel derecho ni barra)

### E3 — normalizacion (script `03_normalizar.py`)
- `salida/entregas/<usuario>/norm/lamina<N>.png` imagen candidata ya recortada al área de piezas
- `salida/entregas/<usuario>/norm/manifest.json`:
```json
{"usuario":"x","items":[{"archivo_origen":"...","pagina":1,"lamina":3,"confianza":0.87,
  "salida":"norm/lamina3.png","metodo":"orb","nota":""}],
 "laminas_detectadas":[1,2,3],"laminas_faltantes":[4,5],"dudosos":[]}
```

### E4 — correccion (script `04_corregir.py`)
- `salida/resultados.csv` una fila POR CARA:
  `usuario,lamina,pieza,cara_id,color_esperado,color_detectado,correcto,confianza`
- `salida/resumen.csv` una fila POR ESTUDIANTE:
  `usuario,correo,nombre,laminas_entregadas,caras_total,caras_correctas,puntaje_0_100,revisar,motivo_revisar`
- `salida/reportes/<usuario>_lamina<N>.png` triple panel: pauta | estudiante alineado | diff con caras marcadas

### E5 — excel (script `05_excel.py`)
- `salida/Notas_Actividad1_PCI1119-3.xlsx`

## Convenciones
- Colores del código (RGB exacto del applet):
  rojo (255,0,0)=Alzado · amarillo (255,255,0)=Planta · cyan (0,255,255)=Perfil ·
  naranjo (255,187,0)=Alzado+Planta · verde (0,255,0) · azul (0,0,255) · blanco/sin pintar (255,255,255) · fondo (243,240,231)
  La leyenda REAL de cada lámina se extrae del panel derecho de la pauta, no se asume.
- Puntuación BINARIA: cara correcta = 1, cualquier otra cosa = 0.
- Puntaje final = 100 * caras_correctas / caras_totales de las 5 láminas (no entregada = 0 caras correctas).
- Python 3.10, usar cv2, numpy, PIL, pandas, openpyxl, pdf2image/pdftoppm. NO instalar nada pesado.
- Sin emojis en los scripts. Comentarios en español.
