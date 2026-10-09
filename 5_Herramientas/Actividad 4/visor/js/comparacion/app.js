// app.js - orquesta la pagina de comparacion: carga el listado (servidor) y
// el manifest (para las rutas de imagen), maneja la seleccion de
// usuario/pagina/cuadro, dispara las comparaciones y el registro de notas.

import { carpetaDatos, cargarManifest, celdaAlumno, celdaPauta, rutaCompleta, tipoBasePagina } from "../datos.js";
import * as api from "./api.js";
import { renderizarListaAlumnos, renderizarResumenListado } from "./vistaAlumnos.js";
import { renderizarTabsPagina, renderizarTablaCuadros, resolverPaginaParaParte } from "./vistaTabla.js";
import { renderizarPanelNota, mostrarEstadoRegistro } from "./vistaNotas.js";
import { instalarSelectorParte, etiquetaParte, otraParte } from "../partes.js";
import { moverParte } from "../servidorHojas.js";
import { confirmar } from "../dialogo.js";

const refs = {
  buscador: document.getElementById("buscador-cmp"),
  listaAlumnos: document.getElementById("lista-alumnos-cmp"),
  resumenGeneral: document.getElementById("resumen-general-cmp"),
  fuenteDatos: document.getElementById("fuente-datos-cmp"),
  btnRecargar: document.getElementById("btn-recargar-cmp"),
  selectorParteContenedor: document.getElementById("selector-parte-contenedor"),

  vacio: document.getElementById("cmp-vacio"),
  contenido: document.getElementById("cmp-contenido"),
  usuarioTitulo: document.getElementById("cmp-usuario"),
  tabsPagina: document.getElementById("cmp-tabs-pagina"),
  btnMoverParte: document.getElementById("btn-mover-parte-cmp"),
  btnCompararPagina: document.getElementById("btn-comparar-pagina"),
  avisoPagina: document.getElementById("cmp-aviso-pagina"),
  tablaCuerpo: document.getElementById("cmp-tabla-cuerpo"),

  detalleVacio: document.getElementById("cmp-detalle-vacio"),
  detalleContenido: document.getElementById("cmp-detalle-contenido"),
  detalleTitulo: document.getElementById("cmp-detalle-titulo"),
  imgPauta: document.getElementById("img-pauta"),
  imgDiferencia: document.getElementById("img-diferencia"),
  imgAlumno: document.getElementById("img-alumno"),
  detalleMetricas: document.getElementById("cmp-detalle-metricas"),

  notaResumen: document.getElementById("nota-resumen"),
  inputNotaFinal: document.getElementById("input-nota-final"),
  inputObservaciones: document.getElementById("input-observaciones"),
  btnRegistrarExcel: document.getElementById("btn-registrar-excel"),
  notaEstado: document.getElementById("nota-estado"),
};

const estado = {
  base: carpetaDatos(),
  listado: null,
  manifest: null,
  filtro: "",
  usuarioActivo: null,
  parteActiva: "vistas", // Parte 1 / Parte 2, fuente de verdad de la pestana
  paginaActiva: null, // pagina real resuelta para parteActiva (puede ser null: sin escanear)
  resultados: {}, // {n: resultado|null}
  cuadroSeleccionado: null,
  cargandoPagina: false,
  // Ultima discrepancia de tipo detectada por el servidor, por parte
  // (persiste mientras no se vuelva a comparar esa parte sin discrepancia).
  discrepanciaPorParte: { vistas: null, isometricos: null },
};

let selectorParte = null;

function alumnoListadoActivo() {
  return (estado.listado.alumnos || []).find((a) => a.usuario === estado.usuarioActivo) || null;
}

function alumnoManifestActivo() {
  return (estado.manifest.alumnos || []).find((a) => a.usuario === estado.usuarioActivo) || null;
}

function paginaListadoActiva() {
  const al = alumnoListadoActivo();
  return al ? (al.paginas || []).find((p) => p.pagina === estado.paginaActiva) : null;
}

// ---------------- Carga inicial ----------------

async function iniciar() {
  refs.fuenteDatos.textContent = `datos: ${estado.base}`;
  try {
    const [listado, manifest] = await Promise.all([api.obtenerListado(), cargarManifest(estado.base)]);
    estado.listado = listado;
    estado.manifest = manifest;
  } catch (err) {
    mostrarErrorCarga(err.message);
    return;
  }

  selectorParte = instalarSelectorParte(refs.selectorParteContenedor, (parte) => {
    if (!estado.usuarioActivo) {
      estado.parteActiva = parte;
      return;
    }
    irAParte(parte);
  });
  estado.parteActiva = selectorParte.obtener();

  refrescarListaYResumen();
  instalarEventos();
}

function mostrarErrorCarga(mensaje) {
  refs.vacio.innerHTML = "";
  const p = document.createElement("p");
  p.style.color = "var(--incorrecto)";
  p.style.maxWidth = "480px";
  p.style.textAlign = "center";
  p.textContent = mensaje;
  refs.vacio.appendChild(p);
  refs.listaAlumnos.innerHTML = '<div class="alumno-meta" style="padding:10px">No hay datos que mostrar.</div>';
}

async function recargar() {
  refs.btnRecargar.disabled = true;
  const original = refs.btnRecargar.textContent;
  refs.btnRecargar.textContent = "Recargando...";
  try {
    const [listado, manifest] = await Promise.all([api.obtenerListado(), cargarManifest(estado.base)]);
    estado.listado = listado;
    estado.manifest = manifest;
    refrescarListaYResumen();
    if (estado.usuarioActivo) {
      irAParte(estado.parteActiva);
    }
  } catch (err) {
    alert("No se pudo recargar: " + err.message);
  } finally {
    refs.btnRecargar.disabled = false;
    refs.btnRecargar.textContent = original;
  }
}

function refrescarListaYResumen() {
  renderizarListaAlumnos(refs.listaAlumnos, estado.listado, estado.filtro, estado.usuarioActivo, seleccionarUsuario);
  renderizarResumenListado(refs.resumenGeneral, estado.listado);
}

// ---------------- Seleccion de usuario / pagina ----------------

function seleccionarUsuario(usuario) {
  estado.usuarioActivo = usuario;
  refs.vacio.classList.add("oculto");
  refs.contenido.classList.remove("oculto");
  refs.usuarioTitulo.textContent = usuario;
  refrescarListaYResumen();
  irAParte(estado.parteActiva);
}

/**
 * Cambia la parte activa (Parte 1 / Parte 2) y resuelve que pagina real del
 * alumno corresponde a esa parte (puede no haber ninguna: "sin escanear").
 * Es el unico lugar que mueve `estado.parteActiva`/`estado.paginaActiva`
 * juntos, para que el selector global de arriba, las tabs locales y la
 * tabla de cuadros nunca queden mostrando cosas distintas.
 */
function irAParte(parteId) {
  estado.parteActiva = parteId;
  if (selectorParte) selectorParte.fijar(parteId);
  const al = alumnoListadoActivo();
  estado.paginaActiva = al ? resolverPaginaParaParte(al, parteId) : null;
  estado.resultados = {};
  estado.cuadroSeleccionado = null;
  estado.cargandoPagina = false;

  renderTabs();
  ocultarDetalle();
  actualizarBotonMoverParte();
  refs.btnCompararPagina.disabled = !estado.paginaActiva;
  refs.btnCompararPagina.title = estado.paginaActiva
    ? ""
    : "No hay ninguna hoja guardada para esta parte todavia: no hay nada que comparar.";

  if (estado.paginaActiva) {
    cargarPagina(); // ya refresca el panel de nota al terminar (ver cargarPagina)
  } else {
    mostrarAvisoPagina(`Este alumno no tiene ninguna hoja guardada como ${etiquetaParte(parteId)} todavia.`, "error");
    renderizarTablaCuadros(refs.tablaCuerpo, { tienePauta: false, resultadosPorN: {}, cuadroSeleccionado: null, cargando: false }, callbacksTabla());
    cargarNotas();
  }
}

function renderTabs() {
  const al = alumnoListadoActivo();
  if (!al) return;
  renderizarTabsPagina(refs.tabsPagina, al, estado.parteActiva, irAParte);
}

/** Boton "Mover esta hoja a la otra parte": solo visible si hay algo
 * guardado en la parte activa (si no, no hay archivos que mover). */
function actualizarBotonMoverParte() {
  if (!estado.paginaActiva) {
    refs.btnMoverParte.classList.add("oculto");
    return;
  }
  const tipoActual = tipoBasePagina(estado.paginaActiva) || estado.parteActiva;
  const destino = otraParte(tipoActual);
  refs.btnMoverParte.textContent = `Mover esta hoja a ${etiquetaParte(destino)}`;
  refs.btnMoverParte.dataset.destino = destino;
  refs.btnMoverParte.classList.remove("oculto");
}

async function moverHojaActivaAOtraParte(destinoForzado) {
  const usuario = estado.usuarioActivo;
  const paginaOrigen = estado.paginaActiva;
  const destino = destinoForzado || refs.btnMoverParte.dataset.destino;
  if (!usuario || !paginaOrigen || !destino) return;

  const ok = await confirmar({
    titulo: "Mover hoja a la otra parte",
    mensaje:
      `Esto va a mover en el servidor los archivos de "${usuario}" ` +
      `guardados como "${paginaOrigen}" hacia ${etiquetaParte(destino)}.\n\n` +
      "Es un cambio en disco (no solo en esta pantalla). ¿Confirmas?",
    textoConfirmar: `Mover a ${etiquetaParte(destino)}`,
    claseConfirmar: "boton-mover-parte",
  });
  if (!ok) return;

  refs.btnMoverParte.disabled = true;
  const original = refs.btnMoverParte.textContent;
  refs.btnMoverParte.textContent = "Moviendo...";
  try {
    await moverParte(usuario, paginaOrigen, destino);
    const [listado, manifest] = await Promise.all([api.obtenerListado(), cargarManifest(estado.base)]);
    estado.listado = listado;
    estado.manifest = manifest;
    estado.discrepanciaPorParte = { vistas: null, isometricos: null };
    refrescarListaYResumen();
    irAParte(destino);
  } catch (err) {
    mostrarAvisoPagina(`No se pudo mover la hoja: ${err.message}`, "error");
    // Solo se restaura el texto/destino de ANTES de mover si la operacion
    // fallo: si tuvo exito, irAParte() -> actualizarBotonMoverParte() ya
    // dejo el boton correcto para el nuevo estado (parte destino), y
    // pisarlo aqui con "original" volvia a mostrar el destino viejo.
    refs.btnMoverParte.textContent = original;
  } finally {
    refs.btnMoverParte.disabled = false;
  }
}

/** `accion` (opcional): {texto, onClick} agrega un boton dentro del aviso,
 * usado por ejemplo para "Mover a Parte X" cuando hay discrepancia de tipo. */
function mostrarAvisoPagina(mensaje, tipo, accion) {
  refs.avisoPagina.innerHTML = "";
  if (!mensaje) {
    refs.avisoPagina.classList.add("oculto");
    return;
  }
  refs.avisoPagina.className = "cmp-aviso" + (tipo ? ` ${tipo}` : "");
  const texto = document.createElement("div");
  texto.textContent = mensaje;
  refs.avisoPagina.appendChild(texto);
  if (accion) {
    const botonera = document.createElement("div");
    botonera.className = "aviso-destacado-acciones";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "boton boton-chico boton-mover-parte";
    btn.textContent = accion.texto;
    btn.addEventListener("click", accion.onClick);
    botonera.appendChild(btn);
    refs.avisoPagina.appendChild(botonera);
  }
  refs.avisoPagina.classList.remove("oculto");
}

/** Busca, entre los resultados de una comparacion, si algun cuadro vino con
 * discrepancia_tipo (el servidor detecto que la hoja del alumno es de un
 * tipo distinto al de la pauta contra la que se comparo). */
function primeraDiscrepancia(resultados) {
  return Object.values(resultados).find((r) => r && r.discrepancia_tipo) || null;
}

/** Actualiza estado.discrepanciaPorParte para la pagina recien comparada y,
 * si corresponde, muestra el aviso bloqueante con el boton para corregir el
 * etiquetado (en vez de dejar que se vea un porcentaje enganoso). Devuelve
 * la discrepancia encontrada (o null). */
function procesarDiscrepancia(pagina, resultados) {
  const tipoBase = tipoBasePagina(pagina) || estado.parteActiva;
  const discrepancia = primeraDiscrepancia(resultados);
  estado.discrepanciaPorParte[tipoBase] = discrepancia;
  if (discrepancia) {
    const tipoAlumno = discrepancia.tipo_alumno || "otra parte";
    mostrarAvisoPagina(
      discrepancia.mensaje ||
        `Esta hoja parece ser de ${etiquetaParte(tipoAlumno)}, pero se esta comparando contra la pauta de ${etiquetaParte(discrepancia.tipo_pauta || tipoBase)}.`,
      "error",
      {
        texto: `Mover a ${etiquetaParte(tipoAlumno)}`,
        onClick: () => moverHojaActivaAOtraParte(tipoAlumno),
      }
    );
  }
  return discrepancia;
}

// ---------------- Tabla de cuadros ----------------

function callbacksTabla() {
  return {
    onComparar: (n) => compararUno(n),
    onVerCuadro: (n) => verCuadro(n),
  };
}

function renderTabla() {
  const pg = paginaListadoActiva();
  const tienePauta = !!(pg && pg.tiene_pauta);
  renderizarTablaCuadros(
    refs.tablaCuerpo,
    {
      tienePauta,
      resultadosPorN: estado.resultados,
      cuadroSeleccionado: estado.cuadroSeleccionado,
      cargando: estado.cargandoPagina,
    },
    callbacksTabla()
  );
}

async function cargarPagina() {
  const usuario = estado.usuarioActivo;
  const pagina = estado.paginaActiva;
  const pg = paginaListadoActiva();
  mostrarAvisoPagina(null);

  if (!pg) {
    estado.resultados = {};
    renderTabla();
    await cargarNotas();
    return;
  }
  if (!pg.tiene_pauta) {
    mostrarAvisoPagina(`No hay pauta disponible para la pagina "${pagina}": no se puede comparar.`, "error");
    estado.resultados = {};
    renderTabla();
    await cargarNotas();
    return;
  }

  estado.cargandoPagina = true;
  renderTabla();
  try {
    // forzar=false: si ya se comparo antes y los archivos de trazo no
    // cambiaron, el servidor devuelve el resultado cacheado al instante
    // (ver servidor.py:comparar_cuadro) en vez de recalcular.
    const respuesta = await api.compararPagina(usuario, pagina, false);
    const nuevos = {};
    const errores = [];
    respuesta.resultados.forEach((r) => {
      nuevos[r.n] = r;
      if (r.error) errores.push(`Cuadro ${r.n}: ${r.error}`);
    });
    estado.resultados = nuevos;
    const discrepancia = procesarDiscrepancia(pagina, nuevos);
    if (!discrepancia && errores.length) {
      mostrarAvisoPagina(errores.join("  ·  "), "");
    }
  } catch (err) {
    mostrarAvisoPagina(`No se pudo comparar la pagina: ${err.message}`, "error");
  } finally {
    estado.cargandoPagina = false;
    renderTabla();
    // Se refresca el panel de nota siempre al terminar (exito o error):
    // esta pagina puede ser "vistas" o "isometricos", que es justo lo que
    // alimenta el promedio/nota sugerida, y el profesor no deberia tener
    // que apretar otro boton para verlo actualizado.
    await cargarNotas();
  }
}

async function compararTodaLaPagina() {
  if (!estado.paginaActiva) return; // sin hoja guardada para esta parte: nada que comparar
  refs.btnCompararPagina.disabled = true;
  const original = refs.btnCompararPagina.textContent;
  refs.btnCompararPagina.textContent = "Comparando...";
  const usuario = estado.usuarioActivo;
  const pagina = estado.paginaActiva;
  mostrarAvisoPagina(null);
  estado.cargandoPagina = true;
  renderTabla();
  try {
    const respuesta = await api.compararPagina(usuario, pagina, true); // forzar: el profesor pidio explicitamente comparar de nuevo
    const nuevos = {};
    const errores = [];
    respuesta.resultados.forEach((r) => {
      nuevos[r.n] = r;
      if (r.error) errores.push(`Cuadro ${r.n}: ${r.error}`);
    });
    estado.resultados = nuevos;
    const discrepancia = procesarDiscrepancia(pagina, nuevos);
    if (!discrepancia && errores.length) mostrarAvisoPagina(errores.join("  ·  "), "");
    await cargarNotas();
  } catch (err) {
    mostrarAvisoPagina(`No se pudo comparar la pagina: ${err.message}`, "error");
  } finally {
    estado.cargandoPagina = false;
    renderTabla();
    refs.btnCompararPagina.disabled = false;
    refs.btnCompararPagina.textContent = original;
  }
}

async function compararUno(n) {
  const usuario = estado.usuarioActivo;
  const pagina = estado.paginaActiva;
  mostrarAvisoPagina(null);
  try {
    const resultado = await api.compararCuadro(usuario, pagina, n, true); // forzar: boton explicito del profesor
    estado.resultados = { ...estado.resultados, [n]: resultado };
    procesarDiscrepancia(pagina, estado.resultados);
    renderTabla();
    if (estado.cuadroSeleccionado === n) mostrarDetalle(n);
    await cargarNotas();
  } catch (err) {
    mostrarAvisoPagina(`Cuadro ${n}: ${err.message}`, "error");
  }
}

// ---------------- Detalle del cuadro ----------------

function ocultarDetalle() {
  refs.detalleVacio.classList.remove("oculto");
  refs.detalleContenido.classList.add("oculto");
}

function verCuadro(n) {
  estado.cuadroSeleccionado = n;
  renderTabla();
  mostrarDetalle(n);
}

function mostrarDetalle(n) {
  const resultado = estado.resultados[n];
  if (!resultado || resultado.error || resultado.discrepancia_tipo) {
    ocultarDetalle();
    return;
  }

  const alumnoManifest = alumnoManifestActivo();
  const celdaAl = alumnoManifest ? celdaAlumno(alumnoManifest, estado.paginaActiva, n) : null;
  const celdaPa = celdaPauta(estado.manifest, estado.paginaActiva, n);

  refs.detalleVacio.classList.add("oculto");
  refs.detalleContenido.classList.remove("oculto");
  refs.detalleTitulo.textContent = `${estado.usuarioActivo} · ${estado.paginaActiva} · cuadro ${n}`;

  refs.imgPauta.src = celdaPa && celdaPa.trazo ? rutaCompleta(estado.base, celdaPa.trazo) : "";
  refs.imgAlumno.src = celdaAl && celdaAl.trazo ? rutaCompleta(estado.base, celdaAl.trazo) : "";
  refs.imgDiferencia.src = rutaCompleta(estado.base, resultado.mapa_diferencia);

  const m = resultado.metricas;
  const r = resultado.registro;
  refs.detalleMetricas.innerHTML = "";
  const filas = [
    ["Porcentaje", `${resultado.porcentaje.toFixed(1)}%`],
    ["IoU con tolerancia", m.iou_tolerante],
    ["Precision", m.precision],
    ["Cobertura", m.cobertura],
    ["F-score", m.f_score],
    ["Chamfer promedio", `${m.chamfer_promedio_px} px (${m.chamfer_promedio_casillas} casillas)`],
    ["Desplazamiento", `dx=${r.dx}px, dy=${r.dy}px`],
    ["Escala / rotacion", `${r.escala} / ${r.rotacion_grados}°`],
    ["Calculado", resultado.calculado],
  ];
  filas.forEach(([etiqueta, valor]) => {
    const div = document.createElement("div");
    const spanE = document.createElement("span");
    spanE.textContent = etiqueta;
    const spanV = document.createElement("span");
    spanV.textContent = valor;
    div.appendChild(spanE);
    div.appendChild(spanV);
    refs.detalleMetricas.appendChild(div);
  });
}

// ---------------- Panel de nota ----------------

function contextoNotas() {
  const al = alumnoListadoActivo();
  return {
    tienePaginaPorParte: {
      vistas: !!(al && resolverPaginaParaParte(al, "vistas")),
      isometricos: !!(al && resolverPaginaParaParte(al, "isometricos")),
    },
    discrepanciaPorParte: estado.discrepanciaPorParte,
  };
}

async function cargarNotas() {
  if (!estado.usuarioActivo) return;
  try {
    const resumen = await api.obtenerNotasAlumno(estado.usuarioActivo);
    renderizarPanelNota(refs, resumen, contextoNotas());
  } catch (err) {
    mostrarEstadoRegistro(refs, `No se pudo cargar el resumen de notas: ${err.message}`, "error");
  }
}

async function registrarEnExcel() {
  const usuario = estado.usuarioActivo;
  if (!usuario) return;

  const valorCrudo = refs.inputNotaFinal.value.trim();
  let notaFinal = null;
  if (valorCrudo !== "") {
    notaFinal = Number(valorCrudo);
    if (Number.isNaN(notaFinal) || notaFinal < 0 || notaFinal > 100) {
      mostrarEstadoRegistro(refs, "La nota final debe ser un numero entre 0 y 100.", "error");
      return;
    }
  }
  const observaciones = refs.inputObservaciones.value;

  refs.btnRegistrarExcel.disabled = true;
  const original = refs.btnRegistrarExcel.textContent;
  refs.btnRegistrarExcel.textContent = "Registrando...";
  try {
    const resultado = await api.registrarNota(usuario, notaFinal, observaciones);
    const donde = resultado.motor === "csv" ? "CSV de respaldo" : "Excel";
    let mensaje = `Registrado en el ${donde} (${resultado.actualizado ? "fila actualizada" : "fila nueva"}).`;
    if (resultado.aviso) mensaje += ` ${resultado.aviso}`;
    mostrarEstadoRegistro(refs, mensaje, "ok");
  } catch (err) {
    mostrarEstadoRegistro(refs, `No se pudo registrar: ${err.message}`, "error");
  } finally {
    refs.btnRegistrarExcel.disabled = false;
    refs.btnRegistrarExcel.textContent = original;
  }
}

// ---------------- Eventos ----------------

function instalarEventos() {
  refs.buscador.addEventListener("input", () => {
    estado.filtro = refs.buscador.value;
    refrescarListaYResumen();
  });
  refs.btnRecargar.addEventListener("click", recargar);
  refs.btnMoverParte.addEventListener("click", () => moverHojaActivaAOtraParte());
  refs.btnCompararPagina.addEventListener("click", compararTodaLaPagina);
  refs.btnRegistrarExcel.addEventListener("click", registrarEnExcel);
}

iniciar();
