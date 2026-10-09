// dialogo.js - dialogo de confirmacion modal minimo, sin dependencias
// externas. Se usa para toda accion que pueda sorprender al usuario si se
// dispara sin querer: mover una hoja a la otra parte (mueve archivos en el
// servidor) o guardar una hoja cuando el servidor detecto un tipo distinto
// al elegido.

/**
 * Muestra un dialogo modal y devuelve una Promise<boolean>: true si se
 * confirma (click en el boton de confirmar o Enter), false si se cancela
 * (click en cancelar, click afuera, o Escape).
 *
 * options: { titulo, mensaje, textoConfirmar, textoCancelar, claseConfirmar }
 * `mensaje` puede traer saltos de linea (\n): se respetan.
 */
export function confirmar(options) {
  const {
    titulo = "",
    mensaje = "",
    textoConfirmar = "Confirmar",
    textoCancelar = "Cancelar",
    claseConfirmar = "boton-primario",
  } = options || {};

  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "dialogo-overlay";

    const caja = document.createElement("div");
    caja.className = "dialogo-caja";
    caja.setAttribute("role", "alertdialog");
    caja.setAttribute("aria-modal", "true");

    if (titulo) {
      const h = document.createElement("h3");
      h.className = "dialogo-titulo";
      h.textContent = titulo;
      caja.appendChild(h);
    }

    const p = document.createElement("p");
    p.className = "dialogo-mensaje";
    p.textContent = mensaje;
    caja.appendChild(p);

    const botonera = document.createElement("div");
    botonera.className = "dialogo-botones";

    const btnCancelar = document.createElement("button");
    btnCancelar.type = "button";
    btnCancelar.className = "boton";
    btnCancelar.textContent = textoCancelar;

    const btnConfirmar = document.createElement("button");
    btnConfirmar.type = "button";
    btnConfirmar.className = "boton " + claseConfirmar;
    btnConfirmar.textContent = textoConfirmar;

    botonera.appendChild(btnCancelar);
    botonera.appendChild(btnConfirmar);
    caja.appendChild(botonera);
    overlay.appendChild(caja);
    document.body.appendChild(overlay);

    function cerrar(valor) {
      document.removeEventListener("keydown", onKeydown);
      overlay.remove();
      resolve(valor);
    }
    function onKeydown(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        cerrar(false);
      } else if (e.key === "Enter") {
        e.preventDefault();
        cerrar(true);
      }
    }

    btnCancelar.addEventListener("click", () => cerrar(false));
    btnConfirmar.addEventListener("click", () => cerrar(true));
    overlay.addEventListener("mousedown", (e) => {
      if (e.target === overlay) cerrar(false);
    });
    document.addEventListener("keydown", onKeydown);
    btnConfirmar.focus();
  });
}
