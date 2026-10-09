// api.js - llamadas HTTP a los endpoints de comparacion que expone
// servidor.py (ver servidor.py, seccion "Pagina de comparacion").

async function _json(resp) {
  let cuerpo = null;
  try {
    cuerpo = await resp.json();
  } catch (err) {
    // sin cuerpo JSON valido
  }
  if (!resp.ok) {
    const detalle = cuerpo && cuerpo.error ? cuerpo.error : `HTTP ${resp.status}`;
    throw new Error(detalle);
  }
  return cuerpo;
}

/** GET /api/comparacion/listado: usuarios, paginas y cuadros disponibles. */
export async function obtenerListado() {
  const resp = await fetch("/api/comparacion/listado", { cache: "no-store" });
  return _json(resp);
}

/** GET /api/comparacion/notas_alumno: resumen de porcentajes/nota sugerida. */
export async function obtenerNotasAlumno(usuario) {
  const resp = await fetch(`/api/comparacion/notas_alumno?usuario=${encodeURIComponent(usuario)}`, {
    cache: "no-store",
  });
  return _json(resp);
}

/** POST /api/comparacion/comparar: compara un cuadro contra su pauta. */
export async function compararCuadro(usuario, pagina, n, forzar = false) {
  const resp = await fetch("/api/comparacion/comparar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, pagina, n, forzar }),
  });
  return _json(resp);
}

/** POST /api/comparacion/comparar_pagina: compara los 6 cuadros de una pasada. */
export async function compararPagina(usuario, pagina, forzar = false) {
  const resp = await fetch("/api/comparacion/comparar_pagina", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, pagina, forzar }),
  });
  return _json(resp);
}

/** POST /api/comparacion/registrar_nota: registra/actualiza la fila del Excel. */
export async function registrarNota(usuario, notaFinal, observaciones) {
  const resp = await fetch("/api/comparacion/registrar_nota", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, nota_final: notaFinal, observaciones }),
  });
  return _json(resp);
}
