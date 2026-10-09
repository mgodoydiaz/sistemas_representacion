// almacen.js - persistencia de calificaciones en localStorage,
// exportacion/importacion CSV y JSON.

const CLAVE = "visor_calificaciones_v1";

function claveCuadro(usuario, pagina, n) {
  return `${usuario}|${pagina}|${n}`;
}

/** Estructura en memoria: { "<usuario>|<pagina>|<n>": {veredicto, comentario, fecha} } */
let cache = null;

function cargarDeStorage() {
  if (cache) return cache;
  try {
    const raw = window.localStorage.getItem(CLAVE);
    cache = raw ? JSON.parse(raw) : {};
  } catch (err) {
    console.warn("No se pudo leer localStorage, se usara memoria volatil.", err);
    cache = {};
  }
  return cache;
}

function guardarEnStorage() {
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(cache));
  } catch (err) {
    console.warn("No se pudo escribir en localStorage.", err);
  }
}

export function obtener(usuario, pagina, n) {
  const datos = cargarDeStorage();
  return datos[claveCuadro(usuario, pagina, n)] || null;
}

export function guardar(usuario, pagina, n, { veredicto, comentario }) {
  const datos = cargarDeStorage();
  const k = claveCuadro(usuario, pagina, n);
  const anterior = datos[k] || {};
  datos[k] = {
    veredicto: veredicto !== undefined ? veredicto : anterior.veredicto || null,
    comentario: comentario !== undefined ? comentario : anterior.comentario || "",
    fecha: new Date().toISOString(),
  };
  guardarEnStorage();
  return datos[k];
}

export function borrarTodo() {
  cache = {};
  guardarEnStorage();
}

export function todasLasCalificaciones() {
  return { ...cargarDeStorage() };
}

export function reemplazarTodo(obj) {
  cache = obj && typeof obj === "object" ? obj : {};
  guardarEnStorage();
}

/** Cuenta cuadros calificados y total por pagina de un alumno. */
export function progresoAlumno(alumno) {
  let total = 0;
  let calificados = 0;
  let correctos = 0;
  (alumno.paginas || []).forEach((pg) => {
    (pg.celdas || []).forEach((c) => {
      total += 1;
      const cal = obtener(alumno.usuario, pg.pagina, c.n);
      if (cal && cal.veredicto) {
        calificados += 1;
        if (cal.veredicto === "correcto") correctos += 1;
      }
    });
  });
  return { total, calificados, correctos };
}

// ---------------- Exportacion / importacion ----------------

function descargarArchivo(nombre, contenido, tipo) {
  const blob = new Blob([contenido], { type: tipo });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function csvEscapar(valor) {
  const s = String(valor === undefined || valor === null ? "" : valor);
  if (/[",\n;]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/** Genera y descarga el CSV con columnas usuario,pagina,cuadro,veredicto,comentario,fecha */
export function exportarCSV(manifest) {
  const filas = [["usuario", "pagina", "cuadro", "veredicto", "comentario", "fecha"]];
  (manifest.alumnos || []).forEach((al) => {
    (al.paginas || []).forEach((pg) => {
      (pg.celdas || []).forEach((c) => {
        const cal = obtener(al.usuario, pg.pagina, c.n);
        filas.push([
          al.usuario,
          pg.pagina,
          c.n,
          cal && cal.veredicto ? cal.veredicto : "",
          cal && cal.comentario ? cal.comentario : "",
          cal && cal.fecha ? cal.fecha : "",
        ]);
      });
    });
  });
  const csv = filas.map((f) => f.map(csvEscapar).join(",")).join("\r\n");
  const fecha = new Date().toISOString().slice(0, 10);
  descargarArchivo(`calificaciones_${fecha}.csv`, csv, "text/csv;charset=utf-8");
}

/** Genera y descarga un JSON con todas las calificaciones tal como se guardan. */
export function exportarJSON() {
  const datos = todasLasCalificaciones();
  const fecha = new Date().toISOString().slice(0, 10);
  descargarArchivo(
    `calificaciones_${fecha}.json`,
    JSON.stringify({ version: 1, calificaciones: datos }, null, 1),
    "application/json"
  );
}

/** Importa un JSON previamente exportado (o compatible) y lo fusiona con lo existente. */
export function importarJSON(objeto) {
  if (!objeto || typeof objeto !== "object") {
    throw new Error("El archivo no tiene el formato esperado.");
  }
  const entrante = objeto.calificaciones && typeof objeto.calificaciones === "object"
    ? objeto.calificaciones
    : objeto; // tolera un JSON plano {clave: {...}}
  const datos = cargarDeStorage();
  Object.assign(datos, entrante);
  guardarEnStorage();
}

/** Resumen por alumno: correctos/parciales/incorrectos/total. */
export function resumenPorAlumno(manifest) {
  return (manifest.alumnos || []).map((al) => {
    let correctos = 0, parciales = 0, incorrectos = 0, total = 0;
    (al.paginas || []).forEach((pg) => {
      (pg.celdas || []).forEach((c) => {
        total += 1;
        const cal = obtener(al.usuario, pg.pagina, c.n);
        if (cal && cal.veredicto === "correcto") correctos += 1;
        else if (cal && cal.veredicto === "parcial") parciales += 1;
        else if (cal && cal.veredicto === "incorrecto") incorrectos += 1;
      });
    });
    return { usuario: al.usuario, correctos, parciales, incorrectos, total };
  });
}
