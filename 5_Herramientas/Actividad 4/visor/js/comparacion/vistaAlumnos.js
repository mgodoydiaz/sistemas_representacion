// vistaAlumnos.js - panel lateral de la pagina de comparacion: lista de
// usuarios (con buscador), poblada desde GET /api/comparacion/listado (que
// a su vez lee salida/manifest.json). Deliberadamente simple: a diferencia
// de vistaLista.js (visor principal) no conoce veredictos ni localStorage,
// solo el doble indicador de partes (sin_escanear/escaneada/comparada/con_nota).

import { construirIndicadorPartes } from "../estadoPartes.js";

export function renderizarListaAlumnos(contenedor, listado, filtro, usuarioActivo, onSeleccionar) {
  contenedor.innerHTML = "";
  const alumnos = (listado.alumnos || []).filter(
    (al) => !filtro || al.usuario.toLowerCase().includes(filtro.toLowerCase())
  );

  if (alumnos.length === 0) {
    const vacio = document.createElement("div");
    vacio.className = "alumno-meta";
    vacio.style.padding = "10px";
    vacio.textContent = "Sin resultados.";
    contenedor.appendChild(vacio);
    return;
  }

  alumnos.forEach((alumno) => {
    const tiposCubiertos = new Set((alumno.paginas || []).map((p) => p.tipo_base).filter(Boolean));

    const item = document.createElement("div");
    item.className = "alumno-item";
    item.setAttribute("role", "option");
    item.dataset.usuario = alumno.usuario;
    if (alumno.usuario === usuarioActivo) item.classList.add("seleccionado");

    const nombre = document.createElement("div");
    nombre.className = "alumno-nombre";
    const spanNombre = document.createElement("span");
    spanNombre.textContent = alumno.usuario;
    nombre.appendChild(spanNombre);
    nombre.appendChild(construirIndicadorPartes(alumno));
    item.appendChild(nombre);

    const meta = document.createElement("div");
    meta.className = "alumno-meta";

    if ((alumno.paginas || []).length !== tiposCubiertos.size) {
      const c = document.createElement("span");
      c.className = "chip chip-aviso";
      c.textContent = `${alumno.paginas.length} hojas`;
      meta.appendChild(c);
    }

    item.appendChild(meta);
    item.addEventListener("click", () => onSeleccionar(alumno.usuario));
    contenedor.appendChild(item);
  });
}

export function renderizarResumenListado(contenedor, listado) {
  contenedor.innerHTML = "";
  const total = (listado.alumnos || []).length;
  const div = document.createElement("div");
  div.textContent = `${total} alumno${total === 1 ? "" : "s"} disponible${total === 1 ? "" : "s"}.`;
  contenedor.appendChild(div);
}
