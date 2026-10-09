/* Lógica del visor: arma el selector a partir de NIVELES (datos.js),
   muestra la imagen elegida a la derecha y permite navegar con teclado. */

(function () {
  "use strict";

  const CLAVE_GUARDADA = "visorPauta2.ultimaSeleccion";

  const elSelector = document.getElementById("selector");
  const elImagen = document.getElementById("imagen-pauta");
  const elContenedorImagen = document.getElementById("visor-imagen");
  const elEtiquetaNivel = document.getElementById("etiqueta-nivel");
  const elEtiquetaNumero = document.getElementById("etiqueta-numero");

  let seleccionActual = null; // { indiceNivel, numero }

  function idBoton(indiceNivel, numero) {
    return `pieza-${indiceNivel}-${numero}`;
  }

  function construirSelector() {
    NIVELES.forEach((nivel, indiceNivel) => {
      const grupo = document.createElement("section");
      grupo.className = "grupo-nivel";

      const titulo = document.createElement("h2");
      titulo.textContent = nivel.nombre;
      grupo.appendChild(titulo);

      const grilla = document.createElement("div");
      grilla.className = "grid-botones";

      for (let numero = 1; numero <= nivel.cantidad; numero++) {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "boton-pieza";
        boton.id = idBoton(indiceNivel, numero);
        boton.textContent = String(numero);
        boton.setAttribute("aria-pressed", "false");
        boton.setAttribute("aria-label", `${nivel.nombre}, ejercicio ${numero}`);
        boton.addEventListener("click", () => seleccionar(indiceNivel, numero));
        grilla.appendChild(boton);
      }

      grupo.appendChild(grilla);
      elSelector.appendChild(grupo);
    });
  }

  function seleccionar(indiceNivel, numero) {
    const nivel = NIVELES[indiceNivel];
    if (!nivel || numero < 1 || numero > nivel.cantidad) return;

    if (seleccionActual) {
      const anterior = document.getElementById(idBoton(seleccionActual.indiceNivel, seleccionActual.numero));
      if (anterior) {
        anterior.classList.remove("activo");
        anterior.setAttribute("aria-pressed", "false");
      }
    }

    const boton = document.getElementById(idBoton(indiceNivel, numero));
    if (boton) {
      boton.classList.add("activo");
      boton.setAttribute("aria-pressed", "true");
      boton.scrollIntoView({ block: "nearest" });
    }

    seleccionActual = { indiceNivel, numero };

    elImagen.src = rutaImagen(nivel.clave, numero);
    elImagen.alt = `Pauta ${nivel.nombre}, ejercicio ${numero}`;
    elImagen.classList.add("visible");
    elContenedorImagen.classList.add("con-imagen");

    elEtiquetaNivel.textContent = nivel.nombre;
    elEtiquetaNumero.textContent = `· Ejercicio ${numero}`;

    guardarSeleccion();
  }

  function guardarSeleccion() {
    try {
      if (seleccionActual) {
        localStorage.setItem(CLAVE_GUARDADA, JSON.stringify(seleccionActual));
      }
    } catch (e) {
      /* almacenamiento no disponible: no es grave, simplemente no se recuerda */
    }
  }

  function recuperarSeleccion() {
    try {
      const guardado = localStorage.getItem(CLAVE_GUARDADA);
      if (!guardado) return null;
      const datos = JSON.parse(guardado);
      if (
        datos &&
        Number.isInteger(datos.indiceNivel) &&
        Number.isInteger(datos.numero) &&
        NIVELES[datos.indiceNivel]
      ) {
        return datos;
      }
    } catch (e) {
      /* ignorar */
    }
    return null;
  }

  function moverHorizontal(delta) {
    if (!seleccionActual) {
      seleccionar(0, 1);
      return;
    }
    const nivel = NIVELES[seleccionActual.indiceNivel];
    let nuevoNumero = seleccionActual.numero + delta;
    if (nuevoNumero < 1) nuevoNumero = 1;
    if (nuevoNumero > nivel.cantidad) nuevoNumero = nivel.cantidad;
    seleccionar(seleccionActual.indiceNivel, nuevoNumero);
  }

  function moverVertical(delta) {
    if (!seleccionActual) {
      seleccionar(0, 1);
      return;
    }
    let nuevoIndice = seleccionActual.indiceNivel + delta;
    if (nuevoIndice < 0 || nuevoIndice >= NIVELES.length) return;
    const nuevoNivel = NIVELES[nuevoIndice];
    const numero = Math.min(seleccionActual.numero, nuevoNivel.cantidad);
    seleccionar(nuevoIndice, numero);
  }

  document.addEventListener("keydown", (evento) => {
    switch (evento.key) {
      case "ArrowRight":
        moverHorizontal(1);
        evento.preventDefault();
        break;
      case "ArrowLeft":
        moverHorizontal(-1);
        evento.preventDefault();
        break;
      case "ArrowDown":
        moverVertical(1);
        evento.preventDefault();
        break;
      case "ArrowUp":
        moverVertical(-1);
        evento.preventDefault();
        break;
    }
  });

  construirSelector();

  const previa = recuperarSeleccion();
  if (previa) {
    seleccionar(previa.indiceNivel, previa.numero);
  }
})();
