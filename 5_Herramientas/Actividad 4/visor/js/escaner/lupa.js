// lupa.js - dibuja la lupa de aumento (zoom al colocar/arrastrar un punto)
// sobre un canvas flotante, a partir de la imagen fuente completa.

/**
 * Dibuja en `canvasLupa` un recorte ampliado de `fuente` (un canvas o
 * imagen que contiene la foto completa a resolucion natural) centrado en
 * el punto de imagen (imgX, imgY), con cruz de mira. `zoom` es el factor de
 * aumento (pixeles de pantalla por pixel de imagen).
 */
export function dibujarLupa(canvasLupa, fuente, imgX, imgY, zoom = 6) {
  const tam = canvasLupa.width; // se asume canvas cuadrado
  const ctx = canvasLupa.getContext("2d");
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, tam, tam);

  const lado = tam / zoom;
  const sx = imgX - lado / 2;
  const sy = imgY - lado / 2;

  ctx.fillStyle = "#20242a";
  ctx.fillRect(0, 0, tam, tam);
  ctx.drawImage(fuente, sx, sy, lado, lado, 0, 0, tam, tam);

  // Cruz de mira en el centro (el punto exacto que se esta marcando).
  ctx.strokeStyle = "rgba(255,60,60,.9)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(tam / 2, 0);
  ctx.lineTo(tam / 2, tam);
  ctx.moveTo(0, tam / 2);
  ctx.lineTo(tam, tam / 2);
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,.85)";
  ctx.beginPath();
  ctx.arc(tam / 2, tam / 2, 5, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = "#000";
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, tam - 2, tam - 2);
  ctx.restore();
}

/** Posiciona el elemento flotante de la lupa cerca del cursor, evitando
 * que quede tapado por el propio cursor y sin salirse del contenedor. */
export function posicionarLupa(elLupa, contenedor, clientX, clientY) {
  const rectCont = contenedor.getBoundingClientRect();
  const tam = elLupa.offsetWidth || 180;
  const desplazamiento = 26;
  let x = clientX - rectCont.left + desplazamiento;
  let y = clientY - rectCont.top - tam - desplazamiento;
  if (y < 4) y = clientY - rectCont.top + desplazamiento;
  if (x + tam > rectCont.width - 4) x = clientX - rectCont.left - tam - desplazamiento;
  if (x < 4) x = 4;
  elLupa.style.left = `${x}px`;
  elLupa.style.top = `${y}px`;
}
