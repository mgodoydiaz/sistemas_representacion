// vistaLista.js - panel lateral de alumnos: listado, busqueda, marca de
// corregidos y resumen general.

import { progresoAlumno, resumenPorAlumno } from "./almacen.js";
import { metodoEsFallido, metodoEsFallback, tipoBasePagina } from "./datos.js";
import { construirIndicadorPartes } from "./estadoPartes.js";

function estadoAlumno(alumno) {
  const paginas = alumno.paginas || [];
  const nPaginas = paginas.length;
  const confianzaProm =
    nPaginas > 0
      ? paginas.reduce((s, p) => s + (p.confianza || 0), 0) / nPaginas
      : 0;
  const avisos = paginas.reduce((s, p) => s + (p.avisos ? p.avisos.length : 0), 0);
  const tieneFallido = paginas.some((p) => metodoEsFallido(p.metodo));
  const tieneFallback = paginas.some((p) => metodoEsFallback(p.metodo));
  // Tipos de lamina cubiertos (vistas/isometricos), independiente de cuantas
  // hojas fisicas entrego: un alumno puede haber fotografiado 2 hojas de
  // isometricos juntas (vistas_2) o una hoja no reconocible (desconocida_N),
  // asi que "nPaginas" ya no es directamente comparable contra 2.
  const tiposCubiertos = new Set(paginas.map((p) => tipoBasePagina(p.pagina)).filter(Boolean));
  return { nPaginas, confianzaProm, avisos, tieneFallido, tieneFallback, tiposCubiertos };
}

/**
 * Renderiza la lista de alumnos dentro de `contenedor`.
 * `onSeleccionar(usuario)` se llama al hacer click en un alumno.
 * `usuarioActivo` resalta el seleccionado actualmente.
 */
export function renderizarLista(contenedor, manifest, filtro, usuarioActivo, onSeleccionar, listado) {
  contenedor.innerHTML = "";
  const alumnos = (manifest.alumnos || [])
    .slice()
    .sort((a, b) => a.usuario.localeCompare(b.usuario))
    .filter((al) => !filtro || al.usuario.toLowerCase().includes(filtro.toLowerCase()));

  if (alumnos.length === 0) {
    const vacio = document.createElement("div");
    vacio.className = "alumno-meta";
    vacio.style.padding = "10px";
    vacio.textContent = "Sin resultados.";
    contenedor.appendChild(vacio);
    return;
  }

  alumnos.forEach((alumno) => {
    const est = estadoAlumno(alumno);
    const prog = progresoAlumno(alumno);

    const item = document.createElement("div");
    item.className = "alumno-item";
    item.setAttribute("role", "option");
    item.dataset.usuario = alumno.usuario;
    if (alumno.usuario === usuarioActivo) item.classList.add("seleccionado");

    const completo = prog.total > 0 && prog.calificados === prog.total;
    const parcialProg = prog.calificados > 0 && !completo;

    const nombre = document.createElement("div");
    nombre.className = "alumno-nombre";
    const marca = document.createElement("span");
    marca.className =
      "marca-check" + (completo ? " completo" : parcialProg ? " parcial" : "");
    nombre.appendChild(marca);
    const spanNombre = document.createElement("span");
    spanNombre.textContent = alumno.usuario;
    nombre.appendChild(spanNombre);
    const alumnoListado = listado && (listado.alumnos || []).find((a) => a.usuario === alumno.usuario);
    nombre.appendChild(construirIndicadorPartes(alumnoListado || alumno));
    item.appendChild(nombre);

    const meta = document.createElement("div");
    meta.className = "alumno-meta";

    const chipPaginas = document.createElement("span");
    chipPaginas.className = "chip " + (est.tiposCubiertos.size >= 2 ? "chip-ok" : "chip-aviso");
    // "tipos" cuenta vistas/isometricos entregados (max 2); si ademas hay
    // mas hojas de las esperadas (hojas dobles, paginas no reconocidas) se
    // muestra aparte para no mostrar cosas como "4/2 paginas".
    chipPaginas.textContent = `${est.tiposCubiertos.size}/2 tipos`;
    meta.appendChild(chipPaginas);
    if (est.nPaginas !== est.tiposCubiertos.size) {
      const c = document.createElement("span");
      c.className = "chip chip-aviso";
      c.textContent = `${est.nPaginas} hojas`;
      c.title = "Cantidad de hojas/fotos entregadas, distinta de los tipos porque hay hojas duplicadas o no reconocidas.";
      meta.appendChild(c);
    }

    if (est.tieneFallido) {
      const c = document.createElement("span");
      c.className = "chip chip-fallo";
      c.textContent = "fallido";
      meta.appendChild(c);
    } else if (est.tieneFallback) {
      const c = document.createElement("span");
      c.className = "chip chip-aviso";
      c.textContent = "fallback";
      meta.appendChild(c);
    }

    if (est.avisos > 0) {
      const c = document.createElement("span");
      c.className = "chip chip-aviso";
      c.textContent = `${est.avisos} aviso${est.avisos > 1 ? "s" : ""}`;
      meta.appendChild(c);
    }

    const chipConf = document.createElement("span");
    chipConf.className = "chip " + (est.confianzaProm >= 0.8 ? "chip-ok" : "chip-aviso");
    chipConf.textContent = `conf. ${(est.confianzaProm * 100).toFixed(0)}%`;
    meta.appendChild(chipConf);

    const chipCorr = document.createElement("span");
    chipCorr.className = "chip " + (completo ? "chip-corregido" : "chip-pendiente");
    chipCorr.textContent = completo
      ? "corregido"
      : prog.calificados > 0
      ? `${prog.calificados}/${prog.total}`
      : "pendiente";
    meta.appendChild(chipCorr);

    item.appendChild(meta);
    item.addEventListener("click", () => onSeleccionar(alumno.usuario));
    contenedor.appendChild(item);
  });
}

/** Renderiza el resumen general (conteo de correctos por alumno) al pie del panel. */
export function renderizarResumen(contenedor, manifest) {
  const resumen = resumenPorAlumno(manifest);
  const totalAlumnos = resumen.length;
  const totalCorrectos = resumen.reduce((s, r) => s + r.correctos, 0);
  const totalCuadros = resumen.reduce((s, r) => s + r.total, 0);
  const totalCalificados = resumen.reduce(
    (s, r) => s + r.correctos + r.parciales + r.incorrectos,
    0
  );

  contenedor.innerHTML = "";
  const titulo = document.createElement("div");
  titulo.style.fontWeight = "600";
  titulo.style.marginBottom = "4px";
  titulo.style.color = "var(--texto)";
  titulo.textContent = `Progreso: ${totalCalificados}/${totalCuadros} cuadros`;
  contenedor.appendChild(titulo);

  const linea = document.createElement("div");
  linea.textContent = `${totalAlumnos} alumnos · ${totalCorrectos} correctos en total`;
  contenedor.appendChild(linea);
}
