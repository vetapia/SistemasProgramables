// ============================================
// Proyecto:  BikeSafe - Candado inteligente portatil
// Archivo:   interfaz/firebase-config.js
// Objetivo:  Datos de conexion del dashboard con su proyecto de Firebase
// Equipo:    Oscar Sandoval Cabrera (23240457),
//            Diego Josue Talamantes Santiago (23240355)
// Materia:   Sistemas Programables - ISC TecNM Leon
// Semestre:  ago-dic-2026
// ============================================
//
// Donde se sacan: consola de Firebase > Configuracion del proyecto >
// General > "Tus apps" > App web (</>) > "Configuracion del SDK".
// Copien ese bloque aqui. Estos datos NO son secretos (los ve cualquier
// navegador); lo que protege la base son las reglas de firestore.rules.

export const firebaseConfig = {
  apiKey: "AIzaSyC13nYA2WOaK5vgJZWKNdNLx9aq-fo1Q3s",
  authDomain: "bikesafe-equipo13.firebaseapp.com",
  projectId: "bikesafe-equipo13",
  storageBucket: "bikesafe-equipo13.firebasestorage.app",
  messagingSenderId: "274871777413",
  appId: "1:274871777413:web:35a4d728d64e3c6cb0d1ec",
};
