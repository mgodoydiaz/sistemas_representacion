// imagenFuente.js - carga la imagen de trabajo (archivo local o URL del
// servidor) a un canvas en memoria a resolucion NATURAL (sin reducir), que
// es lo que necesitan tanto el warp final como el refinamiento de bordes
// para trabajar "por pixel".

function cargarImagenElemento(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("No se pudo decodificar la imagen."));
    img.src = src;
  });
}

/**
 * Carga una imagen (desde File o desde una URL relativa al servidor) y
 * devuelve un objeto con:
 *   ancho, alto        - dimensiones naturales
 *   canvas             - canvas offscreen con la imagen dibujada (sirve
 *                         para la lupa y para el warp final)
 *   obtenerDatos()     - ImageData completo (se calcula una sola vez y se
 *                         cachea; es lo que usan el warp y el refinamiento)
 *   obtenerGris()      - Float32Array de luminancia (una sola vez, para el
 *                         refinamiento de bordes, mas liviano que RGBA)
 */
export async function cargarImagenDeTrabajo(origen) {
  let url;
  let liberar = null;
  if (origen instanceof File || origen instanceof Blob) {
    url = URL.createObjectURL(origen);
    liberar = () => URL.revokeObjectURL(url);
  } else {
    url = origen;
  }

  let img;
  try {
    img = await cargarImagenElemento(url);
  } finally {
    if (liberar) liberar();
  }

  const ancho = img.naturalWidth;
  const alto = img.naturalHeight;
  const canvas = document.createElement("canvas");
  canvas.width = ancho;
  canvas.height = alto;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);

  let datosCache = null;
  let grisCache = null;

  return {
    ancho,
    alto,
    canvas,
    obtenerDatos() {
      if (!datosCache) datosCache = ctx.getImageData(0, 0, ancho, alto);
      return datosCache;
    },
    obtenerGris() {
      if (!grisCache) {
        const datos = this.obtenerDatos();
        const n = ancho * alto;
        grisCache = new Float32Array(n);
        const d = datos.data;
        for (let i = 0; i < n; i++) {
          const idx = i * 4;
          // Luminancia perceptual estandar (BT.601), suficiente para
          // detectar el salto papel/fondo en el gradiente.
          grisCache[i] = 0.299 * d[idx] + 0.587 * d[idx + 1] + 0.114 * d[idx + 2];
        }
      }
      return grisCache;
    },
  };
}
