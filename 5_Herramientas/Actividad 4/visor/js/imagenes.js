// imagenes.js - carga de imagenes con cache y procesamiento de capas de
// trazo (tinte, dilatacion/grosor, umbral de alfa, inversion, rotacion,
// ajuste fino de posicion/escala). Todo hecho a mano sobre canvas.

const cacheImagenes = new Map();

/** Carga una imagen (con cache) devolviendo una promesa de HTMLImageElement. */
export function cargarImagen(url) {
  if (!url) return Promise.resolve(null);
  if (cacheImagenes.has(url)) return cacheImagenes.get(url);
  const p = new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null); // se resuelve null, el llamador decide como avisar
    img.src = url;
  });
  cacheImagenes.set(url, p);
  return p;
}

export function limpiarCache() {
  cacheImagenes.clear();
}

/**
 * Filtro de maximo (dilatacion) separable: aplica un pase horizontal y uno
 * vertical de "maximo en ventana de radio r" sobre el canal alfa. Es el
 * equivalente a una dilatacion morfologica con elemento estructurante
 * cuadrado de lado (2r+1), mucho mas rapido que una convolucion 2D directa.
 */
function dilatarAlfa(alfa, w, h, radio) {
  if (radio <= 0) return alfa;
  const tmp = new Uint8ClampedArray(w * h);
  const out = new Uint8ClampedArray(w * h);

  // Pase horizontal
  for (let y = 0; y < h; y++) {
    const base = y * w;
    for (let x = 0; x < w; x++) {
      let m = 0;
      const x0 = Math.max(0, x - radio);
      const x1 = Math.min(w - 1, x + radio);
      for (let xx = x0; xx <= x1; xx++) {
        const v = alfa[base + xx];
        if (v > m) m = v;
      }
      tmp[base + x] = m;
    }
  }
  // Pase vertical
  for (let x = 0; x < w; x++) {
    for (let y = 0; y < h; y++) {
      let m = 0;
      const y0 = Math.max(0, y - radio);
      const y1 = Math.min(h - 1, y + radio);
      for (let yy = y0; yy <= y1; yy++) {
        const v = tmp[yy * w + x];
        if (v > m) m = v;
      }
      out[y * w + x] = m;
    }
  }
  return out;
}

/**
 * Procesa una capa de trazo (imagen RGBA con solo alfa variable, color negro)
 * y devuelve un canvas del mismo tamaño con:
 *  - alfa dilatado segun `grosor` (0-6 px)
 *  - alfa recortado por `umbral` (0-255)
 *  - alfa invertido si `invertir`
 *  - color de relleno segun `tinte` ([r,g,b]) o negro si no se entrega
 *
 * No aplica rotacion ni desplazamiento: eso se hace en una etapa posterior
 * (transformarCanvas) para poder combinarlo con el resto de las capas.
 */
export function procesarTrazo(img, opts = {}) {
  const { grosor = 0, umbral = 10, invertir = false, tinte = null } = opts;
  const w = img && img.naturalWidth ? img.naturalWidth : 1000;
  const h = img && img.naturalHeight ? img.naturalHeight : 1000;

  const off = document.createElement("canvas");
  off.width = w;
  off.height = h;
  const ctx = off.getContext("2d", { willReadFrequently: true });

  if (img) {
    ctx.drawImage(img, 0, 0, w, h);
  }
  const imgData = ctx.getImageData(0, 0, w, h);
  const { data } = imgData;
  const n = w * h;
  let alfa = new Uint8ClampedArray(n);
  for (let i = 0; i < n; i++) alfa[i] = data[i * 4 + 3];

  if (grosor > 0) alfa = dilatarAlfa(alfa, w, h, grosor);

  const [tr, tg, tb] = tinte || [0, 0, 0];
  for (let i = 0; i < n; i++) {
    let a = alfa[i];
    if (a < umbral) a = 0;
    if (invertir) a = 255 - a;
    data[i * 4] = tr;
    data[i * 4 + 1] = tg;
    data[i * 4 + 2] = tb;
    data[i * 4 + 3] = a;
  }
  ctx.putImageData(imgData, 0, 0);
  return off;
}

/**
 * Dibuja `canvasFuente` sobre `ctxDestino` aplicando rotacion (en pasos de
 * 90 grados), desplazamiento (dx,dy) y escala, centrado en el cuadro.
 */
export function dibujarTransformado(ctxDestino, canvasFuente, { dx = 0, dy = 0, escala = 1, rotacion = 0 } = {}) {
  const w = ctxDestino.canvas.width;
  const h = ctxDestino.canvas.height;
  ctxDestino.save();
  ctxDestino.translate(w / 2 + dx, h / 2 + dy);
  ctxDestino.rotate((rotacion * Math.PI) / 180);
  ctxDestino.scale(escala, escala);
  ctxDestino.drawImage(canvasFuente, -w / 2, -h / 2, w, h);
  ctxDestino.restore();
}

/** Dibuja la imagen de fondo (escala de grises) tal cual, sin transformar. */
export function dibujarFondo(ctx, imgFondo, alpha = 1) {
  const w = ctx.canvas.width;
  const h = ctx.canvas.height;
  ctx.save();
  ctx.globalAlpha = alpha;
  if (imgFondo) {
    ctx.drawImage(imgFondo, 0, 0, w, h);
  } else {
    ctx.fillStyle = "#e6e6e6";
    ctx.fillRect(0, 0, w, h);
  }
  ctx.restore();
}

/**
 * Calcula, pixel a pixel, la diferencia entre dos capas de trazo ya
 * procesadas (mismo tamaño): devuelve un canvas donde:
 *  - gris  = ambos tienen trazo (coincide)
 *  - color `soloAlumno` = solo el alumno tiene trazo
 *  - color `soloPauta`  = solo la pauta tiene trazo
 *  - blanco = ninguno tiene trazo
 */
export function calcularDiferencia(canvasPauta, canvasAlumno, { soloAlumno = [205, 60, 55], soloPauta = [60, 110, 210], umbralPresencia = 40 } = {}) {
  const w = canvasPauta.width;
  const h = canvasPauta.height;
  const out = document.createElement("canvas");
  out.width = w;
  out.height = h;
  const octx = out.getContext("2d");

  const cp = canvasPauta.getContext("2d").getImageData(0, 0, w, h).data;
  const ca = canvasAlumno.getContext("2d").getImageData(0, 0, w, h).data;
  const res = octx.createImageData(w, h);
  const rd = res.data;

  for (let i = 0; i < w * h; i++) {
    const idx = i * 4;
    const aPauta = cp[idx + 3] >= umbralPresencia;
    const aAlumno = ca[idx + 3] >= umbralPresencia;
    let r, g, b;
    if (aPauta && aAlumno) {
      r = g = b = 120; // coincide -> gris
    } else if (aAlumno && !aPauta) {
      [r, g, b] = soloAlumno;
    } else if (aPauta && !aAlumno) {
      [r, g, b] = soloPauta;
    } else {
      r = g = b = 250; // ninguno -> casi blanco
    }
    rd[idx] = r;
    rd[idx + 1] = g;
    rd[idx + 2] = b;
    rd[idx + 3] = 255;
  }
  octx.putImageData(res, 0, 0);
  return out;
}
