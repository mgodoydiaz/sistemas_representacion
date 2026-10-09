// comparador.js - logica de los 4 modos de comparacion (superposicion,
// lado a lado, cortina, diferencia) y de los controles de trazo/ajuste.

import { cargarImagen, procesarTrazo, dibujarFondo, dibujarTransformado, calcularDiferencia } from "./imagenes.js";
import {
  rutaCompleta,
  celdaPauta,
  celdaAlumno,
  paginaAlumno,
  metodoEsFallido,
  metodoEsFallback,
  metodoEsCuadroSuelto,
} from "./datos.js";

const COLOR_PAUTA = [50, 100, 200];   // azul
const COLOR_ALUMNO = [200, 55, 50];   // rojo

export class Comparador {
  constructor(refs) {
    this.refs = refs;
    this.modo = "1";
    this.panzoom = { scale: 1, tx: 0, ty: 0 };
    this.cortinaPct = 50;
    this._arrastrandoPan = false;
    this._arrastrandoCortina = false;
    this._ultimoMouse = null;

    this._contextos = {
      superpos: refs.canvasSuperpos.getContext("2d"),
      ladoPauta: refs.canvasLadoPauta.getContext("2d"),
      ladoAlumno: refs.canvasLadoAlumno.getContext("2d"),
      cortinaPauta: refs.canvasCortinaPauta.getContext("2d"),
      cortinaAlumno: refs.canvasCortinaAlumno.getContext("2d"),
      diferencia: refs.canvasDiferencia.getContext("2d"),
    };

    this._instalarInteracciones();
  }

  /** Carga las 4 imagenes (fondo/trazo x pauta/alumno) del cuadro indicado. */
  async cargar({ manifest, alumno, pagina, n, base }) {
    this.base = base;
    this.manifest = manifest;
    this.alumno = alumno;
    this.pagina = pagina;
    this.n = n;

    const pg = paginaAlumno(alumno, pagina);
    const cPauta = celdaPauta(manifest, pagina, n);
    const cAlumno = pg ? celdaAlumno(alumno, pagina, n) : null;

    this.faltaPauta = !cPauta;
    this.faltaPaginaAlumno = !pg;
    this.metodoPagina = pg ? pg.metodo : null;
    this.celdaVacia = !!(cAlumno && cAlumno.vacio);
    this.faltaCeldaAlumno = !!pg && !cAlumno;

    const [pautaFondo, pautaTrazo, alumnoFondo, alumnoTrazo] = await Promise.all([
      cargarImagen(cPauta ? rutaCompleta(base, cPauta.img) : null),
      cargarImagen(cPauta ? rutaCompleta(base, cPauta.trazo) : null),
      cargarImagen(cAlumno && !cAlumno.vacio ? rutaCompleta(base, cAlumno.img) : null),
      cargarImagen(cAlumno && !cAlumno.vacio ? rutaCompleta(base, cAlumno.trazo) : null),
    ]);

    this.pautaFondoImg = pautaFondo;
    this.pautaTrazoImg = pautaTrazo;
    this.alumnoFondoImg = alumnoFondo;
    this.alumnoTrazoImg = alumnoTrazo;

    // Reinicia estado visual dependiente del cuadro.
    this.panzoom = { scale: 1, tx: 0, ty: 0 };
    this.cortinaPct = 50;
    this._aplicarCortinaPct();
    this._dimensionarCortina();

    this._actualizarAviso();
  }

  _actualizarAviso() {
    const el = this.refs.avisoCuadro;
    el.classList.remove("fallo");
    let texto = null;
    if (this.faltaPaginaAlumno) {
      texto = `El alumno no entrego la pagina "${this.pagina}".`;
      el.classList.add("fallo");
    } else if (this.faltaPauta) {
      texto = `No hay pauta cargada para "${this.pagina}" cuadro ${this.n}.`;
      el.classList.add("fallo");
    } else if (metodoEsFallido(this.metodoPagina)) {
      texto = "Metodo de recorte FALLIDO para esta pagina: verificar manualmente.";
      el.classList.add("fallo");
    } else if (this.celdaVacia) {
      texto = "Este cuadro fue marcado como VACIO (sin trazo detectado).";
    } else if (metodoEsCuadroSuelto(this.metodoPagina) && this.n !== 1) {
      texto = "Esta pagina es un cuadro suelto: el unico dibujo del alumno se muestra en el cuadro 1.";
    } else if (metodoEsCuadroSuelto(this.metodoPagina)) {
      texto = "Cuadro suelto: no se sabe a cual ejercicio de la pauta corresponde. Compare contra cada cuadro de la pauta si es necesario.";
    } else if (metodoEsFallback(this.metodoPagina)) {
      texto = "Pagina procesada con metodo de respaldo (menor confianza).";
    }
    if (texto) {
      el.textContent = texto;
      el.classList.remove("oculto");
    } else {
      el.classList.add("oculto");
    }
  }

  /** Reprocesa las capas de trazo con las opciones globales + ajuste actuales
   * y vuelve a dibujar el modo activo. Se llama tras cualquier cambio de
   * control (grosor, umbral, invertir, rotacion, ajuste fino, opacidad). */
  redibujar(globales, ajuste) {
    this.globales = globales;
    this.ajuste = ajuste;

    const tamano = 1000;

    // Capa de trazo de la pauta (sin transformar, la pauta no se mueve).
    this.canvasPautaTrazo = this.pautaTrazoImg
      ? procesarTrazo(this.pautaTrazoImg, {
          grosor: globales.grosorPauta,
          umbral: globales.umbral,
          tinte: COLOR_PAUTA,
        })
      : this._canvasVacio(tamano);

    // Capa de trazo del alumno, procesada y luego transformada (rotacion,
    // desplazamiento y escala del ajuste fino).
    const trazoAlumnoBase = this.alumnoTrazoImg
      ? procesarTrazo(this.alumnoTrazoImg, {
          grosor: globales.grosorAlumno,
          umbral: globales.umbral,
          invertir: globales.invertir,
          tinte: COLOR_ALUMNO,
        })
      : this._canvasVacio(tamano);

    const destino = document.createElement("canvas");
    destino.width = tamano;
    destino.height = tamano;
    dibujarTransformado(destino.getContext("2d"), trazoAlumnoBase, ajuste);
    this.canvasAlumnoTrazo = destino;

    this._render();
  }

  _canvasVacio(tam) {
    const c = document.createElement("canvas");
    c.width = tam;
    c.height = tam;
    return c;
  }

  setModo(modo) {
    this.modo = modo;
    for (let i = 1; i <= 4; i++) {
      this.refs[`modo${i}`].classList.toggle("oculto", String(i) !== modo);
    }
    if (modo === "3") {
      // El contenedor puede no haber tenido tamaño mientras estaba oculto.
      requestAnimationFrame(() => this._dimensionarCortina());
    }
    this._render();
  }

  _render() {
    if (!this.canvasPautaTrazo) return;
    const g = this.globales || {};
    switch (this.modo) {
      case "1":
        this._renderSuperposicion(g);
        break;
      case "2":
        this._renderLadoALado(g);
        break;
      case "3":
        this._renderCortina(g);
        break;
      case "4":
        this._renderDiferencia(g);
        break;
    }
  }

  _renderSuperposicion(g) {
    const ctx = this._contextos.superpos;
    ctx.clearRect(0, 0, 1000, 1000);
    if (g.mostrarFondo) dibujarFondo(ctx, this.pautaFondoImg, 0.55);
    ctx.save();
    ctx.globalAlpha = 1;
    ctx.drawImage(this.canvasPautaTrazo, 0, 0);
    ctx.globalAlpha = Math.max(0, Math.min(1, g.opacidad));
    ctx.drawImage(this.canvasAlumnoTrazo, 0, 0);
    ctx.restore();
  }

  _renderLadoALado(g) {
    const cp = this._contextos.ladoPauta;
    const ca = this._contextos.ladoAlumno;
    cp.clearRect(0, 0, 1000, 1000);
    ca.clearRect(0, 0, 1000, 1000);
    if (g.mostrarFondo) {
      dibujarFondo(cp, this.pautaFondoImg);
      dibujarFondo(ca, this.alumnoFondoImg);
    } else {
      cp.fillStyle = "#e6e6e6";
      cp.fillRect(0, 0, 1000, 1000);
      ca.fillStyle = "#e6e6e6";
      ca.fillRect(0, 0, 1000, 1000);
    }
    cp.drawImage(this.canvasPautaTrazo, 0, 0);
    ca.drawImage(this.canvasAlumnoTrazo, 0, 0);
    this._aplicarPanZoom();
  }

  _renderCortina(g) {
    const cp = this._contextos.cortinaPauta;
    const ca = this._contextos.cortinaAlumno;
    cp.clearRect(0, 0, 1000, 1000);
    ca.clearRect(0, 0, 1000, 1000);
    if (g.mostrarFondo) {
      dibujarFondo(cp, this.pautaFondoImg);
      dibujarFondo(ca, this.alumnoFondoImg);
    } else {
      cp.fillStyle = "#e6e6e6";
      cp.fillRect(0, 0, 1000, 1000);
      ca.fillStyle = "#e6e6e6";
      ca.fillRect(0, 0, 1000, 1000);
    }
    cp.drawImage(this.canvasPautaTrazo, 0, 0);
    ca.drawImage(this.canvasAlumnoTrazo, 0, 0);
  }

  _renderDiferencia(g) {
    const ctx = this._contextos.diferencia;
    const diff = calcularDiferencia(this.canvasPautaTrazo, this.canvasAlumnoTrazo, {
      soloAlumno: COLOR_ALUMNO,
      soloPauta: COLOR_PAUTA,
    });
    ctx.clearRect(0, 0, 1000, 1000);
    if (g.mostrarFondo) dibujarFondo(ctx, this.pautaFondoImg, 0.3);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = g.mostrarFondo ? "multiply" : "source-over";
    ctx.drawImage(diff, 0, 0);
    ctx.globalCompositeOperation = "source-over";
  }

  // ---------------- Interacciones: pan/zoom (modo 2) y cortina (modo 3) ----------------

  _instalarInteracciones() {
    const viewports = [this.refs.viewportPauta, this.refs.viewportAlumno];
    viewports.forEach((vp) => {
      vp.addEventListener("wheel", (e) => this._onWheel(e), { passive: false });
      vp.addEventListener("mousedown", (e) => this._onPanStart(e));
    });
    window.addEventListener("mousemove", (e) => this._onPanMove(e));
    window.addEventListener("mouseup", () => this._onPanEnd());

    const barra = this.refs.cortinaBarra;
    const contenedor = this.refs.cortinaContenedor;
    barra.addEventListener("mousedown", (e) => {
      e.preventDefault();
      this._arrastrandoCortina = true;
    });
    window.addEventListener("mousemove", (e) => {
      if (!this._arrastrandoCortina) return;
      const rect = contenedor.getBoundingClientRect();
      let pct = ((e.clientX - rect.left) / rect.width) * 100;
      pct = Math.max(0, Math.min(100, pct));
      this.cortinaPct = pct;
      this._aplicarCortinaPct();
    });
    window.addEventListener("mouseup", () => {
      this._arrastrandoCortina = false;
    });
    window.addEventListener("resize", () => this._dimensionarCortina());
  }

  _aplicarCortinaPct() {
    this.refs.cortinaRecorte.style.width = `${this.cortinaPct}%`;
    this.refs.cortinaBarra.style.left = `${this.cortinaPct}%`;
  }

  /** El canvas del alumno dentro del recorte debe mantener el tamaño completo
   * del contenedor (no el del recorte, que es mas angosto) para que el
   * recorte "revele" en vez de estirar la imagen. */
  _dimensionarCortina() {
    const cont = this.refs.cortinaContenedor;
    const lienzo = cont.closest(".comparador-lienzo");
    const disponible = lienzo
      ? Math.max(200, Math.min(lienzo.clientWidth, lienzo.clientHeight) * 0.92)
      : 500;
    cont.style.width = `${disponible}px`;
    cont.style.height = `${disponible}px`;
    this.refs.canvasCortinaAlumno.style.width = `${disponible}px`;
    this.refs.canvasCortinaAlumno.style.height = `${disponible}px`;
  }

  _onWheel(e) {
    if (this.modo !== "2") return;
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
    const nuevo = Math.max(0.5, Math.min(8, this.panzoom.scale * factor));
    this.panzoom.scale = nuevo;
    this._aplicarPanZoom();
  }

  _onPanStart(e) {
    if (this.modo !== "2") return;
    this._arrastrandoPan = true;
    this._ultimoMouse = { x: e.clientX, y: e.clientY };
  }

  _onPanMove(e) {
    if (!this._arrastrandoPan) return;
    const dx = e.clientX - this._ultimoMouse.x;
    const dy = e.clientY - this._ultimoMouse.y;
    this._ultimoMouse = { x: e.clientX, y: e.clientY };
    this.panzoom.tx += dx;
    this.panzoom.ty += dy;
    this._aplicarPanZoom();
  }

  _onPanEnd() {
    this._arrastrandoPan = false;
  }

  _aplicarPanZoom() {
    const { scale, tx, ty } = this.panzoom;
    const t = `translate(${tx}px, ${ty}px) scale(${scale})`;
    this.refs.canvasLadoPauta.style.transform = t;
    this.refs.canvasLadoAlumno.style.transform = t;
  }
}
