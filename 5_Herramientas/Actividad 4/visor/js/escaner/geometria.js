// geometria.js - matematica pura del escaner manual: homografia (DLT resuelta
// a mano por eliminacion gaussiana), muestreo bilineal, ajuste de rectas por
// minimos cuadrados con descarte de atipicos, e interseccion de rectas.
//
// Todo este modulo es JS puro sin DOM (facil de razonar y de probar aparte).
// Convenciones:
//  - Un "quad" es un arreglo de 4 puntos [x,y] en el orden
//    [superior-izq, superior-der, inferior-der, inferior-izq] (TL,TR,BR,BL).
//  - Una homografia H se representa como arreglo plano de 9 numeros
//    (fila por fila) con H[8] normalmente pero no forzosamente 1.

/** Resuelve un sistema lineal cuadrado A*x = b por eliminacion gaussiana con
 * pivoteo parcial. A es un arreglo de arreglos (n x n), b un arreglo (n).
 * Devuelve el arreglo solucion x, o null si el sistema es (casi) singular.
 */
export function resolverSistemaLineal(A, b) {
  const n = b.length;
  // Copia de trabajo (matriz aumentada) para no mutar los argumentos.
  const M = A.map((fila, i) => [...fila, b[i]]);

  for (let col = 0; col < n; col++) {
    // Pivoteo parcial: busca la fila con mayor valor absoluto en esta columna.
    let filaPivote = col;
    let mejor = Math.abs(M[col][col]);
    for (let f = col + 1; f < n; f++) {
      const v = Math.abs(M[f][col]);
      if (v > mejor) {
        mejor = v;
        filaPivote = f;
      }
    }
    if (mejor < 1e-10) return null; // sistema singular o casi singular
    if (filaPivote !== col) {
      const tmp = M[col];
      M[col] = M[filaPivote];
      M[filaPivote] = tmp;
    }
    const pivote = M[col][col];
    for (let f = 0; f < n; f++) {
      if (f === col) continue;
      const factor = M[f][col] / pivote;
      if (factor === 0) continue;
      for (let c = col; c <= n; c++) {
        M[f][c] -= factor * M[col][c];
      }
    }
  }
  return M.map((fila, i) => fila[n] / fila[i]);
}

/**
 * Resuelve la homografia 2D que lleva los 4 puntos `src` a los 4 puntos
 * `dst` (DLT clasico con h33=1, resuelto como sistema lineal de 8
 * incognitas). Devuelve un arreglo plano de 9 numeros (fila por fila) o
 * null si los puntos son degenerados.
 */
export function resolverHomografia(src, dst) {
  if (src.length !== 4 || dst.length !== 4) {
    throw new Error("resolverHomografia requiere exactamente 4 puntos por lado.");
  }
  const A = [];
  const b = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = src[i];
    const [xp, yp] = dst[i];
    A.push([x, y, 1, 0, 0, 0, -x * xp, -y * xp]);
    b.push(xp);
    A.push([0, 0, 0, x, y, 1, -x * yp, -y * yp]);
    b.push(yp);
  }
  const h = resolverSistemaLineal(A, b);
  if (!h) return null;
  return [h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], 1];
}

/** Aplica una homografia (arreglo plano de 9) a un punto (x,y). */
export function aplicarH(H, x, y) {
  const w = H[6] * x + H[7] * y + H[8];
  if (Math.abs(w) < 1e-12) return [NaN, NaN];
  return [(H[0] * x + H[1] * y + H[2]) / w, (H[3] * x + H[4] * y + H[5]) / w];
}

/** Aplica una homografia a un arreglo de puntos [[x,y], ...]. */
export function aplicarHLista(H, puntos) {
  return puntos.map(([x, y]) => aplicarH(H, x, y));
}

// ---------------------------------------------------------------------------
// Reindexacion de esquinas por rotacion/espejo del RESULTADO (ver LEEME).
// ---------------------------------------------------------------------------

/**
 * Dado un quad [TL,TR,BR,BL] y una orientacion {k, flipH, flipV} (k = pasos
 * de 90 grados horario, 0..3), devuelve el quad reindexado de forma que el
 * indice 0 sea la esquina que queda como superior-izquierda REAL una vez
 * aplicados esos volteos/rotaciones al resultado. Es la base para que
 * "rotar/voltear el resultado" sea, matematicamente, solo una
 * reetiquetacion de las 4 esquinas ya marcadas (no hace falta re-tocar
 * pixeles para saber que corte usar).
 *
 * Espejo horizontal (izquierda-derecha): TL<->TR, BL<->BR.
 * Espejo vertical (arriba-abajo): TL<->BL, TR<->BR.
 * Rotacion 90 horario: la esquina que era inferior-izq pasa a ser la nueva
 * superior-izq (equivalente a np.rot90 clockwise sobre la imagen).
 */
export function permutarEsquinas(quad, orientacion = {}) {
  const { k = 0, flipH = false, flipV = false } = orientacion;
  let q = quad.slice();
  if (flipH) q = [q[1], q[0], q[3], q[2]];
  if (flipV) q = [q[3], q[2], q[1], q[0]];
  const pasos = ((k % 4) + 4) % 4;
  for (let i = 0; i < pasos; i++) {
    q = [q[3], q[0], q[1], q[2]];
  }
  return q;
}

// ---------------------------------------------------------------------------
// Muestreo bilineal y warp por homografia (rasterizado por pixel de destino).
// ---------------------------------------------------------------------------

/** Muestrea un ImageData (RGBA) en (x,y) con interpolacion bilineal,
 * recortando (clamp) en los bordes. Devuelve [r,g,b,a]. */
export function muestrearBilineal(datos, ancho, alto, x, y) {
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x > ancho - 1) x = ancho - 1;
  if (y > alto - 1) y = alto - 1;
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const x1 = Math.min(x0 + 1, ancho - 1);
  const y1 = Math.min(y0 + 1, alto - 1);
  const fx = x - x0;
  const fy = y - y0;
  const i00 = (y0 * ancho + x0) * 4;
  const i10 = (y0 * ancho + x1) * 4;
  const i01 = (y1 * ancho + x0) * 4;
  const i11 = (y1 * ancho + x1) * 4;
  const out = [0, 0, 0, 0];
  for (let c = 0; c < 4; c++) {
    const v00 = datos[i00 + c];
    const v10 = datos[i10 + c];
    const v01 = datos[i01 + c];
    const v11 = datos[i11 + c];
    const top = v00 + (v10 - v00) * fx;
    const bot = v01 + (v11 - v01) * fx;
    out[c] = top + (bot - top) * fy;
  }
  return out;
}

/** Version en escala de grises (promedio ponderado luminancia) del muestreo
 * bilineal, usada por el refinamiento de bordes (mas rapida: 1 solo canal). */
export function muestrearGrisBilineal(gris, ancho, alto, x, y) {
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x > ancho - 1) x = ancho - 1;
  if (y > alto - 1) y = alto - 1;
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const x1 = Math.min(x0 + 1, ancho - 1);
  const y1 = Math.min(y0 + 1, alto - 1);
  const fx = x - x0;
  const fy = y - y0;
  const v00 = gris[y0 * ancho + x0];
  const v10 = gris[y0 * ancho + x1];
  const v01 = gris[y1 * ancho + x0];
  const v11 = gris[y1 * ancho + x1];
  const top = v00 + (v10 - v00) * fx;
  const bot = v01 + (v11 - v01) * fx;
  return top + (bot - top) * fy;
}

/**
 * Rectifica (warp) un cuadrilatero `quad` (4 puntos en la imagen FUENTE) a
 * un rectangulo `anchoDestino` x `altoDestino`, muestreando la imagen
 * fuente con interpolacion bilineal para cada pixel de destino (por eso se
 * calcula la homografia que va de DESTINO a FUENTE: para cada pixel del
 * resultado se necesita saber de donde viene, no al reves).
 *
 * `datosFuente` es un ImageData (o {data,width,height}) de la imagen
 * completa ya cargada. Devuelve un ImageData nuevo de anchoDestino x
 * altoDestino.
 */
export function warpPerspectiva(datosFuente, quad, anchoDestino, altoDestino) {
  const destino = [
    [0, 0],
    [anchoDestino - 1, 0],
    [anchoDestino - 1, altoDestino - 1],
    [0, altoDestino - 1],
  ];
  const H = resolverHomografia(destino, quad); // destino -> fuente
  const out = new ImageData(anchoDestino, altoDestino);
  const { data, width, height } = datosFuente;
  for (let v = 0; v < altoDestino; v++) {
    for (let u = 0; u < anchoDestino; u++) {
      const [x, y] = aplicarH(H, u, v);
      const [r, g, b, a] = muestrearBilineal(data, width, height, x, y);
      const idx = (v * anchoDestino + u) * 4;
      out.data[idx] = r;
      out.data[idx + 1] = g;
      out.data[idx + 2] = b;
      out.data[idx + 3] = a;
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Subdivision de la hoja completa en 6 cuadros (grilla 2x3) via homografia.
// ---------------------------------------------------------------------------

/**
 * A partir del quad FINAL de la hoja (ya reindexado con permutarEsquinas,
 * es decir con el indice 0 correspondiendo a la superior-izq real), calcula
 * los 4 vertices de cada uno de los 6 cuadros en coordenadas de la imagen
 * FUENTE, dados un margen interior y una separacion entre cuadros (ambos
 * como fraccion 0..1 del lado de la hoja).
 *
 * Se usa una homografia "unidad -> hoja" (en vez de una interpolacion
 * bilineal ingenua de las 4 esquinas) para que la division respete la
 * perspectiva real de la foto: un punto al 25% del ancho de la hoja cae
 * exactamente donde cae ese mismo punto físico en el papel, aunque la hoja
 * este fotografiada en angulo.
 */
/**
 * Calcula, en coordenadas NORMALIZADAS (0..1 del ancho/alto de la hoja), el
 * rectangulo de cada uno de los 6 cuadros dados un margen interior y una
 * separacion entre cuadros. Se usa tanto para dibujar la grilla en vivo
 * (sobre la imagen original o sobre el recorte ya rectificado, que en
 * ambos casos son simples fracciones de ancho/alto) como, via
 * `generarCortesGrilla`, para ubicar esos mismos rectangulos en la imagen
 * fuente real a traves de la homografia de la hoja.
 */
export function calcularRectangulosGrilla(margenInterior, separacion) {
  const anchoUtil = 1 - 2 * margenInterior - 2 * separacion;
  const altoUtil = 1 - 2 * margenInterior - 1 * separacion;
  const cw = anchoUtil / 3;
  const rh = altoUtil / 2;
  const celdas = [];
  for (let fila = 0; fila < 2; fila++) {
    for (let col = 0; col < 3; col++) {
      const x0 = margenInterior + col * (cw + separacion);
      const y0 = margenInterior + fila * (rh + separacion);
      const n = fila * 3 + col + 1;
      celdas.push({ n, x0, y0, w: cw, h: rh });
    }
  }
  return celdas;
}

export function generarCortesGrilla(quadFinal, margenInterior, separacion) {
  const unidad = [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
  ];
  const Hhoja = resolverHomografia(unidad, quadFinal); // unidad -> imagen fuente
  const rects = calcularRectangulosGrilla(margenInterior, separacion);
  return rects.map(({ n, x0, y0, w, h }) => {
    const esquinasUnidad = [
      [x0, y0],
      [x0 + w, y0],
      [x0 + w, y0 + h],
      [x0, y0 + h],
    ];
    return { n, quad: aplicarHLista(Hhoja, esquinasUnidad) };
  });
}

// ---------------------------------------------------------------------------
// Ajuste de rectas por minimos cuadrados (regresion ortogonal / total least
// squares) e interseccion de rectas.
// ---------------------------------------------------------------------------

/**
 * Ajusta una recta a un conjunto de puntos [[x,y],...] minimizando la SUMA
 * DE DISTANCIAS PERPENDICULARES (no la regresion vertical clasica, que
 * falla con rectas casi verticales). Se resuelve por autovectores de la
 * matriz de covarianza 2x2 (metodo cerrado, sin dependencias externas).
 * Devuelve {punto:[cx,cy], direccion:[dx,dy]} (direccion normalizada).
 */
export function ajustarRectaMinCuadrados(puntos) {
  const n = puntos.length;
  let cx = 0, cy = 0;
  for (const [x, y] of puntos) { cx += x; cy += y; }
  cx /= n; cy /= n;
  let sxx = 0, sxy = 0, syy = 0;
  for (const [x, y] of puntos) {
    const dx = x - cx, dy = y - cy;
    sxx += dx * dx;
    sxy += dx * dy;
    syy += dy * dy;
  }
  // Autovalor mayor de [[sxx,sxy],[sxy,syy]] y su autovector (direccion de
  // maxima varianza = direccion de la recta).
  const tr = sxx + syy;
  const det = sxx * syy - sxy * sxy;
  const disc = Math.max(0, (tr * tr) / 4 - det);
  const lambda1 = tr / 2 + Math.sqrt(disc);
  let dx, dy;
  if (Math.abs(sxy) > 1e-9) {
    dx = lambda1 - syy;
    dy = sxy;
  } else if (sxx >= syy) {
    dx = 1; dy = 0;
  } else {
    dx = 0; dy = 1;
  }
  const norma = Math.hypot(dx, dy) || 1;
  return { punto: [cx, cy], direccion: [dx / norma, dy / norma] };
}

/** Distancia perpendicular de un punto a una recta {punto,direccion}. */
export function distanciaARecta(recta, punto) {
  const [px, py] = recta.punto;
  const [dx, dy] = recta.direccion;
  const vx = punto[0] - px, vy = punto[1] - py;
  // componente perpendicular = proyeccion sobre la normal (-dy,dx)
  return Math.abs(vx * -dy + vy * dx);
}

/** Interseccion de dos rectas {punto,direccion}. Devuelve null si son
 * (casi) paralelas. */
export function interseccionRectas(r1, r2) {
  const [p1x, p1y] = r1.punto;
  const [d1x, d1y] = r1.direccion;
  const [p2x, p2y] = r2.punto;
  const [d2x, d2y] = r2.direccion;
  const denom = d1x * d2y - d1y * d2x;
  if (Math.abs(denom) < 1e-9) return null;
  const t = ((p2x - p1x) * d2y - (p2y - p1y) * d2x) / denom;
  return [p1x + t * d1x, p1y + t * d1y];
}

/**
 * Ajusta una recta robusta a un conjunto de puntos con descarte de
 * atipicos: ajusta, calcula residuos perpendiculares, descarta los que
 * superen un umbral basado en la MAD (median absolute deviation) y
 * reajusta una vez con los puntos que sobreviven. Devuelve
 * {recta, usados, descartados} (o null si quedan menos de 2 puntos).
 */
export function ajustarRectaRobusta(puntos, factorMad = 3.5, pisoPx = 1.2) {
  if (puntos.length < 2) return null;
  let recta = ajustarRectaMinCuadrados(puntos);
  if (puntos.length < 4) return { recta, usados: puntos.length, descartados: 0 };

  const residuos = puntos.map((p) => distanciaARecta(recta, p));
  const ordenados = [...residuos].sort((a, b) => a - b);
  const mediana = ordenados[Math.floor(ordenados.length / 2)];
  const desviaciones = residuos.map((r) => Math.abs(r - mediana)).sort((a, b) => a - b);
  const mad = desviaciones[Math.floor(desviaciones.length / 2)];
  const umbral = Math.max(pisoPx, factorMad * 1.4826 * mad);

  const buenos = puntos.filter((_, i) => residuos[i] <= umbral);
  if (buenos.length >= 2) {
    recta = ajustarRectaMinCuadrados(buenos);
    return { recta, usados: buenos.length, descartados: puntos.length - buenos.length };
  }
  return { recta, usados: puntos.length, descartados: 0 };
}

// ---------------------------------------------------------------------------
// Refinamiento de bordes: busca, a lo largo de cada arista del quad, el
// maximo del gradiente de intensidad en perpendiculares muestreadas, ajusta
// una recta robusta a esos maximos, e intersecta las 4 rectas resultantes.
// ---------------------------------------------------------------------------

/**
 * Busca, a lo largo del segmento p1-p2, el borde real de la imagen: para
 * varios puntos a lo largo del segmento (evitando los extremos, donde cerca
 * de la esquina el borde real puede curvarse) muestrea un perfil de
 * intensidad perpendicular al segmento y ubica el maximo del gradiente
 * (mayor salto de intensidad = borde real papel/fondo). Ajusta una recta
 * robusta a esos puntos refinados.
 *
 * `muestreadorGris(x,y)` debe devolver la intensidad (0-255) en ese punto
 * de la imagen FUENTE (usualmente un cierre sobre muestrearGrisBilineal).
 */
export function refinarArista(muestreadorGris, p1, p2, opciones = {}) {
  const {
    numMuestras = 24,
    margenExtremos = 0.08,
    radioBusqueda = 16,
    pasoPerfil = 1,
  } = opciones;

  const largo = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) || 1;
  const tx = (p2[0] - p1[0]) / largo;
  const ty = (p2[1] - p1[1]) / largo;
  // Normal perpendicular (rotacion 90 grados de la tangente).
  const nx = -ty;
  const ny = tx;

  const puntosRefinados = [];
  const puntajes = [];
  for (let i = 0; i < numMuestras; i++) {
    const t = margenExtremos + (i / (numMuestras - 1)) * (1 - 2 * margenExtremos);
    const bx = p1[0] + t * (p2[0] - p1[0]);
    const by = p1[1] + t * (p2[1] - p1[1]);

    const perfil = [];
    for (let r = -radioBusqueda; r <= radioBusqueda; r += pasoPerfil) {
      perfil.push(muestreadorGris(bx + r * nx, by + r * ny));
    }
    // Gradiente central; se ignoran los extremos del perfil (no tienen
    // vecino de un lado) para no confundir un recorte del perfil con borde.
    let mejorIdx = -1;
    let mejorGrad = -1;
    for (let k = 1; k < perfil.length - 1; k++) {
      const grad = Math.abs(perfil[k + 1] - perfil[k - 1]);
      if (grad > mejorGrad) {
        mejorGrad = grad;
        mejorIdx = k;
      }
    }
    if (mejorIdx < 0) continue;
    const rMax = -radioBusqueda + mejorIdx * pasoPerfil;
    puntosRefinados.push([bx + rMax * nx, by + rMax * ny]);
    puntajes.push(mejorGrad);
  }

  if (puntosRefinados.length < 3) {
    // Sin señal suficiente: se conserva el segmento original.
    return { recta: ajustarRectaMinCuadrados([p1, p2]), usados: 0, descartados: numMuestras };
  }

  // Descarta puntos de bajo contraste (probable sombra o mancha, no borde
  // real) antes de ajustar la recta: se exige al menos 20% del mejor
  // puntaje de la arista.
  const maxPuntaje = Math.max(...puntajes);
  const filtrados = puntosRefinados.filter((_, i) => puntajes[i] >= maxPuntaje * 0.2);
  const base = filtrados.length >= 3 ? filtrados : puntosRefinados;

  const ajuste = ajustarRectaRobusta(base);
  return {
    recta: ajuste.recta,
    usados: ajuste.usados,
    descartados: numMuestras - ajuste.usados,
  };
}

/**
 * Refina las 4 esquinas de un quad ajustando sus 4 aristas a los bordes
 * reales de la imagen (ver refinarArista) y recalculando las esquinas como
 * interseccion de las rectas ajustadas. Si alguna interseccion falla o se
 * aleja demasiado de la esquina original (posible ajuste erroneo), esa
 * esquina puntual se conserva sin cambios y se avisa.
 */
export function refinarBordesQuad(muestreadorGris, quad, opciones = {}) {
  const [tl, tr, br, bl] = quad;
  const aristas = {
    superior: refinarArista(muestreadorGris, tl, tr, opciones),
    derecha: refinarArista(muestreadorGris, tr, br, opciones),
    inferior: refinarArista(muestreadorGris, br, bl, opciones),
    izquierda: refinarArista(muestreadorGris, bl, tl, opciones),
  };

  const diagonal = Math.hypot(br[0] - tl[0], br[1] - tl[1]);
  const limiteDesvio = diagonal * 0.12; // no se permite mover una esquina mas de un 12% de la diagonal

  function esquinaSegura(nueva, original) {
    if (!nueva || Number.isNaN(nueva[0]) || Number.isNaN(nueva[1])) return { punto: original, ok: false };
    const dist = Math.hypot(nueva[0] - original[0], nueva[1] - original[1]);
    if (dist > limiteDesvio) return { punto: original, ok: false };
    return { punto: nueva, ok: true };
  }

  const nuevaTL = esquinaSegura(interseccionRectas(aristas.izquierda.recta, aristas.superior.recta), tl);
  const nuevaTR = esquinaSegura(interseccionRectas(aristas.superior.recta, aristas.derecha.recta), tr);
  const nuevaBR = esquinaSegura(interseccionRectas(aristas.derecha.recta, aristas.inferior.recta), br);
  const nuevaBL = esquinaSegura(interseccionRectas(aristas.inferior.recta, aristas.izquierda.recta), bl);

  const avisos = [];
  [
    ["superior izquierda", nuevaTL],
    ["superior derecha", nuevaTR],
    ["inferior derecha", nuevaBR],
    ["inferior izquierda", nuevaBL],
  ].forEach(([nombre, r]) => {
    if (!r.ok) avisos.push(`No se pudo refinar con confianza la esquina ${nombre}; se conservo la marcada a mano.`);
  });

  return {
    quad: [nuevaTL.punto, nuevaTR.punto, nuevaBR.punto, nuevaBL.punto],
    aristas,
    avisos,
  };
}
