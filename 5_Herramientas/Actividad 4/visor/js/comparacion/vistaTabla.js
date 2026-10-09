// vistaTabla.js - tabs de PARTE (Parte 1 · Vistas / Parte 2 · Isometricos)
// y tabla de los 6 cuadros (porcentaje, semaforo, desplazamiento) de la
// pagina de comparacion.

import { PARTES } from "../partes.js";

// Umbrales del semaforo (ajustables): solo una guia visual rapida, el
// numero exacto siempre se muestra al lado. No tienen relacion con los
// pesos de comparador/similitud.py (esos deciden el porcentaje en si; esto
// solo decide de que color se pinta ese porcentaje ya calculado).
const UMBRAL_ALTO = 80; // >= esto: verde
const UMBRAL_MEDIO = 50; // >= esto (y < UMBRAL_ALTO): ambar; menos: rojo

function claseSemaforo(porcentaje) {
  if (porcentaje === null || porcentaje === undefined) return "cmp-semaforo-vacio";
  if (porcentaje >= UMBRAL_ALTO) return "cmp-semaforo-alto";
  if (porcentaje >= UMBRAL_MEDIO) return "cmp-semaforo-medio";
  return "cmp-semaforo-bajo";
}

function textoDesplazamiento(resultado) {
  if (!resultado || resultado.error || !resultado.registro) return "-";
  const r = resultado.registro;
  const partes = [`dx=${r.dx}px`, `dy=${r.dy}px`];
  if (r.escala !== 1) partes.push(`escala=${r.escala}`);
  if (r.rotacion_grados) partes.push(`rot=${r.rotacion_grados}°`);
  return partes.join("  ");
}

/** Encuentra, dentro del listado de paginas de un alumno, la pagina real
 * (con su sufijo si lo tiene) que corresponde a una parte: exacta primero
 * ("vistas"), si no la primera cuyo tipo base coincida ("vistas_2"). null
 * si el alumno no tiene ninguna hoja de esa parte todavia. */
export function resolverPaginaParaParte(alumnoListado, parteId) {
  const paginas = (alumnoListado && alumnoListado.paginas) || [];
  const exacta = paginas.find((p) => p.pagina === parteId);
  if (exacta) return exacta.pagina;
  const porTipo = paginas.find((p) => p.tipo_base === parteId);
  return porTipo ? porTipo.pagina : null;
}

/**
 * Renderiza exactamente 2 tabs, "Parte 1 · Vistas" y "Parte 2 ·
 * Isometricos" (mismo control conceptual que el selector global de arriba,
 * ver js/partes.js): cada una resuelve a la pagina real del alumno para esa
 * parte (si tiene mas de una hoja del mismo tipo, o ninguna, se indica
 * debajo del nombre). `onCambiar(parteId)` se llama al hacer click.
 */
export function renderizarTabsPagina(contenedor, alumnoListado, parteActiva, onCambiar) {
  contenedor.innerHTML = "";
  contenedor.classList.add("selector-parte-tabs");
  PARTES.forEach((p) => {
    const pagina = resolverPaginaParaParte(alumnoListado, p.id);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "selector-parte-btn";
    if (p.id === parteActiva) btn.classList.add("activo");

    const principal = document.createElement("span");
    principal.textContent = p.etiqueta;
    btn.appendChild(principal);

    const sub = document.createElement("span");
    sub.className = "selector-parte-tab-sub";
    sub.textContent = !pagina ? "sin escanear" : pagina !== p.id ? `hoja: ${pagina}` : "escaneada";
    btn.appendChild(sub);

    btn.addEventListener("click", () => onCambiar(p.id));
    contenedor.appendChild(btn);
  });
}

/**
 * Renderiza la tabla de 6 cuadros de la pagina activa.
 * `resultadosPorN`: {1: resultado|null, ..., 6: resultado|null}; un
 * resultado puede traer {error:"..."} si la comparacion de ese cuadro
 * fallo (por ejemplo, el alumno no dibujo ese cuadro).
 */
export function renderizarTablaCuadros(tbody, { tienePauta, resultadosPorN, cuadroSeleccionado, cargando }, callbacks) {
  tbody.innerHTML = "";
  for (let n = 1; n <= 6; n++) {
    const resultado = resultadosPorN[n] || null;
    const tr = document.createElement("tr");
    tr.className = "cmp-fila" + (n === cuadroSeleccionado ? " seleccionada" : "");

    const tdN = document.createElement("td");
    tdN.textContent = `#${n}`;
    tr.appendChild(tdN);

    const tdPct = document.createElement("td");
    tdPct.className = "cmp-celda-pct";
    if (cargando) {
      const span = document.createElement("span");
      span.className = "cmp-sin-comparar";
      span.textContent = "comparando...";
      tdPct.appendChild(span);
    } else if (resultado && resultado.discrepancia_tipo) {
      const span = document.createElement("span");
      span.className = "chip chip-fallo";
      span.textContent = "tipo distinto";
      span.title = resultado.mensaje || "El tipo de esta hoja no coincide con el de la pauta.";
      tdPct.appendChild(span);
    } else if (resultado && resultado.error) {
      const span = document.createElement("span");
      span.className = "chip chip-fallo";
      span.textContent = "sin datos";
      span.title = resultado.error;
      tdPct.appendChild(span);
    } else if (resultado) {
      const barra = document.createElement("div");
      barra.className = "cmp-barra";
      const relleno = document.createElement("div");
      relleno.className = "cmp-barra-relleno " + claseSemaforo(resultado.porcentaje);
      relleno.style.width = `${Math.max(2, resultado.porcentaje)}%`;
      barra.appendChild(relleno);
      tdPct.appendChild(barra);

      const num = document.createElement("span");
      num.className = "cmp-pct-num";
      num.textContent = `${resultado.porcentaje.toFixed(1)}%`;
      tdPct.appendChild(num);

      if (resultado.aviso_tipo) {
        const avisoTipo = document.createElement("span");
        avisoTipo.className = "chip chip-aviso";
        avisoTipo.textContent = "revisar tipo";
        avisoTipo.title = resultado.aviso_tipo;
        tdPct.appendChild(avisoTipo);
      }
    } else {
      const span = document.createElement("span");
      span.className = "cmp-sin-comparar";
      span.textContent = "sin comparar";
      tdPct.appendChild(span);
    }
    tr.appendChild(tdPct);

    const tdDesp = document.createElement("td");
    tdDesp.className = "cmp-celda-desplazamiento";
    tdDesp.textContent = cargando ? "" : textoDesplazamiento(resultado);
    tr.appendChild(tdDesp);

    const tdAcc = document.createElement("td");
    const btnComparar = document.createElement("button");
    btnComparar.className = "boton boton-chico";
    btnComparar.textContent = resultado && !resultado.error && !resultado.discrepancia_tipo ? "Recomparar" : "Comparar";
    btnComparar.disabled = !tienePauta || cargando;
    btnComparar.title = tienePauta ? "" : "No hay pauta disponible para esta pagina.";
    btnComparar.addEventListener("click", (e) => {
      e.stopPropagation();
      callbacks.onComparar(n);
    });
    tdAcc.appendChild(btnComparar);
    tr.appendChild(tdAcc);

    if (resultado && !resultado.error && !resultado.discrepancia_tipo) {
      tr.classList.add("cmp-fila-clicable");
      tr.addEventListener("click", () => callbacks.onVerCuadro(n));
    }

    tbody.appendChild(tr);
  }
}
