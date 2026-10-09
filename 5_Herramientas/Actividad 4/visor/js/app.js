// app.js - orquesta la aplicacion: carga de datos, navegacion entre vistas,
// atajos de teclado y conexion entre el estado de calificaciones y la UI.

import { carpetaDatos, cargarManifest, paginasDeAlumno, etiquetaPagina, tipoBasePagina } from "./datos.js";
import * as almacen from "./almacen.js";
import { renderizarLista, renderizarResumen } from "./vistaLista.js";
import { renderizarContacto } from "./vistaContacto.js";
import { Comparador } from "./comparador.js";
import { limpiarCache } from "./imagenes.js";
import { instalarSelectorParte, etiquetaParte, otraParte } from "./partes.js";
import { obtenerListado, moverParte } from "./servidorHojas.js";
import { confirmar } from "./dialogo.js";

// ---------------- Referencias DOM ----------------

const refs = {
  buscador: document.getElementById("buscador"),
  listaAlumnos: document.getElementById("lista-alumnos"),
  resumenGeneral: document.getElementById("resumen-general"),
  fuenteDatos: document.getElementById("fuente-datos"),
  selectorParteContenedor: document.getElementById("selector-parte-contenedor"),

  vacioInicial: document.getElementById("vacio-inicial"),
  vistaContacto: document.getElementById("vista-contacto"),
  vistaComparador: document.getElementById("vista-comparador"),

  contactoUsuario: document.getElementById("contacto-usuario"),
  contactoTabs: document.getElementById("contacto-tabs"),
  contactoAvisos: document.getElementById("contacto-avisos"),
  contactoGrilla: document.getElementById("contacto-grilla"),
  btnMoverParte: document.getElementById("btn-mover-parte"),

  btnVolver: document.getElementById("btn-volver"),
  compUsuario: document.getElementById("comp-usuario"),
  compCuadroInfo: document.getElementById("comp-cuadro-info"),
  compNavIndicador: document.getElementById("comp-nav-indicador"),
  btnCuadroPrev: document.getElementById("btn-cuadro-prev"),
  btnCuadroNext: document.getElementById("btn-cuadro-next"),

  avisoCuadro: document.getElementById("aviso-cuadro"),
  canvasSuperpos: document.getElementById("canvas-superpos"),
  canvasLadoPauta: document.getElementById("canvas-lado-pauta"),
  canvasLadoAlumno: document.getElementById("canvas-lado-alumno"),
  viewportPauta: document.getElementById("viewport-pauta"),
  viewportAlumno: document.getElementById("viewport-alumno"),
  canvasCortinaPauta: document.getElementById("canvas-cortina-pauta"),
  canvasCortinaAlumno: document.getElementById("canvas-cortina-alumno"),
  cortinaContenedor: document.getElementById("cortina-contenedor"),
  cortinaRecorte: document.getElementById("cortina-recorte"),
  cortinaBarra: document.getElementById("cortina-barra"),
  canvasDiferencia: document.getElementById("canvas-diferencia"),

  modo1: document.getElementById("modo-1"),
  modo2: document.getElementById("modo-2"),
  modo3: document.getElementById("modo-3"),
  modo4: document.getElementById("modo-4"),

  ctlOpacidad: document.getElementById("ctl-opacidad"),
  outOpacidad: document.getElementById("out-opacidad"),
  ctlGrosorAlumno: document.getElementById("ctl-grosor-alumno"),
  outGrosorAlumno: document.getElementById("out-grosor-alumno"),
  ctlGrosorPauta: document.getElementById("ctl-grosor-pauta"),
  outGrosorPauta: document.getElementById("out-grosor-pauta"),
  ctlUmbral: document.getElementById("ctl-umbral"),
  outUmbral: document.getElementById("out-umbral"),
  ctlFondo: document.getElementById("ctl-fondo"),
  ctlInvertir: document.getElementById("ctl-invertir"),
  btnRotarIzq: document.getElementById("btn-rotar-izq"),
  btnRotarDer: document.getElementById("btn-rotar-der"),
  ajusteInfo: document.getElementById("ajuste-info"),
  btnResetAjuste: document.getElementById("btn-reset-ajuste"),

  comentario: document.getElementById("comentario"),
  veredictoEstado: document.getElementById("veredicto-estado"),

  btnRecargarDatos: document.getElementById("btn-recargar-datos"),
  btnExportarCSV: document.getElementById("btn-exportar-csv"),
  btnExportarJSON: document.getElementById("btn-exportar-json"),
  btnImportarJSON: document.getElementById("btn-importar-json"),
  inputImportar: document.getElementById("input-importar"),

  ayudaToggle: document.getElementById("btn-ayuda-toggle"),
  ayudaContenido: document.getElementById("ayuda-contenido"),
};

document.querySelectorAll(".modo-btn").forEach((b) => {
  refs[`modoBtn${b.dataset.modo}`] = b;
});
document.querySelectorAll(".veredicto-btn").forEach((b) => {
  refs[`veredictoBtn_${b.dataset.veredicto}`] = b;
});

// ---------------- Estado global ----------------

const estado = {
  base: carpetaDatos(),
  manifest: null,
  listado: null, // GET /api/comparacion/listado, para el doble indicador de partes (best-effort)
  filtro: "",
  usuarioActivo: null,
  paginaActiva: "vistas",
  parteActiva: "vistas", // se fija de verdad al iniciar, desde el selector global (localStorage)
  cuadroActivo: 1,
  vista: "inicial", // inicial | contacto | comparador
  globales: {
    opacidad: 0.5,
    grosorAlumno: 0,
    grosorPauta: 0,
    umbral: 10,
    mostrarFondo: true,
    invertir: false,
  },
  ajustes: new Map(), // clave usuario|pagina|n -> {dx,dy,escala,rotacion}
};

function claveAjuste(usuario, pagina, n) {
  return `${usuario}|${pagina}|${n}`;
}

function obtenerAjuste(usuario, pagina, n) {
  const k = claveAjuste(usuario, pagina, n);
  if (!estado.ajustes.has(k)) {
    estado.ajustes.set(k, { dx: 0, dy: 0, escala: 1, rotacion: 0 });
  }
  return estado.ajustes.get(k);
}

let comparador = null;
// Referencia al selector global de parte (instalado en iniciar()), para que
// moverHojaActivaAOtraParte tambien pueda cambiar la parte activa cuando
// una hoja se mueve (ver esa funcion mas abajo).
let selectorParte = null;

// ---------------- Carga inicial ----------------

async function iniciar() {
  refs.fuenteDatos.textContent = `datos: ${estado.base}`;
  try {
    estado.manifest = await cargarManifest(estado.base);
  } catch (err) {
    mostrarErrorCarga(err.message);
    return;
  }
  // El listado de comparacion es "best effort": solo alimenta el doble
  // indicador de partes en la lista de alumnos (estados comparada/con_nota).
  // Si falla (motor de comparacion no disponible, etc.) el visor sigue
  // funcionando igual, con el indicador aproximado (ver estadoPartes.js).
  try {
    estado.listado = await obtenerListado();
  } catch (err) {
    estado.listado = null;
  }

  selectorParte = instalarSelectorParte(refs.selectorParteContenedor, (parte) => {
    estado.parteActiva = parte;
    refrescarListaYResumen();
    if (estado.usuarioActivo && estado.vista !== "inicial") {
      seleccionarAlumno(estado.usuarioActivo);
    }
  });
  estado.parteActiva = selectorParte.obtener();

  comparador = new Comparador(refs);
  refrescarListaYResumen();
  instalarEventos();
}

function mostrarErrorCarga(mensaje) {
  refs.vacioInicial.innerHTML = "";
  const p = document.createElement("p");
  p.style.color = "var(--incorrecto)";
  p.style.maxWidth = "480px";
  p.style.textAlign = "center";
  p.textContent = mensaje;
  refs.vacioInicial.appendChild(p);
  refs.listaAlumnos.innerHTML =
    '<div class="alumno-meta" style="padding:10px">No hay datos que mostrar.</div>';
}

/**
 * Vuelve a leer manifest.json desde el servidor (por si el escaner manual
 * de laminas guardo algo nuevo) y refresca la vista actual sin perder la
 * seleccion de alumno/pagina/cuadro. Se limpia la cache de imagenes
 * (imagenes.js) para que los cuadros recien guardados no sigan mostrando
 * la version vieja que el navegador ya tenia en memoria.
 */
async function recargarDatos() {
  refs.btnRecargarDatos.disabled = true;
  const textoOriginal = refs.btnRecargarDatos.textContent;
  refs.btnRecargarDatos.textContent = "Recargando...";
  try {
    estado.manifest = await cargarManifest(estado.base);
    limpiarCache();
    if (estado.vista === "contacto" && estado.usuarioActivo) {
      mostrarContacto();
    } else if (estado.vista === "comparador" && estado.usuarioActivo) {
      await cargarCuadroActual();
    } else {
      refrescarListaYResumen();
    }
  } catch (err) {
    alert("No se pudo recargar manifest.json: " + err.message);
  } finally {
    refs.btnRecargarDatos.disabled = false;
    refs.btnRecargarDatos.textContent = textoOriginal;
  }
}

function refrescarListaYResumen() {
  renderizarLista(refs.listaAlumnos, estado.manifest, estado.filtro, estado.usuarioActivo, seleccionarAlumno, estado.listado);
  renderizarResumen(refs.resumenGeneral, estado.manifest);
}

// ---------------- Navegacion entre vistas ----------------

function mostrarVista(nombre) {
  estado.vista = nombre;
  refs.vacioInicial.classList.toggle("oculto", nombre !== "inicial");
  refs.vistaContacto.classList.toggle("oculto", nombre !== "contacto");
  refs.vistaComparador.classList.toggle("oculto", nombre !== "comparador");
}

function seleccionarAlumno(usuario) {
  estado.usuarioActivo = usuario;
  const alumno = estado.manifest.alumnos.find((a) => a.usuario === usuario);
  const disponibles = paginasDeAlumno(alumno);
  // Siempre se prefiere una pagina que corresponda a la parte activa en el
  // selector global. Si el alumno no entrego nada de esa parte, NO se salta
  // a otra pagina disponible (eso mostraria contenido de otra parte con el
  // selector marcando la parte equivocada, la misma ambiguedad que causo el
  // problema de esta tarea): se deja `paginaActiva` en el propio id de la
  // parte, que no calza con ninguna pagina real y hace que la grilla
  // muestre "sin datos" -- consistente con el aviso de las tabs de arriba
  // ("el alumno no tiene ninguna hoja guardada como Parte X").
  const deLaParte = disponibles.find((p) => tipoBasePagina(p) === estado.parteActiva);
  estado.paginaActiva = deLaParte || estado.parteActiva;
  mostrarContacto();
}

function mostrarContacto() {
  mostrarVista("contacto");
  const alumno = alumnoActivo();
  renderizarContacto(refs, estado.manifest, alumno, estado.paginaActiva, estado.parteActiva, {
    base: estado.base,
    onCambiarPagina: (pagina) => {
      estado.paginaActiva = pagina;
      mostrarContacto();
    },
    onAbrirCuadro: (pagina, n) => {
      estado.paginaActiva = pagina;
      abrirComparador(n);
    },
  });
  actualizarBotonMoverParte();
  refrescarListaYResumen();
}

/**
 * El boton "Mover esta hoja a la otra parte" solo tiene sentido si el
 * alumno realmente entrego la pagina activa (si no hay nada guardado, no
 * hay archivos que mover). Se etiqueta con la parte destino real para que
 * quede explicito hacia donde se movera antes de pedir confirmacion.
 */
function actualizarBotonMoverParte() {
  const alumno = alumnoActivo();
  const pg = alumno && alumno.paginas && alumno.paginas.find((p) => p.pagina === estado.paginaActiva);
  if (!pg) {
    refs.btnMoverParte.classList.add("oculto");
    return;
  }
  const tipoActual = tipoBasePagina(estado.paginaActiva) || estado.parteActiva;
  const destino = otraParte(tipoActual);
  refs.btnMoverParte.textContent = `Mover esta hoja a ${etiquetaParte(destino)}`;
  refs.btnMoverParte.dataset.destino = destino;
  refs.btnMoverParte.classList.remove("oculto");
}

async function moverHojaActivaAOtraParte() {
  const usuario = estado.usuarioActivo;
  const paginaOrigen = estado.paginaActiva;
  const destino = refs.btnMoverParte.dataset.destino;
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
    const resultado = await moverParte(usuario, paginaOrigen, destino);
    estado.manifest = await cargarManifest(estado.base);
    try {
      estado.listado = await obtenerListado();
    } catch (err) {
      estado.listado = null;
    }
    limpiarCache();
    estado.paginaActiva = (resultado && resultado.pagina_destino) || destino;
    // La hoja recien movida queda registrada bajo "destino": el selector
    // global de parte tambien se cambia para que quede consistente con lo
    // que se acaba de mover. Sin esto, el selector se quedaba mostrando la
    // parte de origen mientras la grilla ya mostraba la hoja movida (sin
    // ninguna pestana activa): la misma ambiguedad de etiquetado que este
    // boton existe para resolver, pero ahora causada por la propia UI.
    estado.parteActiva = destino;
    if (selectorParte) selectorParte.fijar(destino);
    mostrarContacto();
  } catch (err) {
    alert("No se pudo mover la hoja: " + err.message);
    // Solo se restaura el texto original si la operacion fallo: si tuvo
    // exito, mostrarContacto() -> actualizarBotonMoverParte() ya dejo el
    // boton con el texto/destino correctos para el nuevo estado, y
    // pisarlos aqui con el texto de ANTES de mover volvia a mostrar
    // "Mover a Parte X" con el destino equivocado (ver REVISION_PARTES.md).
    refs.btnMoverParte.textContent = original;
  } finally {
    refs.btnMoverParte.disabled = false;
  }
}

function alumnoActivo() {
  return estado.manifest.alumnos.find((a) => a.usuario === estado.usuarioActivo);
}

async function abrirComparador(n) {
  estado.cuadroActivo = n;
  mostrarVista("comparador");
  await cargarCuadroActual();
}

async function cargarCuadroActual() {
  const alumno = alumnoActivo();
  refs.compUsuario.textContent = alumno.usuario;
  refs.compCuadroInfo.textContent = `${etiquetaPagina(estado.paginaActiva)} · cuadro ${estado.cuadroActivo} de 6`;
  refs.compNavIndicador.textContent = `${estado.cuadroActivo} / 6`;

  await comparador.cargar({
    manifest: estado.manifest,
    alumno,
    pagina: estado.paginaActiva,
    n: estado.cuadroActivo,
    base: estado.base,
  });

  actualizarControlesDesdeAjuste();
  redibujarComparador();
  cargarVeredictoEnUI();
}

function redibujarComparador() {
  const ajuste = obtenerAjuste(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
  comparador.redibujar(estado.globales, ajuste);
}

function actualizarControlesDesdeAjuste() {
  const a = obtenerAjuste(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
  refs.ajusteInfo.textContent = `dx=${a.dx} dy=${a.dy} escala=${a.escala.toFixed(2)} rot=${a.rotacion}°`;
}

function cargarVeredictoEnUI() {
  const cal = almacen.obtener(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
  document.querySelectorAll(".veredicto-btn").forEach((b) => {
    b.classList.toggle("activo", !!cal && cal.veredicto === b.dataset.veredicto);
  });
  refs.comentario.value = cal && cal.comentario ? cal.comentario : "";
  refs.veredictoEstado.textContent = cal && cal.fecha ? `Guardado: ${new Date(cal.fecha).toLocaleString()}` : "Sin calificar";
}

function volverAContacto() {
  mostrarContacto();
}

// ---------------- Navegacion de cuadros ----------------

function irACuadro(n) {
  if (n < 1) n = 6;
  if (n > 6) n = 1;
  estado.cuadroActivo = n;
  cargarCuadroActual();
}

function siguienteCuadro() {
  irACuadro(estado.cuadroActivo + 1);
}
function anteriorCuadro() {
  irACuadro(estado.cuadroActivo - 1);
}

// ---------------- Veredictos ----------------

function calificar(veredicto) {
  const comentario = refs.comentario.value;
  almacen.guardar(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo, {
    veredicto,
    comentario,
  });
  cargarVeredictoEnUI();
  refrescarListaYResumen();
  // Avance automatico: si no era el ultimo cuadro, sigue; si era el 6, vuelve
  // a la vista de contacto para ver el resumen de la pagina.
  if (estado.cuadroActivo < 6) {
    setTimeout(() => siguienteCuadro(), 120);
  } else {
    setTimeout(() => volverAContacto(), 250);
  }
}

let temporizadorComentario = null;
function guardarComentarioDebounced() {
  clearTimeout(temporizadorComentario);
  temporizadorComentario = setTimeout(() => {
    const cal = almacen.obtener(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
    almacen.guardar(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo, {
      veredicto: cal ? cal.veredicto : null,
      comentario: refs.comentario.value,
    });
    refrescarListaYResumen();
  }, 500);
}

// ---------------- Controles de trazo / ajuste fino ----------------

function actualizarGlobalesYRedibujar() {
  estado.globales.opacidad = Number(refs.ctlOpacidad.value) / 100;
  estado.globales.grosorAlumno = Number(refs.ctlGrosorAlumno.value);
  estado.globales.grosorPauta = Number(refs.ctlGrosorPauta.value);
  estado.globales.umbral = Number(refs.ctlUmbral.value);
  estado.globales.mostrarFondo = refs.ctlFondo.checked;
  estado.globales.invertir = refs.ctlInvertir.checked;

  refs.outOpacidad.textContent = `${Math.round(estado.globales.opacidad * 100)}%`;
  refs.outGrosorAlumno.textContent = `${estado.globales.grosorAlumno} px`;
  refs.outGrosorPauta.textContent = `${estado.globales.grosorPauta} px`;
  refs.outUmbral.textContent = `${estado.globales.umbral}`;

  redibujarComparador();
}

function rotar(delta) {
  const a = obtenerAjuste(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
  a.rotacion = ((a.rotacion + delta) % 360 + 360) % 360;
  actualizarControlesDesdeAjuste();
  redibujarComparador();
}

function moverAjuste(dx, dy) {
  const a = obtenerAjuste(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
  a.dx += dx;
  a.dy += dy;
  actualizarControlesDesdeAjuste();
  redibujarComparador();
}

function escalarAjuste(delta) {
  const a = obtenerAjuste(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo);
  a.escala = Math.max(0.5, Math.min(2, a.escala + delta));
  actualizarControlesDesdeAjuste();
  redibujarComparador();
}

function reiniciarAjuste() {
  estado.ajustes.set(claveAjuste(estado.usuarioActivo, estado.paginaActiva, estado.cuadroActivo), {
    dx: 0,
    dy: 0,
    escala: 1,
    rotacion: 0,
  });
  actualizarControlesDesdeAjuste();
  redibujarComparador();
}

// ---------------- Eventos ----------------

const TIPOS_INPUT_TEXTO = new Set(["text", "search", "email", "number", "url", "tel", "password"]);

function elFocoEsTexto() {
  const el = document.activeElement;
  if (!el) return false;
  if (el.tagName === "TEXTAREA") return true;
  if (el.tagName === "INPUT") return TIPOS_INPUT_TEXTO.has(el.type);
  return false;
}

function instalarEventos() {
  refs.buscador.addEventListener("input", () => {
    estado.filtro = refs.buscador.value;
    refrescarListaYResumen();
  });

  refs.btnRecargarDatos.addEventListener("click", recargarDatos);

  refs.btnVolver.addEventListener("click", volverAContacto);
  refs.btnMoverParte.addEventListener("click", moverHojaActivaAOtraParte);
  refs.btnCuadroPrev.addEventListener("click", anteriorCuadro);
  refs.btnCuadroNext.addEventListener("click", siguienteCuadro);

  ["1", "2", "3", "4"].forEach((m) => {
    refs[`modoBtn${m}`].addEventListener("click", () => activarModo(m));
  });

  document.querySelectorAll(".veredicto-btn").forEach((b) => {
    b.addEventListener("click", () => calificar(b.dataset.veredicto));
  });

  refs.comentario.addEventListener("input", guardarComentarioDebounced);

  [refs.ctlOpacidad, refs.ctlGrosorAlumno, refs.ctlGrosorPauta, refs.ctlUmbral].forEach((el) => {
    el.addEventListener("input", actualizarGlobalesYRedibujar);
  });
  refs.ctlFondo.addEventListener("change", actualizarGlobalesYRedibujar);
  refs.ctlInvertir.addEventListener("change", actualizarGlobalesYRedibujar);

  refs.btnRotarIzq.addEventListener("click", () => rotar(-90));
  refs.btnRotarDer.addEventListener("click", () => rotar(90));
  refs.btnResetAjuste.addEventListener("click", reiniciarAjuste);

  refs.btnExportarCSV.addEventListener("click", () => almacen.exportarCSV(estado.manifest));
  refs.btnExportarJSON.addEventListener("click", () => almacen.exportarJSON());
  refs.btnImportarJSON.addEventListener("click", () => refs.inputImportar.click());
  refs.inputImportar.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const texto = await file.text();
      almacen.importarJSON(JSON.parse(texto));
      refrescarListaYResumen();
      if (estado.vista === "comparador") cargarVeredictoEnUI();
      if (estado.vista === "contacto") mostrarContacto();
      refs.veredictoEstado.textContent = "Importacion completada.";
    } catch (err) {
      alert("No se pudo importar el archivo: " + err.message);
    }
    refs.inputImportar.value = "";
  });

  refs.ayudaToggle.addEventListener("click", () => {
    const plegado = refs.ayudaContenido.classList.toggle("plegado");
    refs.ayudaToggle.textContent = "Atajos de teclado " + (plegado ? "▲" : "▼");
  });

  window.addEventListener("keydown", manejarTeclado);
}

function activarModo(modo) {
  document.querySelectorAll(".modo-btn").forEach((b) => b.classList.toggle("activo", b.dataset.modo === modo));
  comparador.setModo(modo);
}

function manejarTeclado(e) {
  if (elFocoEsTexto() && e.key !== "Escape") return;

  if (estado.vista === "comparador") {
    if (["1", "2", "3", "4"].includes(e.key)) {
      activarModo(e.key);
      e.preventDefault();
      return;
    }
    switch (e.key) {
      case "a":
        calificar("correcto");
        break;
      case "s":
        calificar("parcial");
        break;
      case "d":
        calificar("incorrecto");
        break;
      case "n":
        siguienteCuadro();
        e.preventDefault();
        break;
      case "p":
        anteriorCuadro();
        e.preventDefault();
        break;
      case "ArrowRight":
        if (e.altKey) {
          moverAjuste(e.shiftKey ? 10 : 2, 0);
        } else {
          siguienteCuadro();
        }
        e.preventDefault();
        break;
      case "ArrowLeft":
        if (e.altKey) {
          moverAjuste(e.shiftKey ? -10 : -2, 0);
        } else {
          anteriorCuadro();
        }
        e.preventDefault();
        break;
      case "ArrowUp":
        moverAjuste(0, e.shiftKey ? -10 : -2);
        e.preventDefault();
        break;
      case "ArrowDown":
        moverAjuste(0, e.shiftKey ? 10 : 2);
        e.preventDefault();
        break;
      case "+":
      case "=":
        escalarAjuste(0.02);
        e.preventDefault();
        break;
      case "-":
        escalarAjuste(-0.02);
        e.preventDefault();
        break;
      case "0":
        reiniciarAjuste();
        e.preventDefault();
        break;
      case "r":
        rotar(90);
        break;
      case "Escape":
        volverAContacto();
        break;
    }
  } else if (e.key === "Escape") {
    // sin efecto fuera del comparador
  }
}

iniciar();
