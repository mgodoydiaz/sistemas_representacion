// servidor.js - llamadas al servidor propio (servidor.py) para listar
// imagenes ya presentes y para guardar el resultado del escaner manual.

/** Lista las imagenes de entregas/ y pautas/ que el servidor puede ofrecer
 * como origen ("elegir una entrega ya presente en el servidor"). */
export async function listarImagenesServidor() {
  const resp = await fetch("/api/imagenes", { cache: "no-store" });
  if (!resp.ok) throw new Error(`No se pudo listar imagenes del servidor (HTTP ${resp.status}).`);
  return resp.json();
}

/**
 * Envia el resultado del escaner al servidor. `payload` debe tener:
 *   usuario, pagina, tipo_hoja (opcional),
 *   celdas: [{ n, imagen_png_base64, esquinas: [[x,y]x4] }, ...]
 *   hoja_png_base64 (opcional, solo modo "hoja completa")
 * Devuelve el JSON de respuesta del servidor (incluye avisos, por ejemplo
 * si no hay OpenCV disponible y la capa de trazo no se pudo generar).
 */
export async function guardarEnServidor(payload) {
  const resp = await fetch("/api/guardar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  let cuerpo = null;
  try {
    cuerpo = await resp.json();
  } catch (err) {
    // sin cuerpo JSON valido
  }
  if (!resp.ok) {
    const detalle = cuerpo && cuerpo.error ? cuerpo.error : `HTTP ${resp.status}`;
    throw new Error(`El servidor rechazo el guardado: ${detalle}`);
  }
  return cuerpo;
}
