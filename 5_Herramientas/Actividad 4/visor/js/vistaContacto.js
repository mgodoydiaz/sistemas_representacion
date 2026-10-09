// vistaContacto.js - grilla 2x3 con los cuadros de una pagina del alumno.

import { cargarImagen, procesarTrazo, dibujarFondo, dibujarTransformado } from "./imagenes.js";
import {
  paginaAlumno,
  celdaAlumno,
  rutaCompleta,
  metodoEsFallido,
  metodoEsFallback,
  metodoEsCuadroSuelto,
  etiquetaPagina,
  paginasDeAlumno,
  tipoBasePagina,
} from "./datos.js";
import { obtener } from "./almacen.js";
import { etiquetaParte } from "./partes.js";

async function dibujarMiniatura(canvas, base, celda, tamano) {
  canvas.width = tamano;
  canvas.height = tamano;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, tamano, tamano);

  if (!celda || celda.vacio) {
    ctx.fillStyle = "#eceeef";
    ctx.fillRect(0, 0, tamano, tamano);
    return;
  }

  const [imgFondo, imgTrazo] = await Promise.all([
    cargarImagen(rutaCompleta(base, celda.img)),
    cargarImagen(rutaCompleta(base, celda.trazo)),
  ]);

  const off = document.createElement("canvas");
  off.width = 1000;
  off.height = 1000;
  const octx = off.getContext("2d");
  dibujarFondo(octx, imgFondo);
  if (imgTrazo) {
    const capa = procesarTrazo(imgTrazo, { grosor: 1, umbral: 12, tinte: [20, 20, 20] });
    dibujarTransformado(octx, capa, {});
  }
  ctx.drawImage(off, 0, 0, tamano, tamano);
}

/**
 * Renderiza la vista de contacto (encabezado + tabs de pagina + grilla).
 * `callbacks.onAbrirCuadro(pagina, n)` se llama al hacer click en un cuadro.
 * `callbacks.onCambiarPagina(pagina)` al cambiar de tab.
 */
export async function renderizarContacto(refs, manifest, alumno, paginaActual, parteActiva, callbacks) {
  const base = callbacks.base;
  refs.contactoUsuario.textContent = alumno.usuario;

  // Tabs de pagina: una por cada pagina del alumno que corresponda a la
  // parte activa en el selector global (vistas/isometricos, y sus variantes
  // vistas_2/isometricos_2 cuando fotografio mas de una hoja del mismo
  // tipo). Las paginas "desconocida_N" (tipo no reconocible) se muestran
  // siempre, sin importar la parte activa, porque todavia no se sabe a cual
  // de las dos corresponden -- ocultarlas las haria invisibles para
  // siempre. El selector global filtra asi todo lo que se ve debajo: si el
  // alumno entrego una hoja mal etiquetada (por ejemplo isometricos
  // guardado como "vistas"), aparecera bajo Parte 1 en vez de Parte 2, que
  // es justo la senal de que hay que reetiquetarla con el boton de al lado.
  const todasLasPaginas = paginasDeAlumno(alumno);
  const paginasPosibles = todasLasPaginas.filter((pag) => {
    const tipo = tipoBasePagina(pag);
    return tipo === null || tipo === parteActiva;
  });
  refs.contactoTabs.innerHTML = "";
  if (todasLasPaginas.length === 0) {
    const aviso = document.createElement("span");
    aviso.className = "aviso-pill fallo";
    aviso.textContent = "El alumno no entrego ninguna pagina reconocible.";
    refs.contactoTabs.appendChild(aviso);
  } else if (paginasPosibles.length === 0) {
    const aviso = document.createElement("span");
    aviso.className = "aviso-pill fallo";
    aviso.textContent = `El alumno no tiene ninguna hoja guardada como ${etiquetaParte(parteActiva)}.`;
    refs.contactoTabs.appendChild(aviso);
  }
  paginasPosibles.forEach((pag) => {
    const btn = document.createElement("button");
    btn.textContent = etiquetaPagina(pag);
    if (pag === paginaActual) btn.classList.add("activo");
    btn.addEventListener("click", () => callbacks.onCambiarPagina(pag));
    refs.contactoTabs.appendChild(btn);
  });

  const pg = paginaAlumno(alumno, paginaActual);

  // Avisos de la pagina (metodo fallido/fallback, avisos propios del manifest).
  refs.contactoAvisos.innerHTML = "";
  if (!pg) {
    const pill = document.createElement("span");
    pill.className = "aviso-pill fallo";
    pill.textContent = `El alumno no entrego la pagina "${paginaActual}".`;
    refs.contactoAvisos.appendChild(pill);
  } else {
    if (metodoEsFallido(pg.metodo)) {
      const pill = document.createElement("span");
      pill.className = "aviso-pill fallo";
      pill.textContent = "Metodo de recorte FALLIDO: revisar el original manualmente.";
      refs.contactoAvisos.appendChild(pill);
    } else if (metodoEsFallback(pg.metodo)) {
      const pill = document.createElement("span");
      pill.className = "aviso-pill";
      pill.textContent = "Metodo de recorte: fallback (menor confianza).";
      refs.contactoAvisos.appendChild(pill);
    }
    if (metodoEsCuadroSuelto(pg.metodo)) {
      const pill = document.createElement("span");
      pill.className = "aviso-pill";
      pill.textContent =
        "La foto es un unico cuadro suelto (no la lamina completa): se muestra en el casillero #1, pero no se sabe a que ejercicio de la pauta corresponde. Revisar manualmente.";
      refs.contactoAvisos.appendChild(pill);
    }
    const confianza = typeof pg.confianza === "number" ? pg.confianza : null;
    if (confianza !== null && confianza < 0.7) {
      const pill = document.createElement("span");
      pill.className = "aviso-pill";
      pill.textContent = `Confianza baja: ${(confianza * 100).toFixed(0)}%`;
      refs.contactoAvisos.appendChild(pill);
    }
    (pg.avisos || []).forEach((a) => {
      const pill = document.createElement("span");
      pill.className = "aviso-pill";
      pill.textContent = a;
      refs.contactoAvisos.appendChild(pill);
    });
  }

  // Grilla de 6 cuadros. El tamaño de las miniaturas se calcula a partir
  // del ancho disponible (3 columnas) para que se vean nitidas sin dejar
  // bordes en blanco por dentro de cada celda.
  refs.contactoGrilla.innerHTML = "";
  const anchoDisponible = refs.contactoGrilla.clientWidth || 900;
  const tamanoMiniatura = Math.max(160, Math.min(480, Math.floor((anchoDisponible - 24) / 3)));
  for (let n = 1; n <= 6; n++) {
    const celda = pg ? celdaAlumno(alumno, paginaActual, n) : null;
    const div = document.createElement("div");
    div.className = "cuadro-celda" + (celda && celda.vacio ? " vacio" : "");

    const numero = document.createElement("span");
    numero.className = "cuadro-numero";
    numero.textContent = `#${n}`;
    div.appendChild(numero);

    if (!pg) {
      const msg = document.createElement("span");
      msg.style.color = "#8a919b";
      msg.style.fontSize = "12px";
      msg.textContent = "sin datos";
      div.appendChild(msg);
    } else {
      const canvas = document.createElement("canvas");
      div.appendChild(canvas);
      dibujarMiniatura(canvas, base, celda, tamanoMiniatura);

      if (celda && celda.vacio) {
        const aviso = document.createElement("span");
        aviso.className = "cuadro-aviso-mini";
        aviso.textContent = "vacio";
        div.appendChild(aviso);
      }

      const cal = obtener(alumno.usuario, paginaActual, n);
      if (cal && cal.veredicto) {
        const badge = document.createElement("span");
        badge.className = "cuadro-veredicto-badge " + cal.veredicto;
        badge.textContent = cal.veredicto;
        div.appendChild(badge);
      }

      div.addEventListener("click", () => callbacks.onAbrirCuadro(paginaActual, n));
    }

    refs.contactoGrilla.appendChild(div);
  }
}
