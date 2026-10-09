// servidorHojas.js - funciones compartidas para los endpoints del contrato
// "hoja por parte" (mover_parte, tipo detectado) y el listado de
// comparacion. Vive junto a datos.js/almacen.js porque lo usan tanto el
// visor principal (index.html) como el escaner (escaner.html) y la pagina
// de comparacion (comparacion.html).
//
// /api/hoja/mover_parte y /api/hoja/tipo son un contrato acordado con quien
// mantiene servidor.py que puede no estar implementado todavia en el
// momento de usar esta pagina: toda llamada que reciba HTTP 404 se resuelve
// con una respuesta "no implementado" (o un error legible, segun la
// funcion) en vez de romper la interfaz.

async function leerJSON(resp) {
  let cuerpo = null;
  try {
    cuerpo = await resp.json();
  } catch (err) {
    // sin cuerpo JSON valido (o vacio): se sigue con cuerpo=null.
  }
  return cuerpo;
}

/** GET /api/comparacion/listado: usuarios, paginas (y, con el contrato
 * nuevo, tambien el resumen por parte) leidos del manifest en el servidor. */
export async function obtenerListado() {
  const resp = await fetch("/api/comparacion/listado", { cache: "no-store" });
  const cuerpo = await leerJSON(resp);
  if (!resp.ok) {
    const detalle = cuerpo && cuerpo.error ? cuerpo.error : `HTTP ${resp.status}`;
    throw new Error(detalle);
  }
  return cuerpo;
}

/**
 * GET /api/hoja/tipo?usuario=&pagina= : que tipo de lamina (vistas /
 * isometricos / indeterminado) detecta el servidor para una hoja ya
 * guardada como `pagina`. Nunca lanza: si el endpoint todavia no existe
 * (404), si el servidor da error, o si la red falla, devuelve
 * `{implementado:false}` para que quien llama pueda seguir funcionando sin
 * esta informacion (mostrando la interfaz igual, solo sin el aviso extra).
 */
export async function obtenerTipoHoja(usuario, pagina) {
  try {
    const resp = await fetch(
      `/api/hoja/tipo?usuario=${encodeURIComponent(usuario)}&pagina=${encodeURIComponent(pagina)}`,
      { cache: "no-store" }
    );
    if (resp.status === 404) return { implementado: false, motivo: "endpoint_no_encontrado" };
    const cuerpo = await leerJSON(resp);
    if (!resp.ok) {
      return { implementado: false, motivo: "error_servidor", error: (cuerpo && cuerpo.error) || `HTTP ${resp.status}` };
    }
    if (!cuerpo || typeof cuerpo !== "object") {
      return { implementado: false, motivo: "respuesta_invalida" };
    }
    return { implementado: true, ...cuerpo };
  } catch (err) {
    return { implementado: false, motivo: "red", error: err.message };
  }
}

/**
 * POST /api/hoja/mover_parte: reetiqueta una hoja ya guardada, moviendo sus
 * archivos de `paginaOrigen` a `paginaDestino` en el servidor. A diferencia
 * de `obtenerTipoHoja`, esta SI lanza en cualquier falla (incluyendo el
 * endpoint todavia no implementado): mover archivos es una accion que el
 * usuario pidio explicitamente, asi que un error debe verse, no
 * silenciarse.
 */
export async function moverParte(usuario, paginaOrigen, paginaDestino) {
  let resp;
  try {
    resp = await fetch("/api/hoja/mover_parte", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario, pagina_origen: paginaOrigen, pagina_destino: paginaDestino }),
    });
  } catch (err) {
    throw new Error(`No se pudo contactar al servidor: ${err.message}`);
  }
  if (resp.status === 404) {
    throw new Error(
      "El servidor todavia no tiene disponible /api/hoja/mover_parte (funcion pendiente en servidor.py)."
    );
  }
  const cuerpo = await leerJSON(resp);
  if (!resp.ok || !cuerpo || cuerpo.ok === false) {
    const detalle = (cuerpo && (cuerpo.error || cuerpo.mensaje)) || `HTTP ${resp.status}`;
    throw new Error(detalle);
  }
  return cuerpo;
}
