// vistaNotas.js - panel de nota: promedios y nota sugerida (solo lectura,
// derivados de los porcentajes ya comparados) + nota final EDITABLE por el
// profesor + observaciones. El porcentaje sugiere, el profesor decide: la
// nota_sugerida jamas se manda sola al Excel, siempre se manda la
// nota_final que el profesor tenga en el campo (ver app.js:registrarEnExcel).
//
// El servidor promedia sobre lo que ya este comparado (comparador/
// notas_excel.py:calcular_fila), asi que si a una parte le falta escanearse
// o compararse la "nota sugerida" queda calculada solo con la otra: eso es
// exactamente lo que hay que dejar clarisimo aca en vez de mostrar un
// numero que parece completo sin estarlo (ver tarea).

import { PARTES } from "../partes.js";

function fmtPct(v) {
  return v === null || v === undefined ? "—" : `${v}%`;
}

/**
 * Pinta el resumen (promedios/sugerida) y precarga los campos editables.
 * `contexto` (opcional): { tienePaginaPorParte: {vistas,isometricos},
 * discrepanciaPorParte: {vistas,isometricos} } calculado en app.js a partir
 * del listado del servidor y de las ultimas comparaciones hechas.
 */
export function renderizarPanelNota(refs, resumen, contexto) {
  const tienePaginaPorParte = (contexto && contexto.tienePaginaPorParte) || {};
  const discrepanciaPorParte = (contexto && contexto.discrepanciaPorParte) || {};

  refs.notaResumen.innerHTML = "";
  const tabla = document.createElement("table");

  PARTES.forEach((p) => {
    const promedio = p.id === "vistas" ? resumen.promedio_vistas : resumen.promedio_isometricos;
    const discrepancia = discrepanciaPorParte[p.id];
    const tienePagina = tienePaginaPorParte[p.id];

    const tr = document.createElement("tr");
    if (discrepancia) tr.classList.add("nota-fila-discrepancia");
    const tdE = document.createElement("td");
    tdE.textContent = `Promedio ${p.etiquetaCorta}`;
    const tdV = document.createElement("td");
    tdV.style.textAlign = "right";
    if (discrepancia) {
      tdV.textContent = "tipo distinto";
      tdV.title = discrepancia.mensaje || "El tipo de esta hoja no coincide con la pauta.";
    } else if (!tienePagina) {
      tdV.textContent = "sin escanear";
    } else {
      tdV.textContent = fmtPct(promedio);
    }
    tr.appendChild(tdE);
    tr.appendChild(tdV);
    tabla.appendChild(tr);
  });

  const trSugerida = document.createElement("tr");
  const tdEsug = document.createElement("td");
  tdEsug.textContent = "Nota sugerida";
  const tdVsug = document.createElement("td");
  tdVsug.style.textAlign = "right";
  tdVsug.textContent =
    resumen.nota_sugerida === null || resumen.nota_sugerida === undefined ? "—" : resumen.nota_sugerida;
  trSugerida.appendChild(tdEsug);
  trSugerida.appendChild(tdVsug);
  tabla.appendChild(trSugerida);
  refs.notaResumen.appendChild(tabla);

  // Aviso explicito si falta escanear una parte, o si alguna quedo con
  // discrepancia de tipo: en ambos casos la "nota sugerida" de arriba NO
  // esta promediando sobre datos completos, y hay que decirlo en vez de
  // dejar que parezca un numero final.
  const conDiscrepancia = PARTES.filter((p) => discrepanciaPorParte[p.id]);
  const sinEscanear = PARTES.filter((p) => !discrepanciaPorParte[p.id] && !tienePaginaPorParte[p.id]);
  if (conDiscrepancia.length) {
    const aviso = document.createElement("div");
    aviso.className = "aviso-destacado error";
    aviso.innerHTML = conDiscrepancia
      .map((p) => `<strong>${p.etiqueta}</strong>: el tipo de la hoja no coincide con la pauta, no se promedia hasta corregir el etiquetado.`)
      .join("<br>");
    refs.notaResumen.appendChild(aviso);
  } else if (sinEscanear.length) {
    const aviso = document.createElement("div");
    aviso.className = "aviso-destacado alerta";
    aviso.innerHTML = `Todavia falta escanear <strong>${sinEscanear.map((p) => p.etiqueta).join(" y ")}</strong>. La nota sugerida de arriba promedia solo con lo que ya esta disponible, no reemplaza la parte que falta.`;
    refs.notaResumen.appendChild(aviso);
  }

  // Precarga el campo editable: si el alumno ya tenia una nota registrada
  // en el Excel se respeta esa (la puso el profesor a mano); si no, parte
  // de la sugerida como punto de partida, pero el campo sigue siendo 100%
  // editable en cualquier caso.
  const notaPrevia = resumen.nota_final_registrada;
  const haiPrevia = notaPrevia !== null && notaPrevia !== undefined;
  refs.inputNotaFinal.value = haiPrevia
    ? notaPrevia
    : resumen.nota_sugerida !== null && resumen.nota_sugerida !== undefined
    ? resumen.nota_sugerida
    : "";
  refs.inputObservaciones.value = resumen.observaciones_registradas || "";

  if (haiPrevia) {
    refs.notaEstado.textContent = `Ya registrado en el Excel (nota final actual: ${notaPrevia}).`;
    refs.notaEstado.className = "nota-estado nota-estado-ok";
  } else {
    refs.notaEstado.textContent = "Todavia no se ha registrado en el Excel para este alumno.";
    refs.notaEstado.className = "nota-estado";
  }
}

export function mostrarEstadoRegistro(refs, mensaje, tipo) {
  refs.notaEstado.textContent = mensaje;
  refs.notaEstado.className = "nota-estado" + (tipo ? ` nota-estado-${tipo}` : "");
}
