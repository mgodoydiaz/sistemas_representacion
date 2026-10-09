#!/usr/bin/env python3
"""
pruebas_tipo.py - Validacion de comparador/tipo_hoja.py (deteccion del tipo
de hoja) y de la verificacion cruzada de servidor.py.

Corre tres bloques, en el orden que pide la tarea:

  1. Las 6 pautas reales de "vistas" y las 6 de "isometricos"
     (salida/pautas/) deben detectarse como su propio tipo. Se corre DOS
     veces: con cv2 disponible (Hough) y forzando el respaldo sin cv2
     (FFT), para probar ambos caminos del modulo.
  2. Verificacion cruzada: comparar un cuadro de isometricos (real, de un
     alumno) contra la pauta de "vistas" debe devolver discrepancia, NO un
     porcentaje.
  3. Reetiquetado (POST /api/hoja/mover_parte, probado llamando
     directamente a las funciones de servidor.py): ida y vuelta con un
     usuario de PRUEBA creado y borrado por este script, verificando en
     disco que los archivos se renombraron, que el manifest quedo
     coherente y que la cache de comparaciones se invalido. No toca datos
     de alumnos reales.

Ejecutar con:  python3 comparador/pruebas_tipo.py
"""
import copy
import json
import os
import shutil
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_AQUI)
sys.path.insert(0, _AQUI)
sys.path.insert(0, _RAIZ)

import numpy as np
from PIL import Image

import tipo_hoja as th  # noqa: E402

PAUTAS_DIR = os.path.join(_RAIZ, "salida", "pautas")
CELDAS_DIR = os.path.join(_RAIZ, "salida", "celdas")

_FALLAS_TOTAL = 0


def _titulo(txt):
    print("\n" + "=" * 78)
    print(txt)
    print("=" * 78)


# =============================================================================
# 1. Las 12 pautas reales
# =============================================================================

def _probar_pautas(forzar_sin_cv2):
    global _FALLAS_TOTAL
    cv2_estado_previo = th._CV2
    if forzar_sin_cv2:
        th._CV2 = False
    etiqueta = "SIN cv2 (respaldo FFT numpy)" if forzar_sin_cv2 else "CON cv2 (Hough probabilistica)"
    _titulo(f"1. Deteccion de tipo sobre las 12 pautas reales -- {etiqueta}")

    if not os.path.isdir(PAUTAS_DIR):
        print(f"  ATENCION: no existe {PAUTAS_DIR}; se omite este bloque.")
        th._CV2 = cv2_estado_previo
        return

    falla_local = 0
    for tipo_esperado in ("vistas", "isometricos"):
        for n in range(1, 7):
            ruta_gris = os.path.join(PAUTAS_DIR, f"pauta_{tipo_esperado}_c{n}.png")
            ruta_trazo = os.path.join(PAUTAS_DIR, f"pauta_{tipo_esperado}_c{n}_trazo.png")
            if not os.path.isfile(ruta_gris):
                print(f"  ATENCION: falta {ruta_gris}, se omite ese cuadro.")
                continue
            resultado = th.detectar_tipo_hoja(ruta_gris, ruta_trazo if os.path.isfile(ruta_trazo) else None)
            ok = resultado["tipo"] == tipo_esperado
            estado = "OK   " if ok else "FALLO"
            if not ok:
                falla_local += 1
            print(
                f"  {estado} pauta_{tipo_esperado}_c{n}: esperado={tipo_esperado:12} "
                f"-> detectado={resultado['tipo']:12} confianza={resultado['confianza']:.3f} "
                f"(reticula={resultado['senales']['reticula']['tipo']}/{resultado['senales']['reticula']['confianza']}, "
                f"trazo={resultado['senales'].get('trazo', {}).get('tipo')}/{resultado['senales'].get('trazo', {}).get('confianza')})"
            )

    print(f"\n  Resultado {etiqueta}: {12 - falla_local}/12 correctas.")
    if falla_local:
        print(f"  *** {falla_local} pauta(s) NO se clasificaron como su propio tipo. ***")
    _FALLAS_TOTAL += falla_local
    th._CV2 = cv2_estado_previo


# =============================================================================
# 2. Verificacion cruzada (servidor.py)
# =============================================================================

def _probar_verificacion_cruzada():
    global _FALLAS_TOTAL
    _titulo("2. Verificacion cruzada: cuadro de isometricos vs. pauta de vistas")

    import servidor as srv  # import tardio: necesita sys.path con RAIZ ya puesto

    # Cuadro real de un alumno, detectado como isometricos con confianza
    # alta en la validacion informal de este mismo modulo (ver LEEME.md):
    # rquintana2026, pagina "isometricos", cuadro 6.
    usuario, pagina, n = "rquintana2026", "isometricos", 6
    manifest = srv.leer_manifest()
    alumno = srv._buscar_alumno(manifest, usuario)
    if alumno is None:
        print(f"  ATENCION: no esta '{usuario}' en el manifest real; se omite este bloque.")
        return
    pag = srv._buscar_pagina_alumno(alumno, pagina)
    celda = srv._buscar_celda(pag, n) if pag else None
    if not celda or not celda.get("trazo"):
        print(f"  ATENCION: no hay cuadro utilizable para {usuario}/{pagina}/{n}; se omite este bloque.")
        return

    ruta_gris = os.path.join(srv.SALIDA_DIR, celda["img"])
    ruta_trazo = os.path.join(srv.SALIDA_DIR, celda["trazo"])
    deteccion = th.detectar_tipo_hoja(ruta_gris, ruta_trazo)
    print(f"  Tipo detectado para {usuario}/{pagina}/c{n}: {deteccion['tipo']} (confianza {deteccion['confianza']:.3f})")

    # Se llama directamente a la verificacion (misma funcion que usa
    # /api/comparacion/comparar antes de calcular el porcentaje), pidiendo
    # a proposito la pauta de "vistas" en vez de la de "isometricos".
    resultado = srv.verificar_tipo_antes_de_comparar(
        usuario, pagina, pag, celda, "vistas", deteccion_tipo=deteccion
    )
    print("  Resultado de verificar_tipo_antes_de_comparar(..., pagina_pauta='vistas'):")
    print(" ", json.dumps(resultado, ensure_ascii=False, indent=2))

    if resultado and resultado.get("discrepancia_tipo") is True:
        print("  OK: se bloqueo la comparacion con discrepancia_tipo (no se devolvio un porcentaje).")
    else:
        print("  *** FALLO: se esperaba discrepancia_tipo=True y no se obtuvo. ***")
        _FALLAS_TOTAL += 1


# =============================================================================
# 3. Reetiquetado (mover_parte) con un usuario de prueba
# =============================================================================

_USUARIO_PRUEBA = "zzz_prueba_tipo_hoja_borrar"


def _crear_pagina_prueba(srv, usuario, pagina):
    """Crea, con datos sinteticos minimos (numpy/PIL, sin depender de
    fotos reales), una pagina completa de 6 cuadros para `usuario` en
    salida/celdas + salida/rectificadas + manifest.json, usando el mismo
    camino que usa el servidor al guardar desde el escaner."""
    celdas = []
    for n in range(1, 7):
        gris = np.full((1000, 1000), 250, dtype=np.uint8)
        gris[100:900, 100:900] = 200  # un cuadrado simple: no importa el contenido para esta prueba
        entrada = {
            "n": n,
            "img": None,
            "trazo": None,
            "tinta": None,
            "componentes": None,
            "vacio": None,
            "esquinas": [[0.0, 0.0], [999.0, 0.0], [999.0, 999.0], [0.0, 999.0]],
        }
        prefijo = f"{usuario}_{pagina}"
        os.makedirs(srv.CELDAS_DIR, exist_ok=True)
        ruta_gris = os.path.join(srv.CELDAS_DIR, f"{prefijo}_c{n}.png")
        Image.fromarray(gris, mode="L").save(ruta_gris)
        entrada["img"] = srv.ruta_relativa_salida(ruta_gris)

        rgba = np.zeros((1000, 1000, 4), dtype=np.uint8)
        rgba[400:600, 400:600, 3] = 255  # un cuadradito de "tinta" en el centro
        ruta_trazo = os.path.join(srv.CELDAS_DIR, f"{prefijo}_c{n}_trazo.png")
        Image.fromarray(rgba, mode="RGBA").save(ruta_trazo)
        entrada["trazo"] = srv.ruta_relativa_salida(ruta_trazo)
        celdas.append(entrada)

    os.makedirs(srv.RECTIFICADAS_DIR, exist_ok=True)
    ruta_hoja = os.path.join(srv.RECTIFICADAS_DIR, f"{usuario}_{pagina}.png")
    Image.fromarray(np.full((1000, 1500, 3), 250, dtype=np.uint8), mode="RGB").save(ruta_hoja)
    hoja_rel = srv.ruta_relativa_salida(ruta_hoja)

    srv.actualizar_manifest_con_celdas(usuario, pagina, celdas, hoja_rel)
    return celdas, hoja_rel


def _archivos_de_pagina(srv, usuario, pagina):
    prefijo = f"{usuario}_{pagina}_c"
    encontrados = []
    if os.path.isdir(srv.CELDAS_DIR):
        for f in os.listdir(srv.CELDAS_DIR):
            if f.startswith(prefijo):
                encontrados.append(f)
    return sorted(encontrados)


def _limpiar_usuario_prueba(srv, usuario):
    """Borra cualquier rastro del usuario de prueba: celdas, rectificadas,
    entrada en el manifest, entradas en la cache de comparaciones y mapas
    de diferencia. Se llama al principio (por si quedo algo de una corrida
    anterior interrumpida) y al final."""
    if os.path.isdir(srv.CELDAS_DIR):
        for f in os.listdir(srv.CELDAS_DIR):
            if f.startswith(usuario + "_"):
                os.remove(os.path.join(srv.CELDAS_DIR, f))
    if os.path.isdir(srv.RECTIFICADAS_DIR):
        for f in os.listdir(srv.RECTIFICADAS_DIR):
            if f.startswith(usuario + "_"):
                os.remove(os.path.join(srv.RECTIFICADAS_DIR, f))
    if os.path.isdir(srv.COMPARACION_DIR):
        for f in os.listdir(srv.COMPARACION_DIR):
            if f.startswith(usuario + "_"):
                os.remove(os.path.join(srv.COMPARACION_DIR, f))

    with srv.MANIFEST_LOCK:
        manifest = srv.leer_manifest()
        antes = len(manifest.get("alumnos", []))
        manifest["alumnos"] = [a for a in manifest.get("alumnos", []) if a.get("usuario") != usuario]
        if len(manifest["alumnos"]) != antes:
            srv.recomputar_resumen(manifest)
            srv.escribir_manifest_atomico(manifest)

    with srv.COMPARACION_LOCK:
        cache = srv._leer_cache_comparacion()
        claves_borrar = [k for k in cache["resultados"] if k.startswith(usuario + "|")]
        if claves_borrar:
            for k in claves_borrar:
                del cache["resultados"][k]
            srv._escribir_cache_comparacion_atomico(cache)


def _probar_mover_parte():
    global _FALLAS_TOTAL
    _titulo("3. Reetiquetado (POST /api/hoja/mover_parte) con usuario de prueba")

    import servidor as srv

    usuario = _USUARIO_PRUEBA
    falla_local = 0

    print(f"  Limpiando restos previos de '{usuario}' (si los hubiera)...")
    _limpiar_usuario_prueba(srv, usuario)

    print(f"  Creando pagina de prueba '{usuario}/vistas' (6 cuadros sinteticos)...")
    _crear_pagina_prueba(srv, usuario, "vistas")
    archivos_antes = _archivos_de_pagina(srv, usuario, "vistas")
    print(f"    Archivos creados en salida/celdas/: {len(archivos_antes)} (esperado 12: 6 img + 6 trazo)")
    if len(archivos_antes) != 12:
        falla_local += 1

    # Fuerza una entrada en la cache de comparaciones para poder comprobar
    # que mover_parte la invalida (sin depender de que exista una pauta
    # real utilizable para esta figura sintetica: se escribe la entrada
    # de cache directamente, como si ya se hubiera comparado antes).
    clave_falsa = srv._clave_cuadro_comparacion(usuario, "vistas", 1)
    ruta_dif_falsa = os.path.join(srv.COMPARACION_DIR, f"{usuario}_vistas_c1_dif.png")
    os.makedirs(srv.COMPARACION_DIR, exist_ok=True)
    Image.fromarray(np.zeros((10, 10, 4), dtype=np.uint8), mode="RGBA").save(ruta_dif_falsa)
    with srv.COMPARACION_LOCK:
        cache = srv._leer_cache_comparacion()
        cache["resultados"][clave_falsa] = {
            "usuario": usuario, "pagina": "vistas", "n": 1, "porcentaje": 42.0,
            "mapa_diferencia": srv.ruta_relativa_salida(ruta_dif_falsa),
            "umbral_alfa": 40, "_mtime_alumno": 0.0, "_mtime_pauta": 0.0,
        }
        srv._escribir_cache_comparacion_atomico(cache)
    print("    Se sembro una entrada falsa en salida/comparacion/resultados.json para el cuadro 1.")

    # --- Ida: vistas -> isometricos ---
    print(f"\n  Reetiquetando '{usuario}': vistas -> isometricos ...")
    resultado = srv.mover_parte_hoja(usuario, "vistas", "isometricos")
    print("   ", json.dumps(resultado, ensure_ascii=False))

    archivos_destino = _archivos_de_pagina(srv, usuario, "isometricos")
    archivos_origen_restantes = _archivos_de_pagina(srv, usuario, "vistas")
    print(f"    Archivos ahora bajo 'isometricos': {len(archivos_destino)} (esperado 12)")
    print(f"    Archivos que quedan bajo 'vistas': {len(archivos_origen_restantes)} (esperado 0)")
    if len(archivos_destino) != 12 or len(archivos_origen_restantes) != 0:
        falla_local += 1

    manifest = srv.leer_manifest()
    alumno = srv._buscar_alumno(manifest, usuario)
    paginas = [p["pagina"] for p in alumno.get("paginas", [])] if alumno else []
    print(f"    Paginas del alumno en el manifest: {paginas} (esperado ['isometricos'])")
    if paginas != ["isometricos"]:
        falla_local += 1

    pag_iso = srv._buscar_pagina_alumno(alumno, "isometricos")
    rutas_manifest_ok = all(
        c["img"].startswith(f"celdas/{usuario}_isometricos_c") for c in pag_iso.get("celdas", [])
    )
    print(f"    Rutas de celdas en el manifest actualizadas: {rutas_manifest_ok}")
    if not rutas_manifest_ok:
        falla_local += 1

    hoja_rel_esperada = f"rectificadas/{usuario}_isometricos.png"
    hoja_ok = pag_iso.get("hoja") == hoja_rel_esperada and os.path.isfile(os.path.join(srv.SALIDA_DIR, hoja_rel_esperada))
    print(f"    Hoja completa renombrada en salida/rectificadas/: {hoja_ok}")
    if not hoja_ok:
        falla_local += 1

    with srv.COMPARACION_LOCK:
        cache = srv._leer_cache_comparacion()
    quedo_clave_vieja = srv._clave_cuadro_comparacion(usuario, "vistas", 1) in cache["resultados"]
    quedo_dif_vieja = os.path.isfile(ruta_dif_falsa)
    print(f"    Cache de comparacion de 'vistas' invalidada: {'OK' if not quedo_clave_vieja else 'FALLO, sigue la entrada vieja'}")
    print(f"    Mapa de diferencia viejo borrado: {'OK' if not quedo_dif_vieja else 'FALLO, sigue en disco'}")
    if quedo_clave_vieja or quedo_dif_vieja:
        falla_local += 1

    # --- Choque: crear de nuevo 'vistas' y probar que mover a una pagina
    #     existente no pisa nada. ---
    print(f"\n  Creando de nuevo '{usuario}/vistas' para probar el choque de destino...")
    _crear_pagina_prueba(srv, usuario, "vistas")
    try:
        srv.mover_parte_hoja(usuario, "vistas", "isometricos")
        print("    *** FALLO: se esperaba un error por choque de destino y no se lanzo. ***")
        falla_local += 1
    except ValueError as e:
        print(f"    OK: se rechazo el choque con un error claro: {e}")

    # --- Vuelta: isometricos -> vistas (limpiando primero la 'vistas' de prueba de choque) ---
    print(f"\n  Limpiando la 'vistas' de prueba de choque y reetiquetando de vuelta: isometricos -> vistas ...")
    for f in _archivos_de_pagina(srv, usuario, "vistas"):
        os.remove(os.path.join(srv.CELDAS_DIR, f))
    ruta_hoja_vistas = os.path.join(srv.RECTIFICADAS_DIR, f"{usuario}_vistas.png")
    if os.path.isfile(ruta_hoja_vistas):
        os.remove(ruta_hoja_vistas)
    with srv.MANIFEST_LOCK:
        manifest = srv.leer_manifest()
        alumno = srv._buscar_alumno(manifest, usuario)
        alumno["paginas"] = [p for p in alumno["paginas"] if p["pagina"] != "vistas"]
        srv.recomputar_resumen(manifest)
        srv.escribir_manifest_atomico(manifest)

    resultado_vuelta = srv.mover_parte_hoja(usuario, "isometricos", "vistas")
    print("   ", json.dumps(resultado_vuelta, ensure_ascii=False))
    archivos_vuelta = _archivos_de_pagina(srv, usuario, "vistas")
    print(f"    Archivos de vuelta bajo 'vistas': {len(archivos_vuelta)} (esperado 12)")
    if len(archivos_vuelta) != 12:
        falla_local += 1

    print(f"\n  Limpiando datos de prueba de '{usuario}'...")
    _limpiar_usuario_prueba(srv, usuario)
    manifest_final = srv.leer_manifest()
    sigue = srv._buscar_alumno(manifest_final, usuario) is not None
    archivos_restantes = _archivos_de_pagina(srv, usuario, "vistas") + _archivos_de_pagina(srv, usuario, "isometricos")
    print(f"    Usuario de prueba sigue en el manifest: {sigue} (esperado False)")
    print(f"    Archivos de prueba restantes en disco: {len(archivos_restantes)} (esperado 0)")
    if sigue or archivos_restantes:
        falla_local += 1

    print(f"\n  Resultado del bloque de reetiquetado: {'OK, sin fallas' if falla_local == 0 else f'{falla_local} falla(s)'}.")
    _FALLAS_TOTAL += falla_local


def main():
    _probar_pautas(forzar_sin_cv2=False)
    _probar_pautas(forzar_sin_cv2=True)
    _probar_verificacion_cruzada()
    _probar_mover_parte()

    _titulo("RESUMEN")
    if _FALLAS_TOTAL == 0:
        print("Todas las pruebas pasaron.")
    else:
        print(f"*** {_FALLAS_TOTAL} prueba(s) fallaron. Revisar el detalle arriba. ***")
    sys.exit(0 if _FALLAS_TOTAL == 0 else 1)


if __name__ == "__main__":
    main()
