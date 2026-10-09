# -*- coding: utf-8 -*-
"""
Genera la planilla de notas y rubrica de la ACTIVIDAD 2.
PCI1119 Sistemas de Representacion.

Actividad 2: 10 ejercicios de educacionplastica.net/vistas.html
(4 nivel elemental, 4 nivel medio, 2 nivel alto). Por cada ejercicio, las tres
vistas en norma ISO-E. Evidencia en PDF con pantallazos.

Puntaje: 1 punto por vista, 3 por ejercicio, ponderado x1 / x2 / x3 segun nivel.

Salida: ../Notas_Actividad2_<codigo de la seccion>.xlsx
"""

import os
import sys

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contexto
# Estructura de la evaluacion
NIVELES = [("elemental", 4, 1), ("medio", 4, 2), ("alto", 2, 3)]
VISTAS = [("A", "Alzado (frontal)"), ("P", "Planta (superior)"), ("L", "Perfil (lateral)")]

DESCUENTOS = [
    ("PDF", 0, "Formato solicitado en el enunciado"),
    ("Word", -10, "Entrego .docx en vez de PDF"),
    ("Imagen", -20, "Entrego imagenes sueltas en vez de PDF"),
    ("Sin entrega", 0, "No entrego; el puntaje ya queda en cero por si solo"),
]

FUENTE = "Arial"
AZUL = "2E5E8C"
GRIS_CAB = "D9D9D9"
AMARILLO = "FFF2CC"
CELESTE = "DDEBF7"
VERDE = "C6EFCE"
AMBAR = "FFEB9C"
ROJO = "FFC7CE"
BORDE = Border(*[Side(style="thin", color="BFBFBF")] * 4)
BORDE_GRUESO = Side(style="medium", color="808080")


def cargar_nomina():
    ruta = contexto.ruta_nomina()
    wb = openpyxl.load_workbook(ruta, data_only=True)
    ws = contexto.hoja_nomina(wb)
    filas = []
    for r in ws.iter_rows(min_row=6, values_only=True):
        if not r or not r[0]:
            continue
        filas.append({"n": r[0], "apellidos": r[1], "nombres": r[2], "correo": r[5]})
    return filas


def main():
    nomina = cargar_nomina()
    wb = openpyxl.Workbook()

    # ================================================================ RUBRICA
    wr = wb.active
    wr.title = "Rubrica"
    wr.column_dimensions["A"].width = 3
    wr.column_dimensions["B"].width = 30
    wr.column_dimensions["C"].width = 95

    def titulo(fila, txt):
        wr.cell(row=fila, column=2, value=txt).font = Font(
            name=FUENTE, size=12, bold=True, color=AZUL)

    def linea(fila, etiqueta, texto, negrita=False):
        c = wr.cell(row=fila, column=2, value=etiqueta)
        c.font = Font(name=FUENTE, size=10, bold=True)
        c.alignment = Alignment(vertical="top")
        d = wr.cell(row=fila, column=3, value=texto)
        d.font = Font(name=FUENTE, size=10, bold=negrita)
        d.alignment = Alignment(wrap_text=True, vertical="top")

    wr["B1"] = "RUBRICA - ACTIVIDAD 2: VISTAS DIEDRICAS EN NORMA ISO-E"
    wr["B1"].font = Font(name=FUENTE, size=14, bold=True, color=AZUL)
    wr["B2"] = contexto.encabezado()
    wr["B2"].font = Font(name=FUENTE, size=10, color="666666")

    f = 4
    titulo(f, "1. Encargo"); f += 1
    linea(f, "Tarea",
          "Elegir 10 ejercicios de https://www.educacionplastica.net/vistas.html: "
          "4 de nivel elemental (red 2x2x2), 4 de nivel medio (red 3x3x3) y 2 de nivel alto "
          "(figuras con elementos cilindricos y conicos). Representar cada figura tridimensional "
          "en sus tres vistas: frontal (alzado), superior (planta) y lateral (perfil).")
    f += 2
    linea(f, "Norma", "Sistema europeo, primer diedro (ISO-E).")
    f += 2
    linea(f, "Herramienta y evidencia",
          "Los dibujos se hacen dentro del software. La evidencia de avance se entrega como "
          "pantallazos reunidos en un unico archivo PDF.")
    f += 3

    titulo(f, "2. Unidad de puntaje: la vista"); f += 1
    linea(f, "1 punto",
          "La vista esta dibujada y su contorno corresponde a la proyeccion correcta de la pieza. "
          "Se aceptan diferencias de escala, de grosor de linea y de posicion dentro de la lamina.")
    f += 2
    linea(f, "0 puntos",
          "La vista falta, o su contorno no corresponde a la proyeccion: sobran aristas, faltan "
          "aristas, o estan mal ubicadas.")
    f += 2
    linea(f, "Por ejercicio", "3 vistas x 1 punto = 3 puntos brutos por ejercicio.")
    f += 3

    titulo(f, "3. Ponderacion por nivel"); f += 1
    cab = ["Nivel", "Ejercicios", "Puntos brutos", "Ponderador", "Puntos ponderados"]
    for j, h in enumerate(cab):
        c = wr.cell(row=f, column=2 + j, value=h)
        c.font = Font(name=FUENTE, size=10, bold=True)
        c.fill = PatternFill("solid", fgColor=GRIS_CAB)
        c.alignment = Alignment(horizontal="center")
    fila_tabla = f + 1
    for i, (nombre, n_ej, peso) in enumerate(NIVELES):
        r = fila_tabla + i
        wr.cell(row=r, column=2, value=nombre.capitalize())
        wr.cell(row=r, column=3, value=n_ej)
        wr.cell(row=r, column=4, value="=C%d*3" % r)
        wr.cell(row=r, column=5, value="=Parametros!$C$%d" % (5 + i))
        wr.cell(row=r, column=6, value="=D%d*E%d" % (r, r))
        for j in range(2, 7):
            wr.cell(row=r, column=j).font = Font(name=FUENTE, size=10)
            wr.cell(row=r, column=j).alignment = Alignment(horizontal="center")
        wr.cell(row=r, column=2).alignment = Alignment(horizontal="left")
    rt = fila_tabla + len(NIVELES)
    wr.cell(row=rt, column=2, value="TOTAL").font = Font(name=FUENTE, size=10, bold=True)
    wr.cell(row=rt, column=3, value="=SUM(C%d:C%d)" % (fila_tabla, rt - 1))
    wr.cell(row=rt, column=4, value="=SUM(D%d:D%d)" % (fila_tabla, rt - 1))
    wr.cell(row=rt, column=6, value="=SUM(F%d:F%d)" % (fila_tabla, rt - 1))
    for j in (3, 4, 6):
        wr.cell(row=rt, column=j).font = Font(name=FUENTE, size=10, bold=True)
        wr.cell(row=rt, column=j).alignment = Alignment(horizontal="center")
    for j in range(3, 7):
        wr.column_dimensions[get_column_letter(j + 1)].width = 16
    f = rt + 2
    linea(f, "Lectura", "El puntaje maximo de la actividad es la celda F%d de esta hoja. "
                        "Si cambias un ponderador en la hoja Parametros, se recalcula todo." % rt)
    f += 3

    titulo(f, "4. Disposicion de las vistas (ISO-E)"); f += 1
    linea(f, "Que se exige",
          "En primer diedro la PLANTA va debajo del alzado y el PERFIL IZQUIERDO va a la derecha "
          "del alzado. Las vistas van alineadas entre si: la planta comparte el ancho con el "
          "alzado, y el perfil comparte la altura con el alzado.")
    f += 3
    linea(f, "Como se penaliza",
          "Se evalua por ejercicio, no por vista. Un ejercicio con las tres vistas bien "
          "proyectadas pero dispuestas en tercer diedro (norma americana, ISO-A) descuenta el "
          "valor fijado en Parametros. De este modo un error de criterio no anula tres vistas "
          "que si estaban bien dibujadas.", negrita=True)
    f += 3
    linea(f, "Donde se anota",
          "En la hoja Notas, columna 'Ejercicios en disposicion incorrecta': escribe cuantos "
          "de los 10 ejercicios estan en disposicion equivocada.")
    f += 3

    titulo(f, "5. Formato de entrega"); f += 1
    linea(f, "Que se pidio", "Un unico archivo PDF con los pantallazos.")
    f += 2
    linea(f, "Descuentos",
          "Word descuenta 10 puntos sobre 100. Imagenes sueltas descuentan 20. Los valores "
          "se editan en la hoja Parametros.")
    f += 3

    titulo(f, "6. Calculo de la nota"); f += 1
    linea(f, "Paso 1", "Puntos brutos por nivel = suma de vistas correctas de ese nivel.")
    f += 2
    linea(f, "Paso 2", "Puntos ponderados = puntos brutos x ponderador del nivel.")
    f += 2
    linea(f, "Paso 3", "Se resta la penalizacion por disposicion incorrecta, con piso en cero.")
    f += 2
    linea(f, "Paso 4", "Puntaje base = 100 x puntos obtenidos / puntaje maximo.")
    f += 2
    linea(f, "Paso 5", "Nota final = puntaje base + descuento de formato, con piso en cero.")
    f += 3

    titulo(f, "7. Como llenar la hoja Notas"); f += 1
    linea(f, "Celdas amarillas",
          "Son las unicas que se escriben. Cada ejercicio tiene tres columnas: A (alzado), "
          "P (planta), L (perfil). Escribe 1 si la vista esta correcta y 0 si no. Si prefieres "
          "medio punto en algun caso, tambien acepta 0,5.")
    f += 3
    linea(f, "Celdas celestes",
          "Son formulas. No las escribas: se recalculan solas.")
    f += 2
    linea(f, "Estado",
          "Queda en Pendiente mientras falte llenar alguna de las 30 vistas del alumno.")

    # ============================================================= PARAMETROS
    wp = wb.create_sheet("Parametros")
    wp["A1"] = "PARAMETROS DE CORRECCION - ACTIVIDAD 2"
    wp["A1"].font = Font(name=FUENTE, size=13, bold=True, color=AZUL)
    wp["A2"] = "Cambiar un valor aqui recalcula la hoja Notas y la tabla de la Rubrica."
    wp["A2"].font = Font(name=FUENTE, size=9, italic=True, color="666666")

    wp["A4"] = "Nivel"; wp["B4"] = "Ejercicios"; wp["C4"] = "Ponderador"
    for c in ("A4", "B4", "C4"):
        wp[c].font = Font(name=FUENTE, bold=True)
        wp[c].fill = PatternFill("solid", fgColor=GRIS_CAB)
    for i, (nombre, n_ej, peso) in enumerate(NIVELES):
        r = 5 + i
        wp.cell(row=r, column=1, value=nombre.capitalize()).font = Font(name=FUENTE)
        wp.cell(row=r, column=2, value=n_ej).font = Font(name=FUENTE, color="0000FF")
        cp = wp.cell(row=r, column=3, value=peso)
        cp.font = Font(name=FUENTE, color="0000FF")
        cp.fill = PatternFill("solid", fgColor=AMARILLO)

    wp["A9"] = "Puntos por vista"
    wp["B9"] = 1
    wp["B9"].font = Font(name=FUENTE, color="0000FF")
    wp["B9"].fill = PatternFill("solid", fgColor=AMARILLO)
    wp["A10"] = "Vistas por ejercicio"
    wp["B10"] = 3
    wp["B10"].font = Font(name=FUENTE, color="0000FF")
    wp["A11"] = "Penalizacion por ejercicio en disposicion ISO-A"
    wp["B11"] = -1
    wp["B11"].font = Font(name=FUENTE, color="0000FF")
    wp["B11"].fill = PatternFill("solid", fgColor=AMARILLO)
    wp["A12"] = "PUNTAJE MAXIMO DE LA ACTIVIDAD"
    wp["A12"].font = Font(name=FUENTE, bold=True)
    wp["B12"] = "=SUMPRODUCT($B$5:$B$7,$C$5:$C$7)*$B$9*$B$10"
    wp["B12"].font = Font(name=FUENTE, bold=True)
    for r in range(9, 13):
        wp.cell(row=r, column=1).font = Font(
            name=FUENTE, bold=(r == 12))

    wp["A14"] = "Descuento por formato de entrega"
    wp["A14"].font = Font(name=FUENTE, bold=True)
    wp["A15"] = "Formato"; wp["B15"] = "Descuento"; wp["C15"] = "Criterio"
    for c in ("A15", "B15", "C15"):
        wp[c].font = Font(name=FUENTE, bold=True)
        wp[c].fill = PatternFill("solid", fgColor=GRIS_CAB)
    for i, (nombre, desc, crit) in enumerate(DESCUENTOS):
        r = 16 + i
        wp.cell(row=r, column=1, value=nombre).font = Font(name=FUENTE)
        cd = wp.cell(row=r, column=2, value=desc)
        cd.font = Font(name=FUENTE, color="0000FF")
        cd.fill = PatternFill("solid", fgColor=AMARILLO)
        wp.cell(row=r, column=3, value=crit).font = Font(name=FUENTE, size=9)

    wp["A21"] = ("Fuente de los ponderadores y descuentos: definidos por el profesor. "
                 "Fuente de los niveles: educacionplastica.net/vistas.html (elemental 2x2x2, "
                 "medio 3x3x3, alto con elementos cilindricos y conicos).")
    wp["A21"].font = Font(name=FUENTE, size=9, italic=True, color="666666")
    wp.column_dimensions["A"].width = 44
    wp.column_dimensions["B"].width = 12
    wp.column_dimensions["C"].width = 58

    # ================================================================== NOTAS
    ws = wb.create_sheet("Notas")
    ws["A1"] = "ACTIVIDAD 2 - VISTAS DIEDRICAS EN NORMA ISO-E"
    ws["A1"].font = Font(name=FUENTE, size=14, bold=True, color=AZUL)
    ws["A2"] = contexto.encabezado()
    ws["A2"].font = Font(name=FUENTE, size=10, color="666666")
    ws["A3"] = ("Escribe 1 o 0 en las celdas amarillas (A = alzado, P = planta, L = perfil). "
                "Las celestes son formulas. El detalle del criterio esta en la hoja Rubrica.")
    ws["A3"].font = Font(name=FUENTE, size=9, italic=True, color="806000")
    ws["A3"].fill = PatternFill("solid", fgColor=AMARILLO)

    FIL_EJ = 5      # fila con el nombre del ejercicio (combinada cada 3 columnas)
    FIL_CAB = 6     # fila con A / P / L
    PRIMERA = 7

    fijas = ["N", "Apellidos", "Nombres", "Correo institucional", "Formato de entrega"]
    for j, h in enumerate(fijas, start=1):
        ws.merge_cells(start_row=FIL_EJ, start_column=j, end_row=FIL_CAB, end_column=j)
        c = ws.cell(row=FIL_EJ, column=j, value=h)
        c.font = Font(name=FUENTE, bold=True, size=10)
        c.fill = PatternFill("solid", fgColor=GRIS_CAB)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDE

    col = 6
    bloques = []          # (col_ini, col_fin, nivel, indice_nivel)
    n_ej = 0
    for nivel, cuantos, _ in NIVELES:
        for k in range(cuantos):
            n_ej += 1
            ini = col
            fin = col + 2
            ws.merge_cells(start_row=FIL_EJ, start_column=ini,
                           end_row=FIL_EJ, end_column=fin)
            c = ws.cell(row=FIL_EJ, column=ini,
                        value="Ej %d  %s" % (n_ej, nivel[:4]))
            c.font = Font(name=FUENTE, bold=True, size=9)
            c.fill = PatternFill("solid", fgColor=GRIS_CAB)
            c.alignment = Alignment(horizontal="center", vertical="center")
            for i, (sigla, _nombre) in enumerate(VISTAS):
                d = ws.cell(row=FIL_CAB, column=ini + i, value=sigla)
                d.font = Font(name=FUENTE, bold=True, size=9)
                d.fill = PatternFill("solid", fgColor=GRIS_CAB)
                d.alignment = Alignment(horizontal="center")
                d.border = BORDE
            bloques.append((ini, fin, nivel))
            col = fin + 1

    PRIM_VISTA = 6
    ULT_VISTA = col - 1
    rangos_nivel = {}
    for nivel, _, _ in NIVELES:
        cols = [b for b in bloques if b[2] == nivel]
        rangos_nivel[nivel] = (cols[0][0], cols[-1][1])

    calculadas = [
        ("Ejercicios en disposicion incorrecta", 14, "entrada"),
        ("Puntos elemental", 12, "formula"),
        ("Puntos medio", 11, "formula"),
        ("Puntos alto", 10, "formula"),
        ("Penalizacion disposicion", 13, "formula"),
        ("TOTAL puntos", 11, "formula"),
        ("Puntos maximos", 11, "formula"),
        ("Puntaje base", 11, "formula"),
        ("Descuento formato", 11, "formula"),
        ("NOTA 0-100", 11, "nota"),
        ("Estado", 11, "formula"),
        ("Observaciones", 40, "entrada"),
    ]
    base = ULT_VISTA + 1
    for j, (titulo_col, ancho, tipo) in enumerate(calculadas):
        cc = base + j
        ws.merge_cells(start_row=FIL_EJ, start_column=cc, end_row=FIL_CAB, end_column=cc)
        c = ws.cell(row=FIL_EJ, column=cc, value=titulo_col)
        c.font = Font(name=FUENTE, bold=True, size=9,
                      color="FFFFFF" if tipo == "nota" else "000000")
        c.fill = PatternFill("solid", fgColor=AZUL if tipo == "nota" else GRIS_CAB)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDE
        ws.column_dimensions[get_column_letter(cc)].width = ancho

    C_DISP = base
    C_ELEM = base + 1
    C_MED = base + 2
    C_ALTO = base + 3
    C_PEN = base + 4
    C_TOT = base + 5
    C_MAX = base + 6
    C_PB = base + 7
    C_DESC = base + 8
    C_NOTA = base + 9
    C_EST = base + 10
    C_OBS = base + 11

    L = get_column_letter
    fila = PRIMERA
    for est in nomina:
        ws.cell(row=fila, column=1, value=est["n"]).font = Font(name=FUENTE, size=10)
        ws.cell(row=fila, column=2, value=est["apellidos"]).font = Font(name=FUENTE, size=10)
        ws.cell(row=fila, column=3, value=est["nombres"]).font = Font(name=FUENTE, size=10)
        ws.cell(row=fila, column=4, value=est["correo"]).font = Font(name=FUENTE, size=9)
        cf = ws.cell(row=fila, column=5, value="PDF")
        cf.font = Font(name=FUENTE, size=10, color="0000FF")
        cf.fill = PatternFill("solid", fgColor=AMARILLO)
        cf.alignment = Alignment(horizontal="center")

        for c in range(PRIM_VISTA, ULT_VISTA + 1):
            cel = ws.cell(row=fila, column=c)
            cel.font = Font(name=FUENTE, size=9, color="0000FF")
            cel.fill = PatternFill("solid", fgColor=AMARILLO)
            cel.alignment = Alignment(horizontal="center")
            cel.border = BORDE
            ws.column_dimensions[L(c)].width = 4.2

        cd = ws.cell(row=fila, column=C_DISP, value=0)
        cd.font = Font(name=FUENTE, size=10, color="0000FF")
        cd.fill = PatternFill("solid", fgColor=AMARILLO)
        cd.alignment = Alignment(horizontal="center")
        cd.border = BORDE

        def formula(columna, texto, formato=None, negrita=False):
            c = ws.cell(row=fila, column=columna, value=texto)
            c.font = Font(name=FUENTE, size=10, bold=negrita)
            c.fill = PatternFill("solid", fgColor=CELESTE)
            c.alignment = Alignment(horizontal="center")
            c.border = BORDE
            if formato:
                c.number_format = formato
            return c

        for idx, (nivel, columna) in enumerate(
                [("elemental", C_ELEM), ("medio", C_MED), ("alto", C_ALTO)]):
            ini, fin = rangos_nivel[nivel]
            formula(columna, "=SUM(%s%d:%s%d)*Parametros!$C$%d*Parametros!$B$9"
                    % (L(ini), fila, L(fin), fila, 5 + idx), "0.0")

        formula(C_PEN, "=%s%d*Parametros!$B$11" % (L(C_DISP), fila), "0.0")
        formula(C_TOT, "=MAX(0,%s%d+%s%d+%s%d+%s%d)"
                % (L(C_ELEM), fila, L(C_MED), fila, L(C_ALTO), fila, L(C_PEN), fila),
                "0.0", negrita=True)
        formula(C_MAX, "=Parametros!$B$12", "0.0")
        formula(C_PB, "=IF(%s%d=0,0,100*%s%d/%s%d)"
                % (L(C_MAX), fila, L(C_TOT), fila, L(C_MAX), fila), "0.0")
        formula(C_DESC,
                "=IFERROR(INDEX(Parametros!$B$16:$B$19,MATCH($E%d,Parametros!$A$16:$A$19,0)),0)"
                % fila, "0")

        cn = ws.cell(row=fila, column=C_NOTA,
                     value="=MAX(0,ROUND(%s%d+%s%d,1))" % (L(C_PB), fila, L(C_DESC), fila))
        cn.font = Font(name=FUENTE, size=11, bold=True)
        cn.number_format = "0.0"
        cn.alignment = Alignment(horizontal="center")
        cn.border = Border(left=BORDE_GRUESO, right=BORDE_GRUESO,
                           top=BORDE_GRUESO, bottom=BORDE_GRUESO)

        formula(C_EST,
                ('=IF($E{f}="Sin entrega","Sin entrega",'
                 'IF(COUNT({a}{f}:{b}{f})<{n},"Pendiente","Listo"))').format(
                    f=fila, a=L(PRIM_VISTA), b=L(ULT_VISTA),
                    n=ULT_VISTA - PRIM_VISTA + 1))
        ws.cell(row=fila, column=C_EST).font = Font(name=FUENTE, size=9)

        ws.cell(row=fila, column=C_OBS).font = Font(name=FUENTE, size=9, color="666666")
        fila += 1

    ULTIMA = fila - 1

    # ------------------------------------------------------------- resumen
    fr = ULTIMA + 2
    ws.cell(row=fr, column=2, value="Resumen del curso").font = Font(
        name=FUENTE, bold=True, color=AZUL)
    etiquetas = [
        ("Entregaron", '=COUNTIF($E{a}:$E{b},"<>Sin entrega")'),
        ("No entregaron", '=COUNTIF($E{a}:$E{b},"Sin entrega")'),
        ("Aun pendientes de corregir", '=COUNTIF({e}{a}:{e}{b},"Pendiente")'),
        ("Promedio del curso", "=ROUND(AVERAGE({n}{a}:{n}{b}),1)"),
        ("Promedio de quienes entregaron",
         '=IFERROR(ROUND(SUMIF($E{a}:$E{b},"<>Sin entrega",{n}{a}:{n}{b})/'
         'COUNTIF($E{a}:$E{b},"<>Sin entrega"),1),0)'),
        ("Aprobados (60 o mas)", '=COUNTIF({n}{a}:{n}{b},">=60")'),
        ("Nota mas alta", "=MAX({n}{a}:{n}{b})"),
        ("Nota mas baja", "=MIN({n}{a}:{n}{b})"),
    ]
    for i, (et, fo) in enumerate(etiquetas):
        ws.cell(row=fr + 1 + i, column=2, value=et).font = Font(name=FUENTE, size=10)
        c = ws.cell(row=fr + 1 + i, column=4,
                    value=fo.format(a=PRIMERA, b=ULTIMA, n=L(C_NOTA), e=L(C_EST)))
        c.font = Font(name=FUENTE, size=10, bold=True)
        c.number_format = "0.0"

    # ----------------------------------------------------- validacion y formato
    dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="1",
                        allow_blank=True, showErrorMessage=True)
    dv.errorTitle = "Valor fuera de rango"
    dv.error = "Cada vista vale entre 0 y 1 punto. Escribe 1 si esta correcta, 0 si no."
    ws.add_data_validation(dv)
    dv.add("%s%d:%s%d" % (L(PRIM_VISTA), PRIMERA, L(ULT_VISTA), ULTIMA))

    dvd = DataValidation(type="whole", operator="between", formula1="0", formula2="10",
                         allow_blank=True, showErrorMessage=True)
    dvd.errorTitle = "Valor fuera de rango"
    dvd.error = "Son 10 ejercicios. Escribe cuantos quedaron en disposicion equivocada (0 a 10)."
    ws.add_data_validation(dvd)
    dvd.add("%s%d:%s%d" % (L(C_DISP), PRIMERA, L(C_DISP), ULTIMA))

    dvf = DataValidation(type="list", formula1='"PDF,Word,Imagen,Sin entrega"',
                         allow_blank=False, showErrorMessage=True)
    dvf.errorTitle = "Formato no valido"
    dvf.error = "Elige PDF, Word, Imagen o Sin entrega."
    ws.add_data_validation(dvf)
    dvf.add("E%d:E%d" % (PRIMERA, ULTIMA))

    rango_nota = "%s%d:%s%d" % (L(C_NOTA), PRIMERA, L(C_NOTA), ULTIMA)
    ws.conditional_formatting.add(rango_nota, CellIsRule(
        operator="greaterThanOrEqual", formula=["60"],
        fill=PatternFill("solid", bgColor=VERDE)))
    ws.conditional_formatting.add(rango_nota, CellIsRule(
        operator="between", formula=["40", "59.999"],
        fill=PatternFill("solid", bgColor=AMBAR)))
    ws.conditional_formatting.add(rango_nota, CellIsRule(
        operator="lessThan", formula=["40"],
        fill=PatternFill("solid", bgColor=ROJO)))
    ws.conditional_formatting.add(
        "%s%d:%s%d" % (L(C_EST), PRIMERA, L(C_EST), ULTIMA),
        CellIsRule(operator="equal", formula=['"Pendiente"'],
                   fill=PatternFill("solid", bgColor=AMBAR)))
    # vistas en cero: resaltar suave para leer de un vistazo donde fallo
    ws.conditional_formatting.add(
        "%s%d:%s%d" % (L(PRIM_VISTA), PRIMERA, L(ULT_VISTA), ULTIMA),
        CellIsRule(operator="equal", formula=["0"],
                   fill=PatternFill("solid", bgColor=ROJO)))

    for colu, w in {"A": 5, "B": 24, "C": 22, "D": 32, "E": 15}.items():
        ws.column_dimensions[colu].width = w
    ws.row_dimensions[FIL_EJ].height = 26
    ws.freeze_panes = "F%d" % PRIMERA
    ws.auto_filter.ref = "A%d:%s%d" % (FIL_CAB, L(C_OBS), ULTIMA)

    salida = os.path.join(contexto.seccion_dir(), contexto.nombre_salida("Notas_Actividad2_%s.xlsx"))
    wb.save(salida)
    print("Escrito:", salida)
    print("Estudiantes: %d (filas %d a %d)" % (len(nomina), PRIMERA, ULTIMA))
    print("Columnas de vista: %s a %s (%d celdas por alumno)"
          % (L(PRIM_VISTA), L(ULT_VISTA), ULT_VISTA - PRIM_VISTA + 1))
    print("Columna NOTA:", L(C_NOTA))
    return salida


if __name__ == "__main__":
    try:
        main()
    except contexto.FaltaArchivo as e:
        print("\nNo puedo generar la planilla todavia.\n")
        print(e)
        print("\nDeja la nomina de la seccion en la carpeta de arriba y vuelve a correr esto.")
        raise SystemExit(1)
