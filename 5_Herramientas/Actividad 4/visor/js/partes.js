// partes.js - selector global de "parte" de la actividad, compartido por
// las tres paginas del visor (index.html, escaner.html, comparacion.html).
//
// La actividad tiene dos laminas que en la interfaz se llaman "Parte 1 ·
// Vistas" y "Parte 2 · Isometricos", pero el identificador interno (nombre
// de archivo, clave de pagina en el manifest, etc.) sigue siendo
// "vistas"/"isometricos" tal cual lo esperan servidor.py y el resto del
// pipeline: aca solo se traduce para mostrar, nunca para guardar.
//
// La eleccion de parte se recuerda en localStorage (misma clave en las tres
// paginas) para que sea consistente entre sesiones y entre paginas.

const CLAVE_PARTE = "visor_parte_activa_v1";

export const PARTES = [
  { id: "vistas", numero: 1, etiqueta: "Parte 1 · Vistas", etiquetaCorta: "Parte 1" },
  { id: "isometricos", numero: 2, etiqueta: "Parte 2 · Isometricos", etiquetaCorta: "Parte 2" },
];

export function infoParte(id) {
  return PARTES.find((p) => p.id === id) || null;
}

export function etiquetaParte(id) {
  const p = infoParte(id);
  return p ? p.etiqueta : id || "";
}

export function etiquetaParteCorta(id) {
  const p = infoParte(id);
  return p ? p.etiquetaCorta : id || "";
}

export function esParteValida(id) {
  return id === "vistas" || id === "isometricos";
}

export function otraParte(id) {
  return id === "vistas" ? "isometricos" : "vistas";
}

export function obtenerParteGuardada() {
  try {
    const v = window.localStorage.getItem(CLAVE_PARTE);
    if (esParteValida(v)) return v;
  } catch (err) {
    // localStorage no disponible: se sigue con el valor por defecto.
  }
  return "vistas";
}

export function guardarParteActiva(id) {
  if (!esParteValida(id)) return;
  try {
    window.localStorage.setItem(CLAVE_PARTE, id);
  } catch (err) {
    // Sin persistencia disponible (modo privado, storage lleno, etc.): la
    // eleccion sigue funcionando durante la sesion, solo no se recuerda.
  }
}

function elFocoEsEdicion() {
  const el = document.activeElement;
  if (!el) return false;
  if (el.isContentEditable) return true;
  if (el.tagName === "TEXTAREA") return true;
  if (el.tagName === "INPUT") {
    return !["button", "checkbox", "radio", "range", "submit", "reset", "file"].includes(el.type);
  }
  return false;
}

/**
 * Instala el selector global de parte dentro de `contenedor` (normalmente
 * la barra superior de cada pagina) e instala el atajo de teclado F2 para
 * alternar entre las dos partes desde cualquier lugar de la pagina (salvo
 * mientras se esta escribiendo en un campo de texto).
 *
 * `onCambiar(id, anterior)` se llama cada vez que la parte activa cambia,
 * ya sea por click o por el atajo de teclado (no se llama en la carga
 * inicial: quien instala el selector debe leer el valor inicial con
 * `obtener()` y aplicarlo el mismo).
 *
 * Devuelve `{ obtener(), fijar(id) }` para que el resto de la pagina pueda
 * leer/cambiar la parte activa en un solo lugar (por ejemplo, unas "tabs"
 * locales que representan lo mismo, como en comparacion.html).
 */
export function instalarSelectorParte(contenedor, onCambiar) {
  let activa = obtenerParteGuardada();

  const nav = document.createElement("div");
  nav.className = "selector-parte";
  nav.setAttribute("role", "tablist");
  nav.setAttribute("aria-label", "Parte de la actividad");

  const botones = PARTES.map((p) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "selector-parte-btn";
    btn.dataset.parte = p.id;
    btn.setAttribute("role", "tab");
    btn.title = `Trabajar en ${p.etiqueta} (atajo: F2 alterna entre partes)`;
    btn.textContent = p.etiqueta;
    btn.addEventListener("click", () => fijar(p.id));
    nav.appendChild(btn);
    return btn;
  });

  function pintar() {
    botones.forEach((b) => {
      const esActiva = b.dataset.parte === activa;
      b.classList.toggle("activo", esActiva);
      b.setAttribute("aria-selected", esActiva ? "true" : "false");
    });
  }

  function fijar(id, dispararCallback = true) {
    if (!esParteValida(id) || id === activa) {
      if (esParteValida(id)) pintar();
      return;
    }
    const anterior = activa;
    activa = id;
    guardarParteActiva(id);
    pintar();
    if (dispararCallback) onCambiar(id, anterior);
  }

  pintar();
  contenedor.appendChild(nav);

  window.addEventListener("keydown", (e) => {
    if (e.key !== "F2") return;
    if (elFocoEsEdicion()) return;
    e.preventDefault();
    fijar(otraParte(activa));
  });

  return {
    obtener: () => activa,
    // Fija la parte SIN volver a disparar onCambiar (para sincronizar el
    // selector desde afuera, por ejemplo cuando cambia por otra via como
    // unas tabs locales que representan la misma eleccion).
    fijar: (id) => fijar(id, false),
  };
}
