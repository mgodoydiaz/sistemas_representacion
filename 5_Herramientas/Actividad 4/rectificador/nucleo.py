"""
Nucleo del rectificador de laminas de la Actividad 4 (Sistemas de Representacion).

Contiene todas las funciones reutilizables del pipeline:
  - carga y normalizacion de imagenes (correccion de iluminacion/sombras)
  - deteccion de los 6 cuadros de la hoja como cuadrilateros (no por plantilla fija)
  - deteccion de la rotacion de la hoja usando la posicion del recuadro del numero
  - rectificacion (homografia) de cada cuadro a 1000x1000
  - clasificacion de la hoja en "vistas" / "isometricos" / "desconocida"
  - separacion de la capa de trazo (lapiz del alumno) respecto de la reticula impresa
  - metricas de tinta por celda
  - metodo de respaldo (fallback) por proporciones cuando no se detectan los 6 cuadros

Todo el codigo esta comentado en espanol. Sin dependencias pesadas: solo
cv2, numpy y PIL.
"""

import math
import numpy as np
import cv2

import fitz
import os

def cargar_imagenes(path):
    """Carga una imagen a color (BGR) o extrae todas las paginas de un PDF.
    Devuelve una lista de imagenes numpy en formato BGR. Lanza IOError si falla."""
    ext = os.path.splitext(path)[1].lower()
    imgs = []
    try:
        if ext == '.pdf':
            doc = fitz.open(path)
            for page in doc:
                pix = page.get_pixmap(dpi=150)
                # Convertir a numpy array y de RGB a BGR para OpenCV
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                elif pix.n == 1:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                imgs.append(img)
            doc.close()
        else:
            file_bytes = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is not None:
                imgs.append(img)
    except Exception as e:
        pass
    if not imgs:
        raise IOError(f"No se pudo leer la imagen o PDF: {path}")
    return imgs


def redimensionar_para_deteccion(img, max_lado=1600):
    """Devuelve una copia reducida (para acelerar la deteccion) y la escala usada.

    La escala permite volver a proyectar coordenadas detectadas en la imagen
    chica hacia la imagen ORIGINAL (de mayor resolucion), que es la que se usa
    para el warpPerspective final (mejor calidad) y para reportar las esquinas
    en el manifest.
    """
    h, w = img.shape[:2]
    esc = min(1.0, max_lado / float(max(h, w)))
    if esc < 1.0:
        nuevo = cv2.resize(img, (int(round(w * esc)), int(round(h * esc))),
                            interpolation=cv2.INTER_AREA)
    else:
        nuevo = img.copy()
        esc = 1.0
    return nuevo, esc


def corregir_iluminacion(gray):
    """Corrige iluminacion despareja / sombras de foto de celular.

    Estima el "fondo" (papel) con un cierre morfologico de kernel grande
    (que borra el trazo fino pero conserva la tendencia de brillo del papel)
    y divide la imagen original por ese fondo, reescalando al nivel de gris
    mediano del fondo. Esto aplana sombras y viñeteo de manera robusta.
    """
    h, w = gray.shape
    k = max(15, (min(h, w) // 10) | 1)  # impar, proporcional al tamano de imagen
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    fondo = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    fondo_f = fondo.astype(np.float32) + 1.0
    norm = gray.astype(np.float32) / fondo_f * float(np.median(fondo))
    return np.clip(norm, 0, 255).astype(np.uint8)


def order_points(pts):
    """Ordena 4 puntos como (superior-izq, superior-der, inferior-der, inferior-izq)
    usando el truco clasico de suma/diferencia de coordenadas. Esta funcion
    asume una rotacion menor a ~45 grados respecto de los ejes de la imagen;
    la correccion de rotaciones de 90/180/270 grados se hace aparte (ver
    votar_rotacion / reindexar_esquinas).
    """
    pts = np.array(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).reshape(-1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(d)]
    bl = pts[np.argmax(d)]
    return np.array([tl, tr, br, bl], dtype=np.float32)


def _rotar_punto(pt, k, w, h):
    """Rota un punto (x,y) de una imagen de tamano (w,h) en pasos de 90 grados
    horario (k=0,1,2,3). Se usa solo para calcular el recorte de la hoja
    "enderezada" de vista previa; el recorte de cada celda NUNCA rota la
    imagen fisicamente, solo reindexa las esquinas (ver reindexar_esquinas).
    """
    x, y = pt
    k = k % 4
    if k == 0:
        return (x, y)
    if k == 1:  # 90 horario
        return (h - 1 - y, x)
    if k == 2:  # 180
        return (w - 1 - x, h - 1 - y)
    # k == 3, 90 antihorario
    return (y, w - 1 - x)


_ROT_CONST = {0: None, 1: cv2.ROTATE_90_CLOCKWISE, 2: cv2.ROTATE_180,
              3: cv2.ROTATE_90_COUNTERCLOCKWISE}


def rotar_imagen(img, k):
    """Rota una imagen k pasos de 90 grados horario (0..3)."""
    c = _ROT_CONST.get(k % 4)
    if c is None:
        return img.copy()
    return cv2.rotate(img, c)


# Mapa de la esquina donde aparece el recuadrito del numero -> pasos de
# rotacion horaria "k" que hay que aplicar (reindexando esquinas) para que
# esa esquina pase a ser la superior-izquierda real. Ver justificacion en el
# desarrollo: se calibro y verifico contra pauta_p2_vistas.png.
_CORNER_TO_K = {'TL': 0, 'BL': 1, 'BR': 2, 'TR': 3}


def reindexar_esquinas(pts_tlbrbl, k):
    """Dadas 4 esquinas ya ordenadas por order_points (TL,TR,BR,BL segun los
    EJES de la imagen), devuelve las esquinas reordenadas para que el indice
    0 sea la verdadera esquina superior-izquierda de la lamina (considerando
    que la hoja puede estar rotada k*90 grados horario dentro de la foto).
    """
    p = list(pts_tlbrbl)
    return np.array([p[(i - k) % 4] for i in range(4)], dtype=np.float32)


# ---------------------------------------------------------------------------
# Deteccion de los 6 cuadros
# ---------------------------------------------------------------------------

def _angulos_cercanos_90(quad, tol=32):
    """True si los 4 angulos internos del cuadrilatero (ya ordenado o no)
    estan dentro de `tol` grados de 90. Se usa para descartar paralelogramos
    (por ejemplo caras de un solido isometrico) que un approxPolyDP de 4
    vertices podria dejar pasar. Compartida por todos los detectores de
    cuadrilateros del modulo (celdas, marco exterior, cuadro suelto, hojas
    multiples) para no repetir el calculo.
    """
    qo = order_points(quad)
    for i in range(4):
        p0 = qo[(i - 1) % 4]
        p1 = qo[i]
        p2 = qo[(i + 1) % 4]
        v1 = p0 - p1
        v2 = p2 - p1
        cos_ang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        ang_deg = math.degrees(math.acos(np.clip(cos_ang, -1, 1)))
        if abs(ang_deg - 90) > tol:
            return False
    return True


def _mascara_lineas(gray_corr, params=(31, 7, 9)):
    """A partir de la imagen con iluminacion corregida, obtiene una mascara
    binaria de "lineas" (trazo + reticula + marcos) mediante umbral adaptativo
    y un cierre morfologico que sella pequenos cortes en los trazos.
    """
    block, C, close_k = params
    med = cv2.medianBlur(gray_corr, 5)
    th = cv2.adaptiveThreshold(med, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, block, C)
    lineas = cv2.morphologyEx(th, cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k)))
    return th, lineas


# Distintas combinaciones de (blockSize, C, kernel_de_cierre) para el umbral
# adaptativo. No hay un unico ajuste que sirva igual de bien para una foto de
# celular con sombra (contraste desparejo, requiere blockSize/C mas chicos)
# que para un escaneo limpio con reticula impresa muy fina (requiere un
# cierre mas grande para sellar los cortes de la reticula sin que esta se
# vuelva tan solida como para tapar el interior de cada celda). Se prueban
# varias combinaciones y se usa la que logre encontrar las 6 celdas (o al
# menos la que mas celdas coherentes entregue).
_PARAMS_UMBRAL = [
    (31, 7, 9),
    (31, 6, 9),
    (31, 5, 9),
    (25, 3, 9),
    (31, 8, 9),
    (31, 4, 13),
    (41, 5, 13),
    (21, 3, 9),
    (41, 5, 21),
    (31, 5, 15),
    (31, 3, 9),
    (41, 4, 9),
    (41, 7, 9),
    (31, 7, 13),
    (31, 2, 9),
    (31, 2, 13),
    (31, 2, 17),
    # Combinaciones con cierre morfologico mucho mas grande: sirven para
    # fotos nitidas y bien iluminadas donde, aun asi, el borde impreso de
    # cada cuadro es muy fino/parejo con la reticula de fondo (por ejemplo
    # reticulas triangulares muy tenues) y queda cortado en segmentos que
    # un cierre chico (9-21) no logra sellar.
    (31, 9, 31),
    (31, 9, 35),
    (41, 9, 31),
    (31, 8, 31),
    (31, 7, 31),
    (41, 8, 35),
]


def _limpiar_dibujos_grilla(lineas_mask):
    """
    Filtro morfológico direccional para aislar la grilla de la pagina, borrando dibujos de los estudiantes.
    Se extraen lineas verticales y horizontales largas, y se combinan.
    """
    # Aislar lineas verticales
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35))
    lineas_v = cv2.morphologyEx(lineas_mask, cv2.MORPH_OPEN, kernel_v)
    
    # Aislar lineas horizontales
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1))
    lineas_h = cv2.morphologyEx(lineas_mask, cv2.MORPH_OPEN, kernel_h)
    
    # Unir ambas
    grilla = cv2.add(lineas_v, lineas_h)
    
    # Expandir levemente para asegurar que las intersecciones se toquen
    grilla = cv2.morphologyEx(grilla, cv2.MORPH_DILATE, np.ones((5, 5), np.uint8))
    
    # Sellar los cortes para formar polígonos cerrados
    grilla = cv2.morphologyEx(grilla, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return grilla


def detectar_celdas_candidatas(gray_corr, params=(31, 7, 9)):
    """Detecta candidatos a "cuadro" (celda) de la hoja buscando directamente
    los contornos cerrados de la mascara de lineas (umbral adaptativo +
    cierre morfologico) cuyo approxPolyDP da 4 vertices (o, en su defecto,
    su minAreaRect), con area entre ~2%% y ~26%% del area de la hoja y
    relacion de aspecto razonable (los 6 cuadros de la lamina).

    Como cada linea impresa/dibujada tiene grosor, su contorno aparece
    duplicado (borde interior y borde exterior del trazo) con centroides
    practicamente identicos; estos duplicados se filtran quedandose con el
    de mayor area (el borde exterior).

    Devuelve una lista de dicts: {quad, area, cx, cy, w, h, rectangularidad}
    con las coordenadas en el sistema de la imagen que se le paso (normalmente
    la version reducida usada para deteccion).
    """
    th, lineas = _mascara_lineas(gray_corr, params)
    
    # NUEVO: Aislar solo la grilla descartando el trazo del estudiante
    lineas_limpias = _limpiar_dibujos_grilla(lineas)
    
    cnts, _ = cv2.findContours(lineas_limpias, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    h, w = gray_corr.shape[:2]
    area_img = h * w
    brutos = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 0.02 * area_img or a > 0.26 * area_img:
            continue
        # Se exige que el contorno reduzca a EXACTAMENTE 4 vertices convexos:
        # esto descarta formas complejas (por ejemplo, caras de solidos
        # isometricos dibujados por el alumno/pauta) que con minAreaRect
        # podrian "disfrazarse" de rectangulo aunque no lo sean. El epsilon
        # de approxPolyDP se prueba en varios niveles: un contorno "ruidoso"
        # (brillo/reflejo, jpg con artefactos) puede necesitar un epsilon
        # mas grande para simplificar a 4 vertices limpios.
        peri = cv2.arcLength(c, True)
        quad = None
        for eps_rel in (0.02, 0.03, 0.045, 0.06):
            approx = cv2.approxPolyDP(c, eps_rel * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                quad = approx.reshape(4, 2).astype(np.float32)
                break
        if quad is None:
            continue
        rect = cv2.minAreaRect(c)
        (rcx, rcy), (rw, rh), _ang = rect
        area_rect = rw * rh
        if area_rect <= 0:
            continue
        rectangularidad = a / area_rect
        if rectangularidad < 0.60:
            continue
        aspecto = rw / rh if rh > 0 else 0.0
        if aspecto < 0.40 or aspecto > 2.5:
            continue
        # Angulos internos del cuadrilatero cercanos a 90 grados: esto
        # descarta paralelogramos (caras de un solido en isometrico, con
        # angulos de ~60/120 grados) que igual podrian aprobar approxPolyDP.
        if not _angulos_cercanos_90(quad, tol=32):
            continue
        brutos.append({
            'quad': quad, 'area': float(a), 'cx': float(rcx), 'cy': float(rcy),
            'w': float(rw), 'h': float(rh), 'rectangularidad': float(rectangularidad),
        })

    # deduplicar contornos anidados (borde interior/exterior de la misma linea)
    brutos.sort(key=lambda d: -d['area'])
    finales = []
    for b in brutos:
        es_dup = False
        for f in finales:
            dist = math.hypot(b['cx'] - f['cx'], b['cy'] - f['cy'])
            tam = max(b['w'], b['h'], f['w'], f['h'])
            if dist < 0.12 * tam:
                es_dup = True
                break
        if not es_dup:
            finales.append(b)
    return finales


def _kmeans_1d_2grupos(valores):
    """K-means simple para 1 dimension con 2 centros (usado para separar filas
    o columnas). Determinista: parte de min y max como semillas.
    """
    vals = np.array(valores, dtype=np.float64)
    c0, c1 = vals.min(), vals.max()
    if c0 == c1:
        return np.zeros(len(vals), dtype=int), [c0, c1]
    for _ in range(20):
        d0 = np.abs(vals - c0)
        d1 = np.abs(vals - c1)
        grupo = (d1 < d0).astype(int)
        nuevo_c0 = vals[grupo == 0].mean() if np.any(grupo == 0) else c0
        nuevo_c1 = vals[grupo == 1].mean() if np.any(grupo == 1) else c1
        if abs(nuevo_c0 - c0) < 1e-3 and abs(nuevo_c1 - c1) < 1e-3:
            c0, c1 = nuevo_c0, nuevo_c1
            break
        c0, c1 = nuevo_c0, nuevo_c1
    return grupo, [c0, c1]


def _forma_grilla(candidatos):
    """Determina si la hoja (en el sistema de EJES de la imagen de entrada)
    presenta forma de 2 filas x 3 columnas (apaisada) o 3 filas x 2 columnas
    (hoja escaneada en retrato con el contenido rotado 90 grados, como pasa
    con las pautas del profesor). Se decide por el rango espacial que cubren
    los centroides: si se extienden mas en X que en Y, hay 3 columnas
    (2 filas x 3 columnas); si se extienden mas en Y, hay 3 filas (3x2).
    """
    cxs = [c['cx'] for c in candidatos]
    cys = [c['cy'] for c in candidatos]
    rango_x = max(cxs) - min(cxs)
    rango_y = max(cys) - min(cys)
    if rango_x >= rango_y:
        return 2, 3
    return 3, 2


def _kmeans_1d_ngrupos(valores, n):
    """K-means simple para 1 dimension con n centros, semillas equiespaciadas."""
    vals = np.array(valores, dtype=np.float64)
    if len(np.unique(vals)) < n:
        # no hay suficiente variedad; se reparte por orden
        orden = np.argsort(vals)
        grupo = np.zeros(len(vals), dtype=int)
        for rango, idx in enumerate(orden):
            grupo[idx] = min(rango * n // len(vals), n - 1)
        centros = [vals[grupo == g].mean() if np.any(grupo == g) else 0 for g in range(n)]
        return grupo, centros
    centros = np.linspace(vals.min(), vals.max(), n)
    for _ in range(30):
        dists = np.abs(vals[:, None] - centros[None, :])
        grupo = np.argmin(dists, axis=1)
        nuevos = np.array([vals[grupo == g].mean() if np.any(grupo == g) else centros[g]
                            for g in range(n)])
        if np.allclose(nuevos, centros, atol=1e-3):
            centros = nuevos
            break
        centros = nuevos
    return grupo, list(centros)


def _asignar_grilla(candidatos):
    """Agrupa candidatos en una grilla (n_filas x n_columnas, con
    n_filas*n_columnas == 6) segun su centroide. La forma de la grilla
    (2x3 o 3x2) se determina automaticamente segun la disposicion espacial
    de los candidatos (ver _forma_grilla), para soportar tanto hojas
    apaisadas fotografiadas de frente como hojas escaneadas en retrato con
    el contenido rotado 90 grados (caso de las pautas del profesor).

    Devuelve (grilla, n_filas, n_columnas) donde grilla es una lista de
    listas con el candidato asignado a cada casilla, o None si no hay.
    """
    n_filas, n_cols = _forma_grilla(candidatos)
    cys = [c['cy'] for c in candidatos]
    grupo_fila, centros_fila = _kmeans_1d_ngrupos(cys, n_filas)
    orden_filas = np.argsort(centros_fila)  # de menor a mayor cy
    mapa_fila = {viejo: nuevo for nuevo, viejo in enumerate(orden_filas)}
    grupo_fila = np.array([mapa_fila[g] for g in grupo_fila])

    grilla = [[None] * n_cols for _ in range(n_filas)]
    todos_cx = [c['cx'] for c in candidatos]
    xmin, xmax = min(todos_cx), max(todos_cx)
    objetivo = [xmin + i * (xmax - xmin) / max(1, n_cols - 1) for i in range(n_cols)] \
        if n_cols > 1 else [((xmin + xmax) / 2.0)]

    for fila in range(n_filas):
        de_fila = [c for c, g in zip(candidatos, grupo_fila) if g == fila]
        if len(de_fila) == 0:
            continue
        de_fila_ordenados = sorted(de_fila, key=lambda c: c['cx'])
        if len(de_fila_ordenados) == n_cols:
            for col, c in enumerate(de_fila_ordenados):
                grilla[fila][col] = c
        else:
            # cantidad distinta a la esperada: asignar por cercania a las
            # posiciones X objetivo, priorizando los candidatos de mayor area
            usados = set()
            for c in sorted(de_fila, key=lambda c: -c['area']):
                dists = [abs(c['cx'] - o) if col not in usados else 1e18
                         for col, o in enumerate(objetivo)]
                col = int(np.argmin(dists))
                if grilla[fila][col] is None:
                    grilla[fila][col] = c
                    usados.add(col)
    return grilla, n_filas, n_cols


def _inferir_celda_faltante(grilla, n_filas, n_cols):
    """Si falta exactamente UNA celda en la grilla, la infiere a partir de
    la geometria de las celdas vecinas (misma fila / misma columna), asumiendo
    que los bordes compartidos entre celdas adyacentes estan alineados. Aviso:
    esto asume una perspectiva suave (aceptable dado que ya se corrigio
    iluminacion y se trabaja a resolucion moderada).
    Devuelve (grilla_completa, aviso) o (grilla, None) si no se pudo inferir.
    """
    faltantes = [(f, c) for f in range(n_filas) for c in range(n_cols) if grilla[f][c] is None]
    if len(faltantes) != 1:
        return grilla, None
    f, c = faltantes[0]
    filas_candidatas = [ff for ff in range(n_filas) if ff != f and grilla[ff][c] is not None]
    if not filas_candidatas:
        return grilla, None
    fila_op = filas_candidatas[0]
    # celda en la misma columna, otra fila (para tomar el ancho / posicion x)
    vecino_col = grilla[fila_op][c]
    # celdas en la misma fila, otras columnas (para tomar la altura / posicion y)
    vecinos_fila = [grilla[f][cc] for cc in range(n_cols) if cc != c and grilla[f][cc] is not None]
    if vecino_col is None or len(vecinos_fila) == 0:
        return grilla, None

    # Altura de la celda faltante: promedio de alturas de las celdas de su fila
    alturas = [np.linalg.norm(v['quad'][3] - v['quad'][0]) for v in vecinos_fila]
    alturas += [np.linalg.norm(v['quad'][2] - v['quad'][1]) for v in vecinos_fila]
    h_est = float(np.mean(alturas))
    # Ancho: el de la celda vecina en la misma columna (otra fila)
    w_top = np.linalg.norm(vecino_col['quad'][1] - vecino_col['quad'][0])
    w_bot = np.linalg.norm(vecino_col['quad'][2] - vecino_col['quad'][3])
    w_est = float((w_top + w_bot) / 2.0)

    # Posicion horizontal: se hereda de la celda de la misma columna
    # Posicion vertical: se ubica arriba o abajo de la fila conocida, usando
    # como referencia una celda de la fila conocida mas cercana en columna.
    vecino_fila_cercano = min(vecinos_fila, key=lambda v: abs(v['cx'] - vecino_col['cx']))
    dy = vecino_col['quad'].mean(axis=0)[1] - vecino_fila_cercano['quad'].mean(axis=0)[1]
    signo = 1 if dy > 0 else -1

    # Construccion: tomamos el borde de vecino_col compartido con la fila
    # faltante y extendemos una distancia h_est en direccion vertical.
    if f < fila_op:
        # la celda faltante esta ARRIBA del vecino de columna
        nueva_bl = vecino_col['quad'][0]
        nueva_br = vecino_col['quad'][1]
        direccion = vecino_col['quad'][0] - vecino_col['quad'][3]  # TL-BL (hacia arriba)
        norma = np.linalg.norm(direccion)
        direccion = direccion / norma if norma > 0 else np.array([0, -1])
        nueva_tl = nueva_bl + direccion * h_est
        nueva_tr = nueva_br + direccion * h_est
        quad_nuevo = np.array([nueva_tl, nueva_tr, nueva_br, nueva_bl], dtype=np.float32)
    else:
        # la celda faltante esta ABAJO del vecino de columna
        nueva_tl = vecino_col['quad'][3]
        nueva_tr = vecino_col['quad'][2]
        direccion = vecino_col['quad'][3] - vecino_col['quad'][0]  # BL-TL (hacia abajo)
        norma = np.linalg.norm(direccion)
        direccion = direccion / norma if norma > 0 else np.array([0, 1])
        nueva_bl = nueva_tl + direccion * h_est
        nueva_br = nueva_tr + direccion * h_est
        quad_nuevo = np.array([nueva_tl, nueva_tr, nueva_br, nueva_bl], dtype=np.float32)

    cxcy = quad_nuevo.mean(axis=0)
    grilla[f][c] = {
        'quad': quad_nuevo, 'area': float(w_est * h_est), 'cx': float(cxcy[0]),
        'cy': float(cxcy[1]), 'rectangularidad': 0.8, 'inferida': True,
    }
    aviso = (f"Celda en fila {f + 1} columna {c + 1} (grilla cruda) no se detecto por "
             f"contorno propio; se infirio por geometria de la grilla.")
    return grilla, aviso


def reconstruir_grilla_por_homografia(grilla, n_filas, n_cols):
    """Reconstruye TODAS las celdas de la grilla (detectadas o no) ajustando
    una UNICA homografia que mapea coordenadas normalizadas de grilla
    (columna, fila) en [0,n_cols]x[0,n_filas] hacia la imagen, usando como
    correspondencias las 4 esquinas de cada celda SI fue detectada por
    contorno.

    Es mucho mas robusto que inferir una celda aislada a partir de sus
    vecinas inmediatas (metodo anterior, limitado a exactamente 1 celda
    faltante): al usar TODAS las esquinas de TODAS las celdas detectadas en
    un solo ajuste de minimos cuadrados, funciona igual de bien con 1, 2 o
    mas celdas faltantes (mientras haya al menos 2 celdas detectadas y no
    esten degeneradas en una sola fila/columna), y absorbe la perspectiva
    global de la foto en vez de extrapolar una sola arista.

    Devuelve (grilla_completa, aviso) o (None, None) si no hay evidencia
    suficiente (menos de 2 celdas detectadas) o si la homografia no se pudo
    ajustar.
    """
    src = []
    dst = []
    posiciones_detectadas = []
    for f in range(n_filas):
        for c in range(n_cols):
            celda = grilla[f][c]
            if celda is None:
                continue
            posiciones_detectadas.append((f, c))
            q = order_points(celda['quad'])  # tl, tr, br, bl
            esquinas_norm = ((c, f), (c + 1, f), (c + 1, f + 1), (c, f + 1))
            for (u, v), p in zip(esquinas_norm, q):
                src.append([u, v])
                dst.append([p[0], p[1]])

    n_detectadas = len(posiciones_detectadas)
    if n_detectadas < 2:
        return None, None

    # Con SOLO 2 celdas detectadas, la homografia queda mal condicionada si
    # esas 2 celdas no comparten fila ni columna (por ejemplo, 2 esquinas
    # opuestas en diagonal de la grilla): matematicamente hay suficientes
    # puntos para resolverla, pero la forma resultante puede quedar muy
    # distorsionada (mucho shear) sin que ningun chequeo de angulo/area por
    # celda individual lo detecte. Se exige que compartan fila o columna
    # (un borde real en comun) para confiar en el ajuste con tan poca
    # evidencia; con 3 o mas celdas detectadas ya no hace falta este chequeo.
    if n_detectadas == 2:
        (f0, c0), (f1, c1) = posiciones_detectadas
        if f0 != f1 and c0 != c1:
            return None, None

    src = np.array(src, dtype=np.float32)
    dst = np.array(dst, dtype=np.float32)
    try:
        H, _ = cv2.findHomography(src, dst, method=0)
    except cv2.error:
        H = None
    if H is None:
        return None, None

    areas_detectadas = [grilla[f][c]['area'] for f in range(n_filas) for c in range(n_cols)
                         if grilla[f][c] is not None]
    mediana_area = float(np.median(areas_detectadas)) if areas_detectadas else 0.0

    nueva_grilla = [[None] * n_cols for _ in range(n_filas)]
    n_reconstruidas = 0
    for f in range(n_filas):
        for c in range(n_cols):
            esquinas_norm = np.array([[c, f], [c + 1, f], [c + 1, f + 1], [c, f + 1]],
                                      dtype=np.float32).reshape(-1, 1, 2)
            quad = cv2.perspectiveTransform(esquinas_norm, H).reshape(4, 2).astype(np.float32)

            # Validacion de sanidad de la celda reconstruida: si la
            # homografia extrapolo mal (poca evidencia, celdas detectadas
            # muy concentradas en una esquina), esto lo detecta y rechaza
            # TODO el intento en vez de entregar una celda deforme.
            if not np.all(np.isfinite(quad)):
                return None, None
            if not cv2.isContourConvex(quad.reshape(-1, 1, 2).astype(np.int32)):
                return None, None
            if not _angulos_cercanos_90(quad, tol=35):
                return None, None
            area_q = float(cv2.contourArea(quad))
            if mediana_area > 0 and not (0.35 * mediana_area <= area_q <= 3.0 * mediana_area):
                return None, None

            cxcy = quad.mean(axis=0)
            era_detectada = grilla[f][c] is not None
            if not era_detectada:
                n_reconstruidas += 1
            nueva_grilla[f][c] = {
                'quad': quad, 'area': area_q, 'cx': float(cxcy[0]), 'cy': float(cxcy[1]),
                'rectangularidad': 0.8, 'inferida': not era_detectada,
            }

    if n_reconstruidas == 0:
        # nada que reconstruir (las 6 ya estaban detectadas): no hace falta aviso
        return nueva_grilla, None

    aviso = (f'{n_reconstruidas} de {n_filas * n_cols} cuadros no se detectaron por '
             'contorno propio; se reconstruyeron ajustando una homografia global de '
             'la grilla a partir de los cuadros si detectados (deteccion por lineas '
             'de la grilla).')
    return nueva_grilla, aviso


def detectar_seis_celdas(gray_corr):
    """Intenta detectar las 6 celdas de la hoja, probando varias
    combinaciones de parametros de umbral (ver _PARAMS_UMBRAL) porque una
    foto de celular con sombra y un escaneo limpio con reticula impresa muy
    fina requieren sensibilidades distintas. Si con algun intento se
    detectan por contorno propio entre 2 y 5 de las 6 celdas, se reconstruye
    la grilla completa por homografia global (ver
    reconstruir_grilla_por_homografia), lo que permite recuperar hojas donde
    el borde de mas de un cuadro no cerro por contorno. Se queda con el
    primer intento que logre las 6 celdas (detectadas y/o reconstruidas); si
    ninguno lo logra, se queda con el intento que mas celdas coherentes haya
    entregado (para que el llamador pueda decidir si cae a un metodo de
    respaldo).

    Devuelve (celdas, avisos, ok, params_usados) donde celdas es una lista de
    6 dicts (orden fila/columna en el sistema de EJES de la imagen, sin
    corregir aun la rotacion de la lamina) o None si no se logro nada usable.
    """
    mejor_celdas = None
    mejor_avisos = []
    mejor_n_ok = -1
    mejor_params = _PARAMS_UMBRAL[0]

    for params in _PARAMS_UMBRAL:
        candidatos = detectar_celdas_candidatas(gray_corr, params)
        if len(candidatos) < 2:
            continue
        grilla, n_filas, n_cols = _asignar_grilla(candidatos)

        # Chequeo de consistencia de tamano: las 6 celdas de la lamina deben
        # ser todas de un tamano muy similar. Si algun candidato asignado
        # queda con un area muy distinta a la mediana, probablemente no es
        # el borde real de una celda (por ejemplo, una cara de un solido
        # isometrico que paso los demas filtros por casualidad): se descarta
        # y su casilla se trata como "faltante" para intentar inferirla.
        areas = [grilla[f][c]['area'] for f in range(n_filas) for c in range(n_cols)
                 if grilla[f][c] is not None]
        if areas:
            mediana = float(np.median(areas))
            for f in range(n_filas):
                for c in range(n_cols):
                    celda = grilla[f][c]
                    if celda is not None and mediana > 0 and \
                            not (0.55 * mediana <= celda['area'] <= 1.8 * mediana):
                        grilla[f][c] = None

        n_ok = sum(1 for f in range(n_filas) for c in range(n_cols) if grilla[f][c] is not None)
        avisos = []
        if 2 <= n_ok <= 5:
            # Faltan 1 a 4 celdas: se intenta reconstruir la grilla completa
            # ajustando una homografia global con las celdas si detectadas
            # (mucho mas robusto que inferir por vecino inmediato, y permite
            # recuperar hojas donde el borde de mas de un cuadro no cerro
            # bien por contorno aunque la foto sea nitida).
            grilla_reconstruida, aviso = reconstruir_grilla_por_homografia(grilla, n_filas, n_cols)
            if grilla_reconstruida is not None:
                grilla = grilla_reconstruida
                if aviso:
                    avisos.append(aviso)
            elif n_ok == 5:
                # respaldo: metodo simple de inferencia por vecino inmediato
                grilla, aviso = _inferir_celda_faltante(grilla, n_filas, n_cols)
                if aviso:
                    avisos.append(aviso)
            n_ok = sum(1 for f in range(n_filas) for c in range(n_cols) if grilla[f][c] is not None)

        if n_ok > mejor_n_ok:
            mejor_n_ok = n_ok
            mejor_avisos = avisos
            mejor_params = params
            if n_ok == 6:
                mejor_celdas = []
                for f in range(n_filas):
                    for c in range(n_cols):
                        mejor_celdas.append(grilla[f][c])

        if n_ok == 6:
            return mejor_celdas, avisos, True, params

    return None, mejor_avisos, False, mejor_params


# ---------------------------------------------------------------------------
# Deteccion de rotacion de la hoja (voto por posicion del recuadro del numero)
# ---------------------------------------------------------------------------

def _densidad_esquina(th, quad, esquina_idx, frac=0.16, minimo=10):
    """Mide la densidad de tinta (fraccion de pixeles activos en `th`) en un
    parche cuadrado ubicado hacia el interior de la celda desde la esquina
    `esquina_idx` (0=TL,1=TR,2=BR,3=BL segun order_points). Este parche es
    donde deberia estar el recuadrito con el numero impreso de la celda.
    """
    q = quad
    centro = q.mean(axis=0)
    esquina = q[esquina_idx]
    lado1 = q[(esquina_idx + 1) % 4]
    lado2 = q[(esquina_idx - 1) % 4]
    tam = frac
    # punto de muestreo: un poco adentro de la esquina, hacia el centro y
    # hacia ambos lados adyacentes (para cubrir el recuadrito del numero)
    p = esquina + (lado1 - esquina) * tam + (lado2 - esquina) * tam
    diag = np.linalg.norm(centro - esquina)
    r = max(minimo, int(diag * tam * 0.9))
    x0, y0 = int(p[0] - r), int(p[1] - r)
    x1, y1 = int(p[0] + r), int(p[1] + r)
    h, w = th.shape[:2]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    parche = th[y0:y1, x0:x1]
    return float(np.mean(parche > 0))


def _forma_par_base(n_filas, n_cols):
    """Dado el par (n_filas, n_cols) de la grilla cruda detectada (ver
    _forma_grilla), determina el "k base" (0 o 1) que hace que, al
    aplicarlo, la hoja quede con la forma final correcta (2 filas x 3
    columnas). El OTRO candidato posible es siempre k_base + 2 (180 grados
    adicionales): esa es la UNICA ambiguedad real que puede quedar, porque
    los otros 2 valores de k cambiarian la forma de la grilla (2x3 <-> 3x2)
    y por lo tanto son geometricamente incompatibles con lo ya detectado.

    Esta es la correccion central del bug de rotacion de las pautas: antes
    se dejaba competir a las 4 rotaciones posibles en el voto, aunque 2 de
    ellas ya eran imposibles segun la forma de la grilla detectada (por
    ejemplo, para un escaneo vertical con la lamina rotada -donde la grilla
    cruda sale 3 filas x 2 columnas-, solo +90 o -90 son fisicamente
    plausibles; 0 y 180 no lo son, porque no cambian filas/columnas). Dejar
    competir tambien esas 2 opciones imposibles solo agregaba ruido y hacia
    que el voto real (+90 vs -90, la ambiguedad genuina) se resolviera casi
    al azar.
    """
    return 0 if (n_filas, n_cols) == (2, 3) else 1


# Esquina (segun EJES de la imagen, indices de order_points 0=TL,1=TR,2=BR,
# 3=BL) que se convierte en la esquina superior-izquierda REAL tras aplicar
# k pasos de rotacion horaria. Es el mapa inverso de _CORNER_TO_K.
_K_A_ESQUINA_TL = {0: 'TL', 1: 'BL', 2: 'BR', 3: 'TR'}

# Esquina que se convierte en la esquina inferior-izquierda REAL tras k pasos
# de rotacion horaria (usado para la señal de la letra "A", que va abajo a
# la izquierda de cada vista).
_K_A_ESQUINA_BL = {0: 'BL', 1: 'BR', 2: 'TR', 3: 'TL'}

# Borde del sistema de EJES de la imagen (antes de rotar) que termina siendo
# el borde INFERIOR de la hoja una vez aplicados k pasos de rotacion
# horaria. Se obtiene rastreando, para cada k, de que borde de la imagen de
# origen proviene la ultima fila de la imagen ya rotada (ver _rotar_punto /
# rotar_imagen): con k=0 el pie queda abajo tal cual: con k=1 (90 horario)
# el borde derecho de la imagen original pasa a ser el pie; con k=2 (180) el
# borde superior pasa a ser el pie; con k=3 (90 antihorario) el borde
# izquierdo pasa a ser el pie.
_K_A_BORDE_INFERIOR = {0: 'bottom', 1: 'right', 2: 'top', 3: 'left'}

_ETIQUETA_A_IDX = {'TL': 0, 'TR': 1, 'BR': 2, 'BL': 3}


def _suma_densidad_esquina_todas(th, celdas, etiqueta, frac=0.16):
    """Suma (no solo cuenta "ganadores" por celda) la densidad de tinta en
    la esquina `etiqueta` (TL/TR/BR/BL segun EJES de la imagen) de TODAS las
    celdas dadas. Sumar toda la evidencia en vez de quedarse con el
    "ganador" de cada celda por separado es mucho mas robusto cuando la
    señal es debil o pareja en celdas individuales (como pasa en escaneos
    limpios, donde el recuadrito del numero es una linea fina y su densidad
    de tinta por celda es baja y ruidosa frente a las otras 3 esquinas: ese
    ruido por-celda fue justamente lo que hizo fallar el voto anterior).
    """
    idx = _ETIQUETA_A_IDX[etiqueta]
    total = 0.0
    for celda in celdas:
        quad = order_points(celda['quad'])
        total += _densidad_esquina(th, quad, idx, frac=frac)
    return total


def _senal_recuadro_numero(th, celdas, k_a, k_b):
    """Señal 1 (no ambigua): el recuadrito del numero va en la esquina
    superior-izquierda de cada cuadro. Se suma, sobre las 6 celdas, la
    densidad de tinta en la esquina que seria la superior-izquierda real
    bajo cada uno de los 2 candidatos posibles (k_a, k_b) y se elige el que
    acumula mas tinta. Devuelve (k_elegido, detalle) o (None, detalle) si el
    resultado es practicamente un empate (poca diferencia relativa: no hay
    evidencia clara para preferir uno sobre otro).
    """
    etq_a = _K_A_ESQUINA_TL[k_a % 4]
    etq_b = _K_A_ESQUINA_TL[k_b % 4]
    dens_a = _suma_densidad_esquina_todas(th, celdas, etq_a)
    dens_b = _suma_densidad_esquina_todas(th, celdas, etq_b)
    detalle = f'recuadro_numero(k{k_a}={dens_a:.3f} vs k{k_b}={dens_b:.3f})'
    total = dens_a + dens_b
    if total <= 0 or abs(dens_a - dens_b) < 0.08 * total:
        return None, detalle
    return (k_a if dens_a > dens_b else k_b), detalle


def _franja_margen_densidad(th, bbox, lado):
    """Densidad de tinta (fraccion de pixeles activos) en la franja de
    margen de la hoja entre el borde de la imagen y el borde `lado`
    (top/bottom/left/right) de `bbox` (envolvente de los 6 cuadros
    detectados). Ahi es justamente donde va la banda "Nombre/Rut/Fecha" con
    su linea larga (al pie) o, del lado opuesto, donde no deberia haber
    practicamente nada impreso (encima de los cuadros la lamina esta en
    blanco).
    """
    h, w = th.shape[:2]
    x0, y0, x1, y1 = bbox
    x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(w, x1)), int(min(h, y1))
    if lado == 'top':
        franja = th[0:y0, :]
    elif lado == 'bottom':
        franja = th[y1:h, :]
    elif lado == 'left':
        franja = th[:, 0:x0]
    else:
        franja = th[:, x1:w]
    if franja.size == 0:
        return 0.0
    return float(np.mean(franja > 0))


def _senal_banda_pie(th, celdas, k_a, k_b):
    """Señal 2 (no ambigua): la banda "Nombre/Rut/Fecha" y su linea
    horizontal larga van SIEMPRE al pie de la hoja (fuera del marco de los 6
    cuadros), nunca arriba. Se mide la densidad de tinta en la franja
    externa a cada lado de la grilla de cuadros detectada y se elige el
    candidato cuyo "lado inferior" (ver _K_A_BORDE_INFERIOR) cae del lado
    con mas tinta. Devuelve (k_elegido, detalle) o (None, detalle) si las 2
    franjas relevantes salen con densidad parecida (poca evidencia; por
    ejemplo, una foto muy recortada que casi no deja margen fuera de los
    cuadros).
    """
    xs = np.concatenate([c['quad'][:, 0] for c in celdas])
    ys = np.concatenate([c['quad'][:, 1] for c in celdas])
    bbox = (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))
    lado_a = _K_A_BORDE_INFERIOR[k_a % 4]
    lado_b = _K_A_BORDE_INFERIOR[k_b % 4]
    dens_a = _franja_margen_densidad(th, bbox, lado_a)
    dens_b = _franja_margen_densidad(th, bbox, lado_b)
    detalle = f'banda_pie(k{k_a}={dens_a:.4f} vs k{k_b}={dens_b:.4f})'
    total = dens_a + dens_b
    if total <= 0 or abs(dens_a - dens_b) < 0.15 * total:
        return None, detalle
    return (k_a if dens_a > dens_b else k_b), detalle


def _senal_letra_a(th, celdas, k_a, k_b):
    """Señal 3 (no ambigua, solo hojas tipo "vistas"): cada vista dibujada
    lleva una letra "A" chica abajo a la izquierda. En la esquina que seria
    la inferior-izquierda real de cada cuadro bajo cada candidato, se buscan
    componentes conexas chicas y compactas (se descartan lineas largas del
    marco/reticula por area y por relacion de aspecto de su caja envolvente,
    que serian mucho mas alargadas o mucho mas grandes que una letra suelta)
    compatibles con ser una letra suelta. Se cuentan sobre las 6 celdas y se
    elige el candidato con mas hallazgos. Devuelve (k_elegido, detalle) o
    (None, detalle) si no hay diferencia clara.
    """
    def _contar(etiqueta):
        idx = _ETIQUETA_A_IDX[etiqueta]
        n = 0
        h, w = th.shape[:2]
        for celda in celdas:
            quad = order_points(celda['quad'])
            centro = quad.mean(axis=0)
            esquina = quad[idx]
            lado1 = quad[(idx + 1) % 4]
            lado2 = quad[(idx - 1) % 4]
            frac = 0.30
            p = esquina + (lado1 - esquina) * frac + (lado2 - esquina) * frac
            diag = np.linalg.norm(centro - esquina)
            r = max(12, int(diag * frac * 0.9))
            x0, y0 = max(0, int(p[0] - r)), max(0, int(p[1] - r))
            x1, y1 = min(w, int(p[0] + r)), min(h, int(p[1] + r))
            if x1 <= x0 or y1 <= y0:
                continue
            parche = th[y0:y1, x0:x1]
            area_parche = parche.shape[0] * parche.shape[1]
            num, _labels, stats, _cent = cv2.connectedComponentsWithStats(parche, connectivity=8)
            for i in range(1, num):
                area = stats[i, cv2.CC_STAT_AREA]
                bw, bh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
                if area < 6 or area > 0.35 * area_parche or bw == 0 or bh == 0:
                    continue
                aspecto = bw / float(bh)
                # una letra suelta es compacta: ni una linea larga y fina
                # (marco/reticula), ni algo que ocupe casi todo el parche.
                if 0.35 <= aspecto <= 2.8 and bw < 0.7 * parche.shape[1] and bh < 0.7 * parche.shape[0]:
                    n += 1
        return n

    etq_a = _K_A_ESQUINA_BL[k_a % 4]
    etq_b = _K_A_ESQUINA_BL[k_b % 4]
    n_a = _contar(etq_a)
    n_b = _contar(etq_b)
    detalle = f'letra_A(k{k_a}={n_a} vs k{k_b}={n_b})'
    if n_a == n_b:
        return None, detalle
    return (k_a if n_a > n_b else k_b), detalle


def determinar_rotacion_hoja(th, celdas, n_filas, n_cols, tipo=None):
    """Determina la rotacion (k = pasos de 90 grados horario) que hay que
    aplicar a la hoja para dejarla en orientacion de lectura normal,
    votando entre señales geometricas NO ambiguas:
      1. Esquina donde esta el recuadrito del numero de cada cuadro (debe
         terminar arriba a la izquierda).
      2. Franja de la banda "Nombre/Rut/Fecha" con su linea larga (debe
         terminar al pie de la hoja, nunca arriba).
      3. Letra "A" de cada vista dibujada (debe terminar abajo a la
         izquierda de cada cuadro); solo se evalua en hojas tipo 'vistas'.

    La forma de la grilla cruda detectada (n_filas, n_cols) ya deja SOLO 2
    candidatos posibles para k, separados por 180 grados entre si (ver
    _forma_par_base): cada señal solo tiene que decidir entre esos 2, no
    entre las 4 rotaciones posibles. Justamente ahi estaba el bug: al dejar
    competir tambien las 2 rotaciones geometricamente imposibles, la señal
    (debil de por si en escaneos limpios) se diluia y el desempate quedaba
    practicamente al azar.

    Devuelve (k, confianza_voto, aviso_o_None, detalle_str). `aviso` no es
    None cuando corresponde dejar constancia explicita en el manifest: ya
    sea porque las señales empataron (no se pudo decidir con evidencia) o
    porque se corrigio una hoja que vino con 180 grados adicionales de
    rotacion (para que quede visible en el reporte de QA que se aplico una
    correccion automatica).
    """
    k_base = _forma_par_base(n_filas, n_cols)
    k_alt = (k_base + 2) % 4

    votos = []
    detalles = []
    k1, d1 = _senal_recuadro_numero(th, celdas, k_base, k_alt)
    votos.append(k1)
    detalles.append(d1)
    k2, d2 = _senal_banda_pie(th, celdas, k_base, k_alt)
    votos.append(k2)
    detalles.append(d2)
    if tipo == 'vistas':
        k3, d3 = _senal_letra_a(th, celdas, k_base, k_alt)
        votos.append(k3)
        detalles.append(d3)

    detalle_str = '; '.join(detalles)
    validos = [v for v in votos if v is not None]
    n_senales = len(votos)

    if not validos:
        aviso = ('La orientacion de la hoja quedo AMBIGUA: ninguna de las '
                  'señales de deteccion (recuadro del numero, banda de pie '
                  f'de pagina{", letra A" if tipo == "vistas" else ""}) dio '
                  f'evidencia clara. Se dejo con la orientacion por defecto '
                  f'(k={k_base}) pero CONVIENE REVISARLA A MANO. '
                  f'Detalle de señales: {detalle_str}')
        return k_base, 0.0, aviso, detalle_str

    conteo_base = validos.count(k_base)
    conteo_alt = validos.count(k_alt)

    if conteo_base == conteo_alt:
        aviso = ('La orientacion de la hoja quedo AMBIGUA: las señales de '
                  'deteccion no lograron mayoria '
                  f'({conteo_base} vs {conteo_alt} de {n_senales} señales '
                  f'evaluadas). Se dejo con la orientacion por defecto '
                  f'(k={k_base}) pero CONVIENE REVISARLA A MANO. '
                  f'Detalle de señales: {detalle_str}')
        return k_base, 0.5, aviso, detalle_str

    k_final = k_base if conteo_base > conteo_alt else k_alt
    confianza = max(conteo_base, conteo_alt) / float(n_senales)
    aviso = None
    if k_final != k_base:
        aviso = ('Se detecto, por mayoria de señales de orientacion '
                  f'({max(conteo_base, conteo_alt)}/{n_senales}: '
                  f'{detalle_str}), que la hoja estaba fotografiada/'
                  'escaneada con 180 grados adicionales de rotacion '
                  'respecto de lo esperado por la forma de la grilla; se '
                  'corrigio automaticamente.')
    return k_final, confianza, aviso, detalle_str


# ---------------------------------------------------------------------------
# Rectificacion de celdas (homografia)
# ---------------------------------------------------------------------------

def rectificar_celda_gris(img_color_original, quad_original, size=1000):
    """Aplica warpPerspective sobre la imagen ORIGINAL (mejor calidad) usando
    las 4 esquinas (ya reindexadas: TL,TR,BR,BL reales) para obtener un
    cuadrado perfecto en escala de grises de `size` x `size` px.
    """
    destino = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]],
                        dtype=np.float32)
    M = cv2.getPerspectiveTransform(quad_original.astype(np.float32), destino)
    color = cv2.warpPerspective(img_color_original, M, (size, size),
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    gris = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    return gris


# ---------------------------------------------------------------------------
# Clasificacion de la reticula (vistas / isometricos)
# ---------------------------------------------------------------------------

def _histograma_angulos(gray, peso_por_longitud=True):
    """Calcula un histograma (bins de 1 grado, 0-179) de orientaciones de
    segmentos de recta detectados con HoughLinesP, ponderado por longitud.
    """
    edges = cv2.Canny(gray, 40, 130)
    lineas = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=35,
                              minLineLength=25, maxLineGap=4)
    hist = np.zeros(180, dtype=np.float64)
    if lineas is None or len(lineas) == 0:
        return hist
    for l in lineas.reshape(-1, 4):
        x1, y1, x2, y2 = l
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
        longitud = math.hypot(x2 - x1, y2 - y1) if peso_por_longitud else 1.0
        b = int(round(ang)) % 180
        hist[b] += longitud
    return hist


def _masa_cercana(hist, angulos_objetivo, tolerancia=7):
    total = hist.sum()
    if total <= 0:
        return 0.0
    masa = 0.0
    for a in angulos_objetivo:
        for d in range(-tolerancia, tolerancia + 1):
            masa += hist[(a + d) % 180]
    return masa / total


def clasificar_reticula(celdas_gray):
    """Clasifica el tipo de hoja ('vistas' / 'isometricos' / 'desconocida')
    analizando la orientacion dominante de las lineas de fondo (reticula)
    agregando el histograma de angulos de varias celdas.
    """
    hist_total = np.zeros(180, dtype=np.float64)
    for g in celdas_gray:
        hist_total += _histograma_angulos(g)

    score_vistas = _masa_cercana(hist_total, [0, 90])
    score_iso = _masa_cercana(hist_total, [30, 90, 150])

    if hist_total.sum() < 1000:
        return 'desconocida', 0.0

    if score_vistas < 0.30 and score_iso < 0.30:
        return 'desconocida', max(score_vistas, score_iso)

    if score_vistas >= score_iso * 1.15 and score_vistas >= 0.30:
        return 'vistas', float(score_vistas)
    if score_iso >= score_vistas * 1.15 and score_iso >= 0.30:
        return 'isometricos', float(score_iso)
    return 'desconocida', float(max(score_vistas, score_iso))


# ---------------------------------------------------------------------------
# Separacion de la capa de trazo (lapiz del alumno) vs reticula impresa
# ---------------------------------------------------------------------------

def separar_trazo(gray_cell, tipo_hoja='desconocida'):
    """Separa el trazo a lapiz del alumno de la reticula impresa de fondo.

    La reticula impresa es MUCHO mas clara (gris tenue) que el trazo a lapiz
    o tinta (bien oscuro), incluso si ambas son finas: al umbralizar una
    celda ya con la iluminacion pareja, el histograma de grises muestra un
    pico angosto y oscuro (el trazo) claramente separado de un "hombro" mas
    claro (la reticula) antes de llegar al blanco del papel. Por eso el
    criterio principal de separacion es de INTENSIDAD (un umbral tipo Otsu
    calculado sobre la propia celda, acotado a un rango razonable para no
    irse a un extremo en celdas casi vacias), reforzado con una limpieza de
    componentes conexas chicas para el ruido residual (motas de la reticula
    que igual queden bajo el umbral) y, opcionalmente, una resta adicional
    de "rectas largas" en los angulos propios de la reticula (0/90 para
    vistas, 30/90/150 para isometricos) para lo que sobreviva alineado
    exactamente con la grilla impresa.

    Pasos:
      1. Corregir iluminacion LOCAL de la celda (por si queda gradiente
         residual de sombra de foto, ya que la celda se recorta de la
         imagen ORIGINAL para maxima nitidez, sin la correccion global).
      2. Umbral tipo Otsu sobre la celda corregida, acotado a [95,200] para
         evitar extremos degenerados en celdas casi en blanco.
      3. Apertura chica (2x2) + cierre chico (3x3) para homogeneizar trazo
         sin destruir lineas finas reales.
      4. Resta de rectas largas en los angulos de reticula esperados (limpia
         motas de reticula que hayan quedado justo bajo el umbral).
      5. Se eliminan componentes conexas chicas (ruido residual).
      6. El canal alfa se hace proporcional a que tan oscuro es cada pixel de
         tinta respecto del fondo local (mas oscuro = mas opaco).

    Devuelve (rgba, mascara_binaria_final, n_componentes) donde rgba es una
    imagen 1000x1000 RGBA (fondo transparente, tinta en negro con alfa
    proporcional a la intensidad).
    """
    size = gray_cell.shape[0]
    corr = corregir_iluminacion(gray_cell)

    # 2) umbral tipo Otsu acotado, sobre la celda ya con iluminacion pareja
    t_otsu, _ = cv2.threshold(corr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    t_otsu = float(np.clip(t_otsu, 95, 200))
    bin_todo = (corr < t_otsu).astype(np.uint8) * 255

    # 3) homogeneizar sin destruir trazo fino (no se usa apertura orientada
    #    por angulo de reticula aqui: en hojas "vistas" el propio trazo del
    #    alumno suele ser recto a 0/90 grados, igual que la reticula, y
    #    restar rectas largas en esos angulos borraria trazo real).
    bin_todo = cv2.morphologyEx(bin_todo, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ink_mask = cv2.morphologyEx(bin_todo, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    # 5) limpiar componentes conexas chicas (ruido residual)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(ink_mask, connectivity=8)
    area_min = max(15, size * size // 50000)
    limpio = np.zeros_like(ink_mask)
    n_componentes = 0
    for i in range(1, num):
        if stats[i, cv2.CC_STAT_AREA] >= area_min:
            limpio[labels == i] = 255
            n_componentes += 1

    # 5) alfa proporcional a la oscuridad del pixel dentro de la mascara
    fondo_local = cv2.GaussianBlur(gray_cell, (0, 0), size / 20.0)
    oscuridad = np.clip(fondo_local.astype(np.float32) - gray_cell.astype(np.float32), 0, 255)
    if np.any(limpio > 0) and oscuridad[limpio > 0].max() > 0:
        ref = np.percentile(oscuridad[limpio > 0], 85) + 1e-3
        alfa = np.clip(oscuridad / ref * 255, 0, 255)
    else:
        alfa = oscuridad
    alfa = alfa.astype(np.uint8)
    alfa = cv2.bitwise_and(alfa, alfa, mask=limpio)
    # asegurar opacidad minima donde hay tinta detectada, para que no quede casi invisible
    alfa = np.where((limpio > 0) & (alfa < 120), 160, alfa).astype(np.uint8)

    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 3] = alfa
    # rgb en negro (0,0,0) donde hay tinta; donde no, no importa (alfa=0)

    return rgba, limpio, n_componentes


def metricas_celda(mascara_ink, n_componentes):
    """Calcula la fraccion de tinta y la bandera de "vacio" para una celda."""
    total = mascara_ink.size
    tinta = float(np.count_nonzero(mascara_ink)) / float(total)
    vacio = tinta < 0.0015 or n_componentes == 0
    return tinta, vacio


# ---------------------------------------------------------------------------
# Deteccion de marco exterior (para el metodo de respaldo) y corte por proporciones
# ---------------------------------------------------------------------------

# Combinaciones (blockSize, C, kernel_de_cierre) para la busqueda del marco
# exterior. Igual que con las celdas, una foto de celular curvada o con
# glare necesita umbrales distintos de los de un escaneo limpio: se prueban
# varias y se usa la mejor que pase los chequeos de forma (rectangularidad,
# aspecto, angulos cercanos a 90).
_PARAMS_MARCO = [
    (41, 10, 15),
    (41, 8, 15),
    (31, 10, 15),
    (41, 6, 15),
    (31, 8, 21),
    (41, 10, 21),
    (21, 4, 9),
    (21, 6, 9),
    (21, 6, 15),
    (21, 8, 15),
    (21, 8, 21),
    (21, 4, 31),
    (21, 6, 31),
    (41, 4, 31),
    (41, 6, 31),
    (51, 4, 31),
    (31, 4, 15),
    (31, 4, 21),
    (31, 4, 31),
]


def detectar_marco_exterior(gray_corr, area_min=0.18, area_max=0.99):
    """Intenta encontrar el cuadrilatero del marco exterior de la hoja
    (usado por el metodo de respaldo). Prueba varias combinaciones de
    umbral porque una foto con papel curvado, sombra o glare puede necesitar
    un umbral muy distinto al de un escaneo limpio; entre todos los
    candidatos que pasan los chequeos de forma (4 vertices convexos,
    angulos cercanos a 90, aspecto y rectangularidad razonables) se elige el
    de mayor area. Devuelve un quad (4x2) en el sistema de la imagen de
    entrada, o None si ninguna combinacion encuentra un marco creible.
    """
    med = cv2.medianBlur(gray_corr, 5)
    h, w = gray_corr.shape[:2]
    area_img = h * w
    mejor = None
    for block, C, close_k in _PARAMS_MARCO:
        th = cv2.adaptiveThreshold(med, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, block, C)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k)))
        cnts, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            a = cv2.contourArea(c)
            if a < area_min * area_img or a > area_max * area_img:
                continue
            peri = cv2.arcLength(c, True)
            quad = None
            for eps_rel in (0.01, 0.02, 0.03, 0.045, 0.06, 0.08):
                approx = cv2.approxPolyDP(c, eps_rel * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    quad = approx.reshape(4, 2).astype(np.float32)
                    break
            if quad is None:
                continue
            if not _angulos_cercanos_90(quad, tol=32):
                continue
            rect = cv2.minAreaRect(c)
            (rw, rh) = rect[1]
            if rw <= 0 or rh <= 0:
                continue
            aspecto = max(rw, rh) / min(rw, rh)
            if aspecto < 0.35 or aspecto > 3.0:
                continue
            rectangularidad = a / (rw * rh)
            if rectangularidad < 0.65:
                continue
            if mejor is None or a > mejor[0]:
                mejor = (a, quad)
    return mejor[1] if mejor else None


# Proporciones calibradas a partir de la pauta del profesor (pauta_p2_vistas,
# ya corregida su rotacion): margenes y tamano relativo de cada celda dentro
# del marco exterior. Se usan como ultimo recurso cuando no se detectan los
# 6 cuadros por contornos.
PROP_MARGEN_X = 0.045
PROP_MARGEN_Y = 0.045
PROP_GAP_X = 0.012
PROP_GAP_Y = 0.012


def celdas_por_proporcion(quad_marco):
    """Genera 6 quads (2x3) por proporciones fijas dentro del marco exterior,
    asumiendo que el marco ya esta en orientacion de lectura normal (esto se
    debe garantizar ANTES de llamar a esta funcion, reindexando el quad del
    marco con el mismo criterio de rotacion que para las celdas).
    """
    tl, tr, br, bl = quad_marco
    def punto(u, v):
        arriba = tl + (tr - tl) * u
        abajo = bl + (br - bl) * u
        return arriba + (abajo - arriba) * v

    ancho_celda = (1 - 2 * PROP_MARGEN_X - 2 * PROP_GAP_X) / 3.0
    alto_celda = (1 - 2 * PROP_MARGEN_Y - PROP_GAP_Y) / 2.0
    celdas = []
    for fila in range(2):
        for col in range(3):
            u0 = PROP_MARGEN_X + col * (ancho_celda + PROP_GAP_X)
            u1 = u0 + ancho_celda
            v0 = PROP_MARGEN_Y + fila * (alto_celda + PROP_GAP_Y)
            v1 = v0 + alto_celda
            quad = np.array([punto(u0, v0), punto(u1, v0), punto(u1, v1), punto(u0, v1)],
                             dtype=np.float32)
            celdas.append({'quad': quad, 'inferida': True})
    return celdas


# ---------------------------------------------------------------------------
# Caso "cuadro suelto": la foto es el recorte de UN solo ejercicio (con su
# propio marco), no de la hoja completa de 6 cuadros.
# ---------------------------------------------------------------------------

_PARAMS_CUADRO_SUELTO = [
    (41, 8, 15), (41, 10, 15), (31, 6, 9), (31, 8, 15),
    (41, 6, 21), (31, 10, 21), (21, 6, 9), (21, 8, 15),
]


def detectar_cuadro_suelto(gray_corr, area_min=0.30, area_max=0.92):
    """Detecta el caso en que la foto no es la hoja completa sino el recorte
    de UN solo ejercicio/cuadro (por ejemplo, el alumno fotografio de cerca
    un unico casillero en vez de la lamina entera): busca un UNICO
    cuadrilatero grande que ocupe gran parte del encuadre y cuyo aspecto sea
    cercano al de un cuadro individual de la lamina (mas bien cuadrado, NO
    tan alargado como el marco de la hoja completa apaisada).

    Devuelve el quad (4x2, sistema de gray_corr) o None si no aplica.
    """
    med = cv2.medianBlur(gray_corr, 5)
    h, w = gray_corr.shape[:2]
    area_img = h * w
    mejor = None
    for block, C, close_k in _PARAMS_CUADRO_SUELTO:
        th = cv2.adaptiveThreshold(med, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, block, C)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k)))
        cnts, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            a = cv2.contourArea(c)
            if a < area_min * area_img or a > area_max * area_img:
                continue
            peri = cv2.arcLength(c, True)
            quad = None
            for eps_rel in (0.02, 0.03, 0.045, 0.06):
                approx = cv2.approxPolyDP(c, eps_rel * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    quad = approx.reshape(4, 2).astype(np.float32)
                    break
            if quad is None:
                continue
            if not _angulos_cercanos_90(quad, tol=30):
                continue
            rect = cv2.minAreaRect(c)
            (rw, rh) = rect[1]
            if rw <= 0 or rh <= 0:
                continue
            aspecto = max(rw, rh) / min(rw, rh)
            # un cuadro individual es razonablemente cuadrado; si es muy
            # alargado, es mas probable que sea el marco de la hoja completa
            if aspecto > 1.6:
                continue
            rectangularidad = a / (rw * rh)
            if rectangularidad < 0.65:
                continue
            if mejor is None or a > mejor[0]:
                mejor = (a, quad)
    return mejor[1] if mejor else None


# ---------------------------------------------------------------------------
# Caso "varias hojas en la misma foto": se detectan 2 (o mas) marcos de hoja
# completa bien separados entre si y se separan para procesarlos como hojas
# independientes.
# ---------------------------------------------------------------------------

def detectar_marcos_grandes(gray_corr, area_min=0.06, area_max=0.60):
    """Busca TODOS los cuadrilateros grandes (candidatos a "marco de una
    hoja completa") de la imagen, sin quedarse solo con el mejor. Se usa
    para detectar el caso de varias hojas fotografiadas juntas: si aparecen
    2 o mas marcos bien separados entre si, cada uno se procesa como una
    hoja independiente (ver dividir_multiples_hojas).

    Devuelve una lista de dicts {quad, area} ya deduplicada (sin contornos
    anidados/duplicados del mismo marco), ordenada de mayor a menor area.
    """
    med = cv2.medianBlur(gray_corr, 5)
    h, w = gray_corr.shape[:2]
    area_img = h * w
    brutos = []
    for block, C, close_k in _PARAMS_MARCO:
        th = cv2.adaptiveThreshold(med, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, block, C)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k)))
        cnts, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            a = cv2.contourArea(c)
            if a < area_min * area_img or a > area_max * area_img:
                continue
            peri = cv2.arcLength(c, True)
            quad = None
            for eps_rel in (0.01, 0.02, 0.03, 0.045, 0.06, 0.08):
                approx = cv2.approxPolyDP(c, eps_rel * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    quad = approx.reshape(4, 2).astype(np.float32)
                    break
            if quad is None:
                continue
            if not _angulos_cercanos_90(quad, tol=30):
                continue
            rect = cv2.minAreaRect(c)
            (rw, rh) = rect[1]
            if rw <= 0 or rh <= 0:
                continue
            aspecto = max(rw, rh) / min(rw, rh)
            if aspecto < 0.35 or aspecto > 3.0:
                continue
            rectangularidad = a / (rw * rh)
            if rectangularidad < 0.65:
                continue
            brutos.append({'quad': quad, 'area': float(a)})

    # deduplicar por superposicion de cajas envolventes (mismo marco fisico
    # detectado con distintos parametros de umbral)
    brutos.sort(key=lambda d: -d['area'])
    finales = []
    for b in brutos:
        bx0, by0 = b['quad'].min(axis=0)
        bx1, by1 = b['quad'].max(axis=0)
        es_dup = False
        for f in finales:
            fx0, fy0 = f['quad'].min(axis=0)
            fx1, fy1 = f['quad'].max(axis=0)
            ix0, iy0 = max(bx0, fx0), max(by0, fy0)
            ix1, iy1 = min(bx1, fx1), min(by1, fy1)
            inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
            area_b = (bx1 - bx0) * (by1 - by0)
            area_f = (fx1 - fx0) * (fy1 - fy0)
            union = area_b + area_f - inter
            iou = inter / union if union > 0 else 0.0
            if iou > 0.20:
                es_dup = True
                break
        if not es_dup:
            finales.append(b)
    return finales


def dividir_multiples_hojas(img, max_lado=1600):
    """Si la foto contiene MAS DE UNA hoja completa (por ejemplo, el alumno
    fotografio 2 entregas juntas, una al lado de la otra o una arriba de la
    otra), detecta los marcos grandes y, si encuentra 2 o mas bien
    separados entre si (sin superposicion significativa de sus cajas
    envolventes), devuelve una sub-imagen BGR recortada y enderezada
    (homografia sobre el marco detectado) por cada una, en el sistema de la
    imagen ORIGINAL (mejor calidad).

    Devuelve una lista de (sub_imagen, H_a_original) por cada hoja detectada
    (o [] si no aplica: 0 o 1 sola hoja en la foto), donde H_a_original es
    la homografia 3x3 que transforma coordenadas de la sub-imagen de vuelta
    a coordenadas de la imagen ORIGINAL (para poder reportar "esquinas" en
    el sistema de coordenadas que exige el contrato del manifest, aunque la
    celda se haya recortado de una sub-imagen dividida).
    """
    small, esc = redimensionar_para_deteccion(img, max_lado)
    gray_s = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    corr_s = corregir_iluminacion(gray_s)
    candidatos = detectar_marcos_grandes(corr_s)
    if len(candidatos) < 2:
        return []

    h_s, w_s = corr_s.shape[:2]
    UMBRAL_GAP = 0.03

    def _hay_otro_candidato_en_hueco(qa, qb, eje):
        """True si el centroide de ALGUN OTRO candidato (de la lista
        completa detectada) cae dentro del hueco rectangular entre qa y qb.
        Esto es lo que distingue un hueco de fondo real (nada mas detectado
        ahi) de un "hueco" que en realidad es solo el ancho de otra celda
        de la MISMA hoja que quedo en el medio (por ejemplo, comparar la
        celda de la columna 1 con la de la columna 3 sin considerar que la
        columna 2 esta en el medio).
        """
        ax0, ay0 = qa.min(axis=0)
        ax1, ay1 = qa.max(axis=0)
        bx0, by0 = qb.min(axis=0)
        bx1, by1 = qb.max(axis=0)
        if eje == 'x':
            hx0, hx1 = min(ax1, bx1), max(ax0, bx0)
            hy0, hy1 = max(ay0, by0), min(ay1, by1)
        else:
            hy0, hy1 = min(ay1, by1), max(ay0, by0)
            hx0, hx1 = max(ax0, bx0), min(ax1, bx1)
        for otro in candidatos:
            cx, cy = otro['quad'].mean(axis=0)
            if hx0 <= cx <= hx1 and hy0 <= cy <= hy1:
                return True
        return False

    def _separadas_de_verdad(qa, qb):
        """True solo si las cajas envolventes de 2 quads corresponden a 2
        hojas fisicas distintas: deben estar dispuestas una al lado de la
        otra (alineadas en Y, separadas en X) o una arriba de la otra
        (alineadas en X, separadas en Y), con un espacio de fondo real
        entre ellas (sin ningun otro candidato detectado en ese espacio).
        Esto descarta candidatos que se superponen, candidatos que son en
        realidad 2 regiones vecinas de la MISMA hoja (por ejemplo 2 celdas
        opuestas en diagonal), y candidatos separados por OTRA celda de la
        misma hoja que quedo en el medio (por ejemplo columna 1 vs columna 3
        de la misma fila, saltandose la columna 2).
        """
        ax0, ay0 = qa.min(axis=0)
        ax1, ay1 = qa.max(axis=0)
        bx0, by0 = qb.min(axis=0)
        bx1, by1 = qb.max(axis=0)
        overlap_x = max(0.0, min(ax1, bx1) - max(ax0, bx0))
        overlap_y = max(0.0, min(ay1, by1) - max(ay0, by0))
        if overlap_x > 0 and overlap_y > 0:
            return False  # las cajas se intersectan: no son 2 hojas separadas
        gap_x = max(0.0, max(ax0, bx0) - min(ax1, bx1))
        gap_y = max(0.0, max(ay0, by0) - min(ay1, by1))
        ancho_min = min(ax1 - ax0, bx1 - bx0)
        alto_min = min(ay1 - ay0, by1 - by0)
        lado_a_lado = (overlap_y > 0.35 * alto_min and gap_x / w_s >= UMBRAL_GAP
                       and not _hay_otro_candidato_en_hueco(qa, qb, 'x'))
        apiladas = (overlap_x > 0.35 * ancho_min and gap_y / h_s >= UMBRAL_GAP
                    and not _hay_otro_candidato_en_hueco(qa, qb, 'y'))
        return lado_a_lado or apiladas

    # Ademas de la separacion geometrica, 2 hojas fisicas reales
    # fotografiadas juntas son de tamano comparable entre si (no una hoja
    # completa y, por ejemplo, una sola celda).
    candidatos_ordenados = sorted(candidatos, key=lambda d: -d['area'])
    seleccion = []
    for cand in candidatos_ordenados:
        ok = True
        for s in seleccion:
            razon_area = cand['area'] / s['area'] if s['area'] > 0 else 1e9
            razon_area = max(razon_area, 1.0 / razon_area)
            if not _separadas_de_verdad(cand['quad'], s['quad']) or razon_area > 2.2:
                ok = False
                break
        if ok:
            seleccion.append(cand)
        if len(seleccion) >= 4:  # limite razonable de hojas por foto
            break

    if len(seleccion) < 2:
        return []

    sub_imagenes = []
    for cand in seleccion:
        quad_orig = cand['quad'] / esc
        qo = order_points(quad_orig)
        w_m = float(np.linalg.norm(qo[1] - qo[0]))
        h_m = float(np.linalg.norm(qo[3] - qo[0]))
        w_out = int(np.clip(w_m, 400, 2200))
        h_out = int(np.clip(h_m, 400, 2200))
        destino = np.array([[0, 0], [w_out - 1, 0], [w_out - 1, h_out - 1], [0, h_out - 1]],
                            dtype=np.float32)
        M = cv2.getPerspectiveTransform(qo.astype(np.float32), destino)
        sub = cv2.warpPerspective(img, M, (w_out, h_out), flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_REPLICATE)
        # homografia inversa: de coordenadas de la sub-imagen a coordenadas
        # de la imagen ORIGINAL (destino -> qo, en vez de qo -> destino)
        H_a_original = cv2.getPerspectiveTransform(destino, qo.astype(np.float32))
        sub_imagenes.append((sub, H_a_original))
    return sub_imagenes


# ---------------------------------------------------------------------------
# Orquestacion: procesar una hoja completa de principio a fin
# ---------------------------------------------------------------------------

def _ordenar_celdas_final(celdas_info):
    """Ordena una lista de 6 dicts con 'cx','cy' (ya en el sistema de lectura
    canonico) en 2 filas x 3 columnas, devolviendo los INDICES en orden
    1..6 (fila superior izquierda->derecha, luego fila inferior).
    """
    cys = [c['cy'] for c in celdas_info]
    grupo, centros = _kmeans_1d_ngrupos(cys, 2)
    orden_grp = np.argsort(centros)
    mapa = {viejo: nuevo for nuevo, viejo in enumerate(orden_grp)}
    grupo = [mapa[g] for g in grupo]
    idx_fila0 = sorted([i for i, g in enumerate(grupo) if g == 0],
                        key=lambda i: celdas_info[i]['cx'])
    idx_fila1 = sorted([i for i, g in enumerate(grupo) if g == 1],
                        key=lambda i: celdas_info[i]['cx'])
    return idx_fila0 + idx_fila1


def _procesar_una_hoja(img, max_lado=1600, size_celda=1000):
    """Logica de proceso de UNA hoja ya cargada en memoria (BGR), asumiendo
    que la imagen contiene a lo sumo una hoja completa (o el recorte de un
    solo cuadro suelto). NUNCA lanza una excepcion: cualquier problema se
    refleja en el resultado como metodo='fallido'.

    Ver procesar_hoja para el contrato completo del dict resultado (mismas
    claves) y el manejo de fotos con VARIAS hojas juntas, que se resuelve
    un nivel mas arriba.
    """
    try:
        avisos = []
        small, esc = redimensionar_para_deteccion(img, max_lado)
        gray_s = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        corr_s = corregir_iluminacion(gray_s)
        celdas_raw, avisos_det, ok_det, params = detectar_seis_celdas(corr_s)

        if ok_det:
            avisos.extend(avisos_det)
            th_s, _ = _mascara_lineas(corr_s, params)

            # Se clasifica el tipo de hoja (vistas/isometricos) ANTES de
            # decidir la rotacion final, usando una rectificacion provisoria
            # chica (solo para clasificar, no para el resultado final) con
            # la orientacion "base" que ya deja la grilla con la forma
            # correcta (2 filas x 3 columnas). Esto es valido porque el tipo
            # de reticula (angulos 0/90 vs 30/90/150) es invariante a los
            # 180 grados adicionales que todavia estan en duda: una rotacion
            # de 180 grados no cambia el angulo de ninguna linea modulo 180.
            n_filas_raw, n_cols_raw = _forma_grilla(celdas_raw)
            k_base_tent = _forma_par_base(n_filas_raw, n_cols_raw)
            grises_tent = []
            for c in celdas_raw:
                quad_tent = reindexar_esquinas(order_points(c['quad']), k_base_tent) / esc
                grises_tent.append(rectificar_celda_gris(img, quad_tent, size=240))
            tipo_tent, _score_tent = clasificar_reticula(grises_tent)

            k, conf_voto, aviso_rot, _detalle_rot = determinar_rotacion_hoja(
                th_s, celdas_raw, n_filas_raw, n_cols_raw, tipo=tipo_tent)

            celdas_info = []
            for c in celdas_raw:
                quad_img = order_points(c['quad'])
                quad_canon = reindexar_esquinas(quad_img, k)
                quad_orig = quad_canon / esc
                cx, cy = _rotar_punto((c['cx'], c['cy']), k, small.shape[1], small.shape[0])
                celdas_info.append({'quad_orig': quad_orig, 'cx': cx, 'cy': cy,
                                     'inferida': bool(c.get('inferida', False))})

            orden = _ordenar_celdas_final(celdas_info)
            metodo = 'contornos'
            n_inferidas = sum(1 for c in celdas_info if c['inferida'])
            confianza = 0.95 - 0.15 * n_inferidas
            if aviso_rot:
                avisos.append(aviso_rot)
            if conf_voto <= 0.5:
                confianza -= 0.15
            elif conf_voto < 0.99:
                confianza -= 0.05
            confianza = float(np.clip(confianza, 0.35, 0.98))
        else:
            avisos.extend(avisos_det)
            marco = detectar_marco_exterior(corr_s)
            if marco is None:
                # Ultimo intento antes de declarar la hoja fallida: ¿la foto
                # es en realidad el recorte de UN SOLO cuadro/ejercicio
                # suelto (no la lamina completa de 6 cuadros)? Esto es
                # preferible a "fallido sin nada": al profesor le sirve
                # igual el cuadro rectificado aunque no se identifique su
                # numero automaticamente.
                cuadro = detectar_cuadro_suelto(corr_s)
                if cuadro is not None:
                    try:
                        quad_orig = order_points(cuadro) / esc
                        gris = rectificar_celda_gris(img, quad_orig, size_celda)
                        tipo_c, _score_c = clasificar_reticula([gris])
                        rgba, mask, ncomp = separar_trazo(gris, tipo_c)
                        tinta, vacio = metricas_celda(mask, ncomp)
                        celda_salida = {
                            'n': 0, 'quad_original': quad_orig, 'gris': gris, 'rgba': rgba,
                            'tinta': tinta, 'componentes': ncomp, 'vacio': vacio,
                        }
                        avisos.append(
                            'La foto parece ser el recorte de UN SOLO cuadro/ejercicio '
                            'suelto, no la lamina completa de 6 cuadros; se rectifico ese '
                            'unico cuadro. No fue posible identificar automaticamente su '
                            'numero (se guardo como n=0): conviene revisarlo y renombrarlo '
                            'a mano si corresponde.')
                        return {'ok': True, 'metodo': 'cuadro_suelto', 'confianza': 0.30,
                                'avisos': avisos, 'tipo': tipo_c,
                                'imagen_rectificada': None, 'celdas': [celda_salida]}
                    except Exception as e:
                        avisos.append(f'Se detecto un posible cuadro suelto pero no se pudo '
                                       f'rectificar: {e}')
                return {'ok': False, 'metodo': 'fallido', 'confianza': 0.0,
                        'avisos': avisos + ['No se detectaron los 6 cuadros ni el marco exterior de la hoja.'],
                        'tipo': 'desconocida', 'imagen_rectificada': None, 'celdas': []}
            marco_o = order_points(marco)
            w_m = np.linalg.norm(marco_o[1] - marco_o[0])
            h_m = np.linalg.norm(marco_o[3] - marco_o[0])
            # Aproximacion de forma: si el marco es mas alto que ancho, hace
            # falta un giro de 90 grados para dejarlo apaisado. Igual que en
            # la deteccion por contornos, esto deja SOLO 2 candidatos reales
            # (k_base y k_base+180): se refuerza con las señales del
            # recuadro del numero y de la banda de pie de pagina (aplicadas
            # sobre la grilla proporcional aproximada) y solo se corrige el
            # heuristico de forma cuando AMBAS señales coinciden en pedir el
            # giro adicional de 180 grados; si no hay evidencia clara se
            # conserva el heuristico original (sin riesgo de empeorar casos
            # que ya funcionaban con el metodo de respaldo).
            k_base_fb = 1 if h_m > w_m * 1.15 else 0
            k_alt_fb = (k_base_fb + 2) % 4
            celdas_prop_raw = celdas_por_proporcion(marco_o)  # referencia sin rotar (k=0)
            lineas_fb, _ = _mascara_lineas(corr_s)
            k1_fb, d1_fb = _senal_recuadro_numero(lineas_fb, celdas_prop_raw, k_base_fb, k_alt_fb)
            k2_fb, d2_fb = _senal_banda_pie(lineas_fb, celdas_prop_raw, k_base_fb, k_alt_fb)
            if k1_fb == k_alt_fb and k2_fb == k_alt_fb:
                k = k_alt_fb
                avisos.append('Se detecto, por las señales del recuadro del numero y de la '
                               'banda de pie de pagina, que el marco exterior detectado '
                               'estaba con 180 grados adicionales de rotacion; se corrigio '
                               f'automaticamente ({d1_fb}; {d2_fb}). El metodo de deteccion '
                               'de celdas sigue siendo el de respaldo (proporciones): '
                               'conviene revisar a mano igualmente.')
            else:
                k = k_base_fb
            marco_o = reindexar_esquinas(marco_o, k)
            celdas_prop = celdas_por_proporcion(marco_o)
            celdas_info = []
            for c in celdas_prop:
                quad_orig = c['quad'] / esc
                cxcy = quad_orig.mean(axis=0)
                celdas_info.append({'quad_orig': quad_orig, 'cx': float(cxcy[0]),
                                     'cy': float(cxcy[1]), 'inferida': True})
            orden = list(range(6))  # celdas_por_proporcion ya entrega en orden de grilla
            metodo = 'fallback'
            confianza = 0.35
            avisos.append('No se detectaron los 6 cuadros por contorno; se uso el metodo de '
                           'respaldo (marco exterior + proporciones). La orientacion y el '
                           'recorte de cada celda son aproximados: conviene revisar a mano.')

        celdas_ordenadas = [celdas_info[i] for i in orden]

        grises = [rectificar_celda_gris(img, c['quad_orig'], size_celda) for c in celdas_ordenadas]
        tipo, _score_tipo = clasificar_reticula(grises)
        if tipo == 'desconocida':
            avisos.append('No se pudo determinar con confianza si la hoja es de vistas o de isometricos.')

        celdas_salida = []
        for n, (c, gris) in enumerate(zip(celdas_ordenadas, grises), start=1):
            rgba, mask, ncomp = separar_trazo(gris, tipo)
            tinta, vacio = metricas_celda(mask, ncomp)
            celdas_salida.append({
                'n': n, 'quad_original': c['quad_orig'], 'gris': gris, 'rgba': rgba,
                'tinta': tinta, 'componentes': ncomp, 'vacio': vacio,
                'inferida': bool(c.get('inferida', False)),
            })

        # Hoja completa "enderezada": se rota la imagen ORIGINAL segun la
        # rotacion detectada y se recorta a la envolvente de las 6 celdas
        # (con un margen), para dejar una vista de referencia util al editor
        # manual.
        imagen_rot = rotar_imagen(img, k)
        h0, w0 = img.shape[:2]
        puntos_rot = np.array([
            _rotar_punto(p, k, w0, h0)
            for c in celdas_ordenadas for p in c['quad_orig']
        ])
        x0, y0 = puntos_rot.min(axis=0)
        x1, y1 = puntos_rot.max(axis=0)
        pad_x, pad_y = (x1 - x0) * 0.06, (y1 - y0) * 0.06
        hR, wR = imagen_rot.shape[:2]
        x0i, y0i = int(max(0, x0 - pad_x)), int(max(0, y0 - pad_y))
        x1i, y1i = int(min(wR, x1 + pad_x)), int(min(hR, y1 + pad_y))
        if x1i > x0i and y1i > y0i:
            imagen_rectificada = imagen_rot[y0i:y1i, x0i:x1i]
        else:
            imagen_rectificada = imagen_rot

        return {
            'ok': True, 'metodo': metodo, 'confianza': confianza, 'avisos': avisos,
            'tipo': tipo, 'imagen_rectificada': imagen_rectificada, 'celdas': celdas_salida,
        }
    except Exception as e:
        return {'ok': False, 'metodo': 'fallido', 'confianza': 0.0,
                'avisos': [f'Error inesperado procesando la hoja: {e}'],
                'tipo': 'desconocida', 'imagen_rectificada': None, 'celdas': []}


def procesar_hoja(path_img, max_lado=1600, size_celda=1000):
    """Procesa una imagen (una foto o pagina de PDF rasterizada) de principio
    a fin: normaliza, detecta los 6 cuadros (o cae a un metodo de respaldo,
    o al caso de un cuadro suelto), corrige la rotacion de la hoja,
    rectifica cada celda a 1000x1000, clasifica el tipo de reticula, separa
    el trazo del alumno y calcula sus metricas. NUNCA lanza una excepcion:
    cualquier problema se refleja en el resultado como metodo='fallido' para
    que el llamador pueda seguir con la siguiente hoja.

    Si la foto contiene VARIAS hojas completas fotografiadas juntas (por
    ejemplo, dos entregas una al lado de la otra, o una arriba de la otra),
    se detectan y separan automaticamente (ver dividir_multiples_hojas) y
    cada una se procesa de forma independiente.

    Devuelve una LISTA de dicts (normalmente de largo 1; largo 2 o mas solo
    si se detecto y separo mas de una hoja en la misma foto), cada uno con
    las claves:
      {
        'ok': bool,
        'metodo': 'contornos' | 'fallback' | 'cuadro_suelto' | 'fallido',
        'confianza': float en [0,1],
        'avisos': [str, ...],
        'tipo': 'vistas' | 'isometricos' | 'desconocida',
        'imagen_rectificada': np.ndarray BGR (hoja completa enderezada) o None,
        'celdas': [ {n, quad_original (4x2, TL/TR/BR/BL en la imagen ORIGINAL
                     -o en la sub-imagen de la hoja separada, si aplica-),
                     gris (1000x1000 uint8), rgba (1000x1000x4 uint8),
                     tinta, componentes, vacio}, ... ]  (1..6, [n=0] para
                     cuadro_suelto, o [] si fallido)
      }
    """
    try:
        imgs = cargar_imagenes(path_img)
    except Exception as e:
        return [{'ok': False, 'metodo': 'fallido', 'confianza': 0.0,
                  'avisos': [f'No se pudo leer la imagen o PDF: {e}'],
                  'tipo': 'desconocida', 'imagen_rectificada': None, 'celdas': []}]

    resultados_totales = []
    
    for idx_img, img in enumerate(imgs):
        # Se verifica PRIMERO si la foto contiene VARIAS hojas completas
        # fotografiadas juntas (2 marcos grandes bien separados entre si). Esto
        # se comprueba antes de confiar en el resultado de "una sola hoja",
        # porque si en realidad hay 2 hojas fisicas distintas en el encuadre, un
        # intento de detectar "6 cuadros" sobre la foto completa podria mezclar
        # cuadros de AMBAS hojas (por ejemplo completando por homografia con
        # cuadros de la hoja equivocada) y dar un falso "contornos" con datos
        # incorrectos, que es peor que dividir correctamente.
        try:
            subimgs = dividir_multiples_hojas(img, max_lado)
        except Exception:
            subimgs = []
            
        if len(subimgs) >= 2:
            resultados_split = []
            for i, (sub, H_a_original) in enumerate(subimgs, start=1):
                r = _procesar_una_hoja(sub, max_lado, size_celda)
                # El contrato del manifest exige "esquinas" en coordenadas de la
                # imagen ORIGINAL (el archivo fuente), no de la sub-imagen
                # recortada/enderezada: se remapea cada quad con la homografia
                # inversa calculada al dividir las hojas.
                for c in r['celdas']:
                    pts = c['quad_original'].reshape(-1, 1, 2).astype(np.float32)
                    c['quad_original'] = cv2.perspectiveTransform(pts, H_a_original).reshape(4, 2)
                
                aviso_extra = f'Se detectaron {len(subimgs)} hojas fotografiadas juntas en la imagen.'
                if len(imgs) > 1:
                    aviso_extra = f'Pagina PDF {idx_img+1}: ' + aviso_extra
                
                r['avisos'] = list(r['avisos']) + [
                    aviso_extra + f' Esta es la hoja {i} de {len(subimgs)} (separadas '
                    'automaticamente por sus marcos exteriores). Las "esquinas" reportadas '
                    'estan remapeadas a la imagen original.']
                resultados_split.append(r)
            # se usa la version dividida solo si mejora la situacion (al menos
            # una de las hojas separadas quedo mejor que 'fallido'); si ambas
            # quedaron fallidas, se prefiere reintentar como una sola hoja (por
            # si la deteccion de "2 hojas" fue en realidad un falso positivo).
            if any(r['metodo'] != 'fallido' for r in resultados_split):
                resultados_totales.extend(resultados_split)
                continue

        resultado = _procesar_una_hoja(img, max_lado, size_celda)
        if len(imgs) > 1:
            resultado['avisos'] = [f'Pagina PDF {idx_img+1}: ' + a for a in resultado['avisos']]
        resultados_totales.append(resultado)

    return resultados_totales
