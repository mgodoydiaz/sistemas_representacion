// datos.js - carga y acceso al manifest.json generado por el pipeline.

/**
 * Determina la carpeta base de datos a partir del parametro de URL
 * ?datos=... (relativo a la ubicacion de index.html). Por defecto usa
 * la carpeta real de salida hermana de visor/: ../salida
 */
export function carpetaDatos() {
  const params = new URLSearchParams(window.location.search);
  const param = params.get("datos");
  if (param) {
    // Se permite ruta relativa o absoluta tal cual la entregue el usuario.
    return param.endsWith("/") ? param.slice(0, -1) : param;
  }
  return "../salida";
}

export function rutaCompleta(base, rutaRelativa) {
  if (!rutaRelativa) return null;
  return `${base}/${rutaRelativa}`;
}

/**
 * Carga manifest.json desde la carpeta de datos. Lanza un error legible
 * si no existe o no es JSON valido (por ejemplo si salida/ aun no existe).
 */
export async function cargarManifest(base) {
  const url = `${base}/manifest.json`;
  let resp;
  try {
    resp = await fetch(url, { cache: "no-store" });
  } catch (err) {
    throw new Error(
      `No se pudo conectar a ${url}. ¿Esta corriendo el servidor y existe la carpeta de datos?`
    );
  }
  if (!resp.ok) {
    throw new Error(
      `No se encontro manifest.json en "${base}" (HTTP ${resp.status}). ` +
        `Puede que el proceso de recorte aun no haya generado salida/.`
    );
  }
  let data;
  try {
    data = await resp.json();
  } catch (err) {
    throw new Error(`manifest.json en "${base}" no es JSON valido.`);
  }
  return data;
}

/**
 * El rectificador nombra "pagina" como vistas / isometricos, y cuando un
 * alumno entrega mas de una hoja del mismo tipo (por ejemplo dos hojas de
 * isometricos fotografiadas juntas) agrega un sufijo: vistas_2, vistas_3,
 * isometricos_2, etc. (ver rectificar.siguiente_nombre_pagina). Las hojas
 * de tipo no reconocido quedan como desconocida_N y no tienen tipo base.
 * Esta funcion recupera el tipo base ("vistas"/"isometricos") de un nombre
 * de pagina con o sin sufijo, para poder ir a buscar la pauta correcta.
 */
export function tipoBasePagina(pagina) {
  if (!pagina) return null;
  const m = /^(vistas|isometricos)(?:_\d+)?$/.exec(pagina);
  return m ? m[1] : null;
}

/** Etiqueta legible para mostrar una pagina (tab, titulo, etc). */
export function etiquetaPagina(pagina) {
  if (!pagina) return "";
  const m = /^([a-zA-Z]+)(?:_(\d+))?$/.exec(pagina);
  if (!m) return pagina;
  const base = m[1];
  const nombre = base.charAt(0).toUpperCase() + base.slice(1);
  return m[2] ? `${nombre} ${m[2]}` : nombre;
}

/** Devuelve el arreglo de celdas de pauta para una pagina, o [] si no hay pauta.
 * Si no hay pauta con ese nombre exacto (por ejemplo "vistas_2"), cae al
 * tipo base ("vistas") para poder seguir comparando contra la misma pauta. */
export function celdasPauta(manifest, pagina) {
  const pautas = manifest.pautas || {};
  let p = pautas[pagina];
  if (!p || !Array.isArray(p.celdas)) {
    const base = tipoBasePagina(pagina);
    p = base ? pautas[base] : null;
  }
  if (!p || !Array.isArray(p.celdas) || p.celdas.length === 0) {
    return celdasPautaPorConvencion(pagina);
  }
  return p.celdas;
}

/** Respaldo cuando el manifest no trae registradas las pautas: se arman las
 * rutas por convencion de nombres, igual que hace servidor.py. Los archivos
 * que no existan quedaran como imagen rota, que el visor ya maneja. */
function celdasPautaPorConvencion(pagina) {
  const base = tipoBasePagina(pagina) || pagina;
  if (!base) return [];
  const celdas = [];
  for (let n = 1; n <= 6; n += 1) {
    celdas.push({
      n,
      img: `pautas/pauta_${base}_c${n}.png`,
      trazo: `pautas/pauta_${base}_c${n}_trazo.png`,
    });
  }
  return celdas;
}

export function celdaPauta(manifest, pagina, n) {
  return celdasPauta(manifest, pagina).find((c) => c.n === n) || null;
}

/** Devuelve la entrada de pagina de un alumno, o null si no la entrego. */
export function paginaAlumno(alumno, pagina) {
  if (!alumno || !Array.isArray(alumno.paginas)) return null;
  return alumno.paginas.find((p) => p.pagina === pagina) || null;
}

/** Una pagina "cuadro_suelto" trae una unica celda con n=0 (la foto era el
 * recorte de un solo ejercicio y no se pudo saber cual): ver
 * rectificador.nucleo.procesar_hoja / rectificar.generar_qa. Se muestra y
 * califica en el primer casillero (n=1) de la grilla. */
export function esPaginaCuadroSuelto(pg) {
  return !!pg && Array.isArray(pg.celdas) && pg.celdas.length === 1 && pg.celdas[0].n === 0;
}

export function celdaAlumno(alumno, pagina, n) {
  const pg = paginaAlumno(alumno, pagina);
  if (!pg) return null;
  if (esPaginaCuadroSuelto(pg)) {
    return n === 1 ? pg.celdas[0] : null;
  }
  return pg.celdas.find((c) => c.n === n) || null;
}

/** Lista de nombres de pagina que aparecen en la pauta y/o en algun alumno. */
export function listarPaginas(manifest) {
  const set = new Set();
  Object.keys(manifest.pautas || {}).forEach((p) => set.add(p));
  (manifest.alumnos || []).forEach((al) =>
    (al.paginas || []).forEach((p) => set.add(p.pagina))
  );
  return Array.from(set);
}

/** Lista de nombres de pagina que un alumno entrego, en un orden estable
 * (vistas/isometricos primero, luego sus variantes numeradas, luego las
 * desconocidas), para armar los tabs de la vista de contacto. */
export function paginasDeAlumno(alumno) {
  const paginas = (alumno && alumno.paginas) || [];
  return paginas
    .map((p) => p.pagina)
    .sort((a, b) => {
      const rango = (p) => (p.startsWith("vistas") ? 0 : p.startsWith("isometricos") ? 1 : 2);
      const ra = rango(a);
      const rb = rango(b);
      if (ra !== rb) return ra - rb;
      return a.localeCompare(b, "es", { numeric: true });
    });
}

export function metodoEsFallido(metodo) {
  return metodo === "fallido";
}
export function metodoEsFallback(metodo) {
  return metodo === "fallback";
}
export function metodoEsCuadroSuelto(metodo) {
  return metodo === "cuadro_suelto";
}
