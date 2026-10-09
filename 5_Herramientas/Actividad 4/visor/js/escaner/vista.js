// vista.js - transformacion (zoom/desplazamiento) entre coordenadas de
// pantalla (pixeles del canvas visible) y coordenadas de la imagen cargada
// (pixeles naturales de la foto). Funciones puras, sin DOM.

/** Crea una transformacion que encuadra una imagen de anchoImg x altoImg
 * dentro de un area de anchoArea x altoArea, centrada, con un margen. */
export function ajustarVista(anchoImg, altoImg, anchoArea, altoArea, margen = 20) {
  const escala = Math.min(
    (anchoArea - margen * 2) / anchoImg,
    (altoArea - margen * 2) / altoImg
  );
  const escalaFinal = escala > 0 ? escala : 1;
  const offsetX = (anchoArea - anchoImg * escalaFinal) / 2;
  const offsetY = (altoArea - altoImg * escalaFinal) / 2;
  return { escala: escalaFinal, offsetX, offsetY };
}

export function imagenAPantalla(vista, x, y) {
  return [vista.offsetX + x * vista.escala, vista.offsetY + y * vista.escala];
}

export function pantallaAImagen(vista, x, y) {
  return [(x - vista.offsetX) / vista.escala, (y - vista.offsetY) / vista.escala];
}

/** Devuelve una nueva vista con zoom aplicado centrado en (cxPantalla,
 * cyPantalla), multiplicando la escala actual por `factor` (recortado a
 * [escalaMin, escalaMax]). */
export function aplicarZoom(vista, factor, cxPantalla, cyPantalla, escalaMin = 0.05, escalaMax = 40) {
  const nuevaEscala = Math.max(escalaMin, Math.min(escalaMax, vista.escala * factor));
  const factorReal = nuevaEscala / vista.escala;
  // El punto de la imagen bajo el cursor debe quedar fijo en pantalla.
  const offsetX = cxPantalla - (cxPantalla - vista.offsetX) * factorReal;
  const offsetY = cyPantalla - (cyPantalla - vista.offsetY) * factorReal;
  return { escala: nuevaEscala, offsetX, offsetY };
}

export function desplazar(vista, dx, dy) {
  return { ...vista, offsetX: vista.offsetX + dx, offsetY: vista.offsetY + dy };
}
