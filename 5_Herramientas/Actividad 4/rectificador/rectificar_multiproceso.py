#!/usr/bin/env python3
"""
CLI del rectificador de laminas de la Actividad 4 (Sistemas de Representacion).

Uso:
    python rectificar.py --entradas ../entregas --pautas ../pautas --salida ../salida

Recorre las entregas de los alumnos y las pautas del profesor, corre el
pipeline de nucleo.py sobre cada imagen, y deja en --salida:
    manifest.json
    rectificadas/<usuario>_<pagina>.png
    celdas/<usuario>_<pagina>_c<N>.png
    celdas/<usuario>_<pagina>_c<N>_trazo.png
    pautas/pauta_<pagina>_c<N>.png
    pautas/pauta_<pagina>_c<N>_trazo.png
    _qa/<...>_qa.png          (imagen de control por hoja)
    _qa/REPORTE.md            (tabla de resultados por alumno)

El programa NUNCA aborta por una entrega mala: cualquier error se registra
como aviso/metodo="fallido" y se sigue con la siguiente hoja.

Metodos posibles por pagina (campo "metodo" del manifest):
  - "contornos": las 6 celdas se detectaron por contorno propio (algunas
    pueden haberse reconstruido por homografia de grilla si 1 a 4 de las 6
    no cerraron por contorno; ver avisos).
  - "fallback": no se detectaron los 6 cuadros por contorno; se uso el
    marco exterior de la hoja + un corte proporcional.
  - "cuadro_suelto": la foto es el recorte de UN SOLO cuadro/ejercicio
    (no la lamina completa); se guarda ese cuadro con n=0 si no se pudo
    identificar su numero.
  - "fallido": no se encontro nada aprovechable en la imagen.

Si una foto contiene VARIAS hojas completas fotografiadas juntas, se
detectan y separan automaticamente en varias "paginas" independientes con
el mismo "origen".
"""

import argparse
import datetime
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo as nu


EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png', '.pdf')


def listar_imagenes_alumno(carpeta):
    """Lista, ordenadas, las imagenes a procesar de la carpeta de un alumno
    (fotos .jpg/.jpeg y paginas de PDF ya rasterizadas *_pag-N.png). Se
    ignoran los .pdf originales: se usan solo las imagenes ya rasterizadas.
    """
    archivos = []
    for f in sorted(os.listdir(carpeta)):
        ext = os.path.splitext(f)[1].lower()
        if ext in EXTENSIONES_IMAGEN:
            archivos.append(f)
    return archivos


def siguiente_nombre_pagina(tipo, contador_tipo, contador_desconocida):
    """Decide el nombre de "pagina" para el manifest/archivos, evitando
    colisiones cuando un mismo alumno tiene mas de una hoja del mismo tipo.
    """
    if tipo in ('vistas', 'isometricos'):
        contador_tipo[tipo] = contador_tipo.get(tipo, 0) + 1
        n = contador_tipo[tipo]
        pagina = tipo if n == 1 else f'{tipo}_{n}'
    else:
        contador_desconocida[0] += 1
        pagina = f'desconocida_{contador_desconocida[0]}'
    return pagina


def guardar_celdas(resultado, prefijo, carpeta_celdas, salida_dir):
    """Guarda las imagenes de celda (gris y trazo RGBA) y devuelve la lista
    de dicts para el manifest (con rutas relativas a --salida).
    """
    import numpy as np
    celdas_manifest = []
    for c in resultado['celdas']:
        n = c['n']
        nombre_gris = f'{prefijo}_c{n}.png'
        nombre_trazo = f'{prefijo}_c{n}_trazo.png'
        
        # Guardado seguro para Windows (caracteres Unicode en ruta)
        ruta_abs_gris = os.path.join(carpeta_celdas, nombre_gris)
        cv2.imencode('.png', c['gris'])[1].tofile(ruta_abs_gris)
        
        ruta_abs_trazo = os.path.join(carpeta_celdas, nombre_trazo)
        cv2.imencode('.png', c['rgba'])[1].tofile(ruta_abs_trazo)
        
        ruta_gris = os.path.relpath(ruta_abs_gris, salida_dir)
        ruta_trazo = os.path.relpath(ruta_abs_trazo, salida_dir)
        esquinas = [[round(float(x), 1), round(float(y), 1)] for x, y in c['quad_original']]
        celdas_manifest.append({
            'n': n,
            'img': ruta_gris.replace(os.sep, '/'),
            'trazo': ruta_trazo.replace(os.sep, '/'),
            'tinta': round(float(c['tinta']), 4),
            'componentes': int(c['componentes']),
            'vacio': bool(c['vacio']),
            'esquinas': esquinas,
        })
    return celdas_manifest


def generar_qa(imagen_original, resultado, titulo, out_path):
    """Genera una imagen de control: la hoja original reducida con los 6
    cuadrilateros detectados dibujados y numerados, mas un mosaico de los 6
    recortes (gris con el trazo detectado resaltado en rojo), para que el
    profesor pueda auditar a ojo el resultado.
    """
    max_lado = 1100
    h, w = imagen_original.shape[:2]
    esc = min(1.0, max_lado / max(h, w))
    overlay = cv2.resize(imagen_original, (int(w * esc), int(h * esc))) if esc < 1.0 else imagen_original.copy()

    for c in resultado['celdas']:
        pts = (c['quad_original'] * esc).astype(int)
        color = (0, 200, 0) if not c.get('inferida') else (0, 165, 255)
        cv2.polylines(overlay, [pts], True, color, 3)
        centro = pts.mean(axis=0).astype(int)
        cv2.putText(overlay, str(c['n']), tuple(centro), cv2.FONT_HERSHEY_SIMPLEX,
                    1.3, (255, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(overlay, titulo, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2, cv2.LINE_AA)

    # mosaico de los recortes, mostrando el trazo detectado en rojo sobre el
    # gris de la celda. Normalmente son 6 (grilla 2x3); el caso
    # "cuadro_suelto" trae una sola celda con n=0, que se muestra sola.
    celdas_qa = resultado['celdas']
    es_cuadro_suelto = len(celdas_qa) == 1 and celdas_qa[0]['n'] == 0
    tam_mini = 260
    if es_cuadro_suelto:
        mosaico = np.full((tam_mini, tam_mini, 3), 255, dtype=np.uint8)
    else:
        mosaico = np.full((tam_mini * 2, tam_mini * 3, 3), 255, dtype=np.uint8)
    for c in celdas_qa:
        n = c['n']
        if es_cuadro_suelto:
            fila, col = 0, 0
        else:
            fila, col = (n - 1) // 3, (n - 1) % 3
        gris = c['gris']
        base = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
        alfa = c['rgba'][..., 3].astype(np.float32) / 255.0
        rojo = np.zeros_like(base)
        rojo[..., 2] = 255
        mezcla = (base * (1 - alfa[..., None]) + rojo * alfa[..., None]).astype(np.uint8)
        mini = cv2.resize(mezcla, (tam_mini, tam_mini))
        cv2.putText(mini, str(n), (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
        mosaico[fila * tam_mini:(fila + 1) * tam_mini, col * tam_mini:(col + 1) * tam_mini] = mini

    # apilar overlay (arriba) y mosaico (abajo), igualando anchos
    ancho_final = max(overlay.shape[1], mosaico.shape[1])
    def ajustar_ancho(im):
        if im.shape[1] == ancho_final:
            return im
        return cv2.copyMakeBorder(im, 0, 0, 0, ancho_final - im.shape[1],
                                   cv2.BORDER_CONSTANT, value=(255, 255, 255))
    overlay = ajustar_ancho(overlay)
    mosaico = ajustar_ancho(mosaico)
    franja = np.full((6, ancho_final, 3), 200, dtype=np.uint8)
    final = np.vstack([overlay, franja, mosaico])
    cv2.imencode('.png', final)[1].tofile(out_path)



import concurrent.futures

def procesar_usuario(args):
    usuario, entradas_dir, nombre_entradas, carpeta_rectificadas, carpeta_celdas, salida_dir, carpeta_qa = args
    import os, json, cv2
    import numpy as np
    import rectificador.nucleo as nu
    from rectificador.rectificar import listar_imagenes_alumno, siguiente_nombre_pagina, guardar_celdas, generar_qa

    carpeta_alumno = os.path.join(entradas_dir, usuario)
    archivos = listar_imagenes_alumno(carpeta_alumno)

    contador_tipo = {}
    contador_desconocida = [0]
    paginas_manifest = []
    filas_reporte = []
    resumen = {'ok': 0, 'fallback': 0, 'fallidas': 0}

    for f in archivos:
        path_img = os.path.join(carpeta_alumno, f)
        try:
            resultados_previos = nu.procesar_hoja(path_img)
        except Exception as e:
            resultados_previos = [{'ok': False, 'metodo': 'fallido', 'confianza': 0.0,
                                    'avisos': [f'Excepcion no controlada: {e}'],
                                    'tipo': 'desconocida', 'imagen_rectificada': None, 'celdas': []}]

        for resultado_previo in resultados_previos:
            pagina = siguiente_nombre_pagina(resultado_previo['tipo'], contador_tipo, contador_desconocida)
            prefijo = f'{usuario}_{pagina}'
            ruta_hoja = os.path.join(carpeta_rectificadas, f'{prefijo}.png')

            entrada_manifest = {
                'origen': f'{nombre_entradas}/{usuario}/{f}'.replace(os.sep, '/'),
                'metodo': resultado_previo['metodo'],
                'confianza': round(float(resultado_previo['confianza']), 3),
                'avisos': resultado_previo['avisos'],
                'celdas': [],
            }
            if resultado_previo['celdas']:
                entrada_manifest['celdas'] = guardar_celdas(resultado_previo, prefijo, carpeta_celdas, salida_dir)
            hoja_guardada = False
            if resultado_previo.get('imagen_rectificada') is not None:
                cv2.imencode('.png', resultado_previo['imagen_rectificada'])[1].tofile(ruta_hoja)
                hoja_guardada = True

            try:
                img_orig = nu.cargar_bgr(path_img)
                nombre_qa = os.path.join(carpeta_qa, f'{prefijo}_qa.png')
                if resultado_previo['celdas']:
                    generar_qa(img_orig, resultado_previo, f'{usuario} / {pagina}', nombre_qa)
                else:
                    h, w = img_orig.shape[:2]
                    esc = min(1.0, 900 / max(h, w))
                    vis = cv2.resize(img_orig, (int(w * esc), int(h * esc))) if esc < 1.0 else img_orig.copy()
                    cv2.putText(vis, f'{usuario}/{pagina}: FALLIDO', (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.imencode('.png', vis)[1].tofile(nombre_qa)
            except Exception as e:
                entrada_manifest['avisos'].append(f'No se pudo generar la imagen de control (QA): {e}')

            entrada_pagina = {
                'pagina': pagina,
                'origen': entrada_manifest['origen'],
                'hoja': (os.path.relpath(ruta_hoja, salida_dir).replace(os.sep, '/')
                         if hoja_guardada else None),
                'metodo': entrada_manifest['metodo'],
                'confianza': entrada_manifest['confianza'],
                'avisos': entrada_manifest['avisos'],
                'celdas': entrada_manifest['celdas'],
            }
            paginas_manifest.append(entrada_pagina)

            if entrada_manifest['metodo'] == 'contornos':
                resumen['ok'] += 1
            elif entrada_manifest['metodo'] == 'fallido':
                resumen['fallidas'] += 1
            else:
                resumen['fallback'] += 1

            filas_reporte.append({
                'usuario': usuario, 'pagina': pagina, 'metodo': entrada_manifest['metodo'],
                'confianza': entrada_manifest['confianza'],
                'avisos': '; '.join(entrada_manifest['avisos']),
                'n_celdas': len(entrada_manifest['celdas']),
            })
            f_safe = f.encode('cp1252', errors='replace').decode('cp1252')
            print(f'    {f_safe}: pagina={pagina} metodo={entrada_manifest["metodo"]} confianza={entrada_manifest["confianza"]}', flush=True)

    return {'usuario': usuario, 'paginas': paginas_manifest}, resumen, filas_reporte

def ejecutar_multiproceso(usuarios, entradas_dir, nombre_entradas, carpeta_rectificadas, carpeta_celdas, salida_dir, carpeta_qa):
    tareas = [(u, entradas_dir, nombre_entradas, carpeta_rectificadas, carpeta_celdas, salida_dir, carpeta_qa) for u in usuarios]
    alumnos_manifest = []
    resumen_total = {'paginas_ok': 0, 'paginas_fallback': 0, 'paginas_fallidas': 0}
    filas_reporte_total = []
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        for res_usuario, res_stats, res_filas in executor.map(procesar_usuario, tareas):
            alumnos_manifest.append(res_usuario)
            resumen_total['paginas_ok'] += res_stats['ok']
            resumen_total['paginas_fallback'] += res_stats['fallback']
            resumen_total['paginas_fallidas'] += res_stats['fallidas']
            filas_reporte_total.extend(res_filas)
            
    return alumnos_manifest, resumen_total, filas_reporte_total

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--entradas', required=True, help='Carpeta con las subcarpetas de cada alumno (entregas/)')
    ap.add_argument('--pautas', required=True, help='Carpeta con las pautas del profesor (pautas/)')
    ap.add_argument('--salida', required=True, help='Carpeta de salida (se crea si no existe)')
    args = ap.parse_args()

    entradas_dir = os.path.abspath(args.entradas)
    pautas_dir = os.path.abspath(args.pautas)
    salida_dir = os.path.abspath(args.salida)

    nombre_entradas = os.path.basename(entradas_dir.rstrip(os.sep)) or 'entregas'
    nombre_pautas = os.path.basename(pautas_dir.rstrip(os.sep)) or 'pautas'

    carpeta_rectificadas = os.path.join(salida_dir, 'rectificadas')
    carpeta_celdas = os.path.join(salida_dir, 'celdas')
    carpeta_pautas_out = os.path.join(salida_dir, 'pautas')
    carpeta_qa = os.path.join(salida_dir, '_qa')
    for d in (salida_dir, carpeta_rectificadas, carpeta_celdas, carpeta_pautas_out, carpeta_qa):
        os.makedirs(d, exist_ok=True)

    manifest = {
        'version': 1,
        'generado': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        # se inicializan ambas claves esperadas por el contrato de salida
        # aunque alguna pauta no llegue a clasificarse con confianza.
        'pautas': {'vistas': {'celdas': []}, 'isometricos': {'celdas': []}},
        'alumnos': [],
        'resumen': {'alumnos': 0, 'paginas_ok': 0, 'paginas_fallback': 0, 'paginas_fallidas': 0},
    }

    filas_reporte = []

    # ------------------------------------------------------------------
    # 1) Pautas del profesor: pasan por el MISMO pipeline.
    # ------------------------------------------------------------------
    print('Procesando pautas del profesor...')
    if os.path.isdir(pautas_dir):
        archivos_pauta = [f for f in sorted(os.listdir(pautas_dir))
                           if os.path.splitext(f)[1].lower() in EXTENSIONES_IMAGEN]
    else:
        archivos_pauta = []

    for f in archivos_pauta:
        path_img = os.path.join(pautas_dir, f)
        print(f'  pauta: {f}')
        # nombre provisorio para archivos (se ajusta segun el tipo detectado)
        # Las pautas son 1 sola hoja por archivo: se usa el primer resultado
        # (procesar_hoja devuelve una lista solo por si detecta varias
        # hojas fotografiadas juntas, caso que no aplica a las pautas).
        resultado = nu.procesar_hoja(path_img)[0]
        base_f = os.path.splitext(f)[0]
        tipo = resultado['tipo'] if resultado['tipo'] in ('vistas', 'isometricos') else f'desconocida_{base_f}'
        prefijo = f'pauta_{tipo}'
        entrada_manifest = {
            'origen': f'{nombre_pautas}/{f}'.replace(os.sep, '/'),
            'metodo': resultado['metodo'],
            'confianza': round(float(resultado['confianza']), 3),
            'avisos': resultado['avisos'],
            'celdas': [],
        }
        if resultado['celdas']:
            entrada_manifest['celdas'] = guardar_celdas(resultado, prefijo, carpeta_pautas_out, salida_dir)
        try:
            img_orig = nu.cargar_bgr(path_img)
            nombre_qa = os.path.join(carpeta_qa, f'{prefijo}_qa.png')
            if resultado['celdas']:
                generar_qa(img_orig, resultado, f'PAUTA {tipo}', nombre_qa)
        except Exception as e:
            resultado['avisos'].append(f'No se pudo generar QA de la pauta: {e}')

        manifest['pautas'][tipo] = {'celdas': [
            {'n': c['n'], 'img': c['img'], 'trazo': c['trazo']} for c in entrada_manifest['celdas']
        ]}
        filas_reporte.append({
            'usuario': '(pauta)', 'pagina': tipo, 'metodo': resultado['metodo'],
            'confianza': entrada_manifest['confianza'], 'avisos': '; '.join(resultado['avisos']),
            'n_celdas': len(entrada_manifest['celdas']),
        })
        print(f'    -> tipo={tipo} metodo={resultado["metodo"]} confianza={entrada_manifest["confianza"]}')

    # ------------------------------------------------------------------
    # 2) Entregas de los alumnos.
    # ------------------------------------------------------------------
    print('Procesando entregas de alumnos...')
    usuarios = sorted([d for d in os.listdir(entradas_dir)
                        if os.path.isdir(os.path.join(entradas_dir, d))])


    alumnos_manifest, resumen_total, filas_reporte_total = ejecutar_multiproceso(
        usuarios, entradas_dir, nombre_entradas, carpeta_rectificadas, carpeta_celdas, salida_dir, carpeta_qa)

    manifest['alumnos'].extend(alumnos_manifest)
    manifest['resumen']['paginas_ok'] += resumen_total['paginas_ok']
    manifest['resumen']['paginas_fallback'] += resumen_total['paginas_fallback']
    manifest['resumen']['paginas_fallidas'] += resumen_total['paginas_fallidas']
    filas_reporte.extend(filas_reporte_total)
    
    manifest['resumen']['alumnos'] = len(usuarios)

    with open(os.path.join(salida_dir, 'manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 3) Reporte de QA en markdown.
    # ------------------------------------------------------------------
    reporte_path = os.path.join(carpeta_qa, 'REPORTE.md')
    with open(reporte_path, 'w', encoding='utf-8') as fh:
        fh.write('# Reporte de rectificacion - Actividad 4\n\n')
        fh.write(f'Generado: {manifest["generado"]}\n\n')
        r = manifest['resumen']
        fh.write(f'Alumnos: {r["alumnos"]}  \n')
        fh.write(f'Paginas OK (contornos): {r["paginas_ok"]}  \n')
        fh.write(f'Paginas con metodo de respaldo (fallback / cuadro_suelto): {r["paginas_fallback"]}  \n')
        fh.write(f'Paginas fallidas: {r["paginas_fallidas"]}\n\n')
        fh.write('| Usuario | Pagina | Metodo | Confianza | Celdas | Avisos |\n')
        fh.write('|---|---|---|---|---|---|\n')
        for fila in filas_reporte:
            avisos = fila['avisos'].replace('|', '/').replace('\n', ' ') if fila['avisos'] else ''
            fh.write(f'| {fila["usuario"]} | {fila["pagina"]} | {fila["metodo"]} | '
                     f'{fila["confianza"]:.2f} | {fila["n_celdas"]} | {avisos} |\n')

    print('\nListo.')
    print(f'  Alumnos procesados: {manifest["resumen"]["alumnos"]}')
    print(f'  Paginas OK: {manifest["resumen"]["paginas_ok"]}')
    print(f'  Paginas fallback: {manifest["resumen"]["paginas_fallback"]}')
    print(f'  Paginas fallidas: {manifest["resumen"]["paginas_fallidas"]}')
    print(f'  Manifest: {os.path.join(salida_dir, "manifest.json")}')
    print(f'  Reporte QA: {reporte_path}')


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
