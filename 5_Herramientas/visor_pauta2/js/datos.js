/* Datos del visor: niveles disponibles y cómo armar la ruta de cada imagen.
   Las imágenes viven en 5_Herramientas/pauta_actividad2, hermana de esta
   carpeta, con el patrón vistas_n_<nivel>_pieza<N>.jpg */

const NIVELES = [
  { clave: "ele", nombre: "Elemental", cantidad: 16 },
  { clave: "med", nombre: "Medio", cantidad: 12 },
  { clave: "alto", nombre: "Alto", cantidad: 16 },
];

function rutaImagen(claveNivel, numero) {
  return `../pauta_actividad2/vistas_n_${claveNivel}_pieza${numero}.jpg`;
}
