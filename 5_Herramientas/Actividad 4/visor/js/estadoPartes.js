// estadoPartes.js - calcula, para un alumno y una parte (vistas/isometricos),
// uno de cuatro estados: "sin_escanear" | "escaneada" | "comparada" |
// "con_nota". Alimenta el doble indicador de la lista de alumnos (uno por
// parte) tanto en index.html como en comparacion.html.
//
// Usa el campo `partes` de GET /api/comparacion/listado cuando el servidor
// ya lo entrega (contrato nuevo, ver tarea). Si todavia no lo entrega (o no
// se pudo consultar el listado en absoluto), cae a un calculo aproximado
// con lo unico que se puede saber sin el: si la pagina esta presente o no
// (a partir del manifest/listado viejo). Ese calculo aproximado NO puede
// distinguir "comparada" de "con_nota", asi que se marca con
// `aproximado:true` para que la interfaz lo dejare claro (tooltip) en vez
// de aparentar una precision que no tiene.

import { tipoBasePagina } from "./datos.js";
import { PARTES } from "./partes.js";

export function etiquetaEstadoParte(estado) {
  switch (estado) {
    case "sin_escanear":
      return "sin escanear";
    case "escaneada":
      return "escaneada";
    case "comparada":
      return "comparada";
    case "con_nota":
      return "con nota";
    default:
      return estado || "sin datos";
  }
}

/**
 * `alumnoConPaginas` es cualquier objeto con `.paginas` (arreglo con al
 * menos `{pagina}`, como trae tanto manifest.json como el listado del
 * servidor) y, opcionalmente, `.partes` (contrato nuevo).
 */
export function estadoParte(alumnoConPaginas, parteId) {
  const partes = alumnoConPaginas && alumnoConPaginas.partes;
  const entradaNueva = partes && partes[parteId];
  if (entradaNueva && entradaNueva.estado) {
    return {
      estado: entradaNueva.estado,
      tipoDetectado: entradaNueva.tipo_detectado || null,
      confianzaTipo: typeof entradaNueva.confianza_tipo === "number" ? entradaNueva.confianza_tipo : null,
      aproximado: false,
    };
  }
  const paginas = (alumnoConPaginas && alumnoConPaginas.paginas) || [];
  const presente = paginas.some((p) => tipoBasePagina(p.pagina) === parteId);
  return {
    estado: presente ? "escaneada" : "sin_escanear",
    tipoDetectado: null,
    confianzaTipo: null,
    aproximado: true,
  };
}

/**
 * Construye (sin insertar en el DOM) el doble indicador de partes para un
 * alumno: un cuadrito por parte (1 y 2), coloreado segun su estado, con un
 * tooltip que explica el estado completo. Lo usan tanto vistaLista.js
 * (index.html) como vistaAlumnos.js (comparacion.html) para que las dos
 * listas de alumnos se vean consistentes.
 */
export function construirIndicadorPartes(alumnoConPaginas) {
  const cont = document.createElement("span");
  cont.className = "indicador-partes";
  PARTES.forEach((p) => {
    const info = estadoParte(alumnoConPaginas, p.id);
    const celda = document.createElement("span");
    celda.className = `indicador-parte indicador-parte-${info.estado}`;
    celda.textContent = String(p.numero);
    let titulo = `${p.etiqueta}: ${etiquetaEstadoParte(info.estado)}`;
    if (info.tipoDetectado && info.tipoDetectado !== p.id && info.tipoDetectado !== "indeterminado") {
      titulo += ` (el servidor detecta tipo "${info.tipoDetectado}": revisar etiquetado)`;
      celda.classList.add("indicador-parte-sospechosa");
    }
    if (info.aproximado) {
      titulo += " · estimado: el servidor todavia no informa el detalle de comparacion/nota para esta parte.";
    }
    celda.title = titulo;
    cont.appendChild(celda);
  });
  return cont;
}
