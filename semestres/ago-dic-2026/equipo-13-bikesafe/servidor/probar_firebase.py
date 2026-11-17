# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/probar_firebase.py
# Objetivo:  Probar la conexion con Firebase sin placas ni MQTT:
#            analiza una foto con la IA y escribe datos de ejemplo
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Uso (dentro de la carpeta servidor):
#   python probar_firebase.py
# Luego abran el dashboard: deben salir estos datos.

import os
import random
import time

import cv2

import config as cfg
from ia.detector import DetectorPersonas
from nube import Nube

nube = Nube(cfg.FIREBASE_LLAVE, cfg.CARPETA_REGISTROS)
if not nube.en_firebase:
    raise SystemExit("No hay conexion con Firebase: revisen serviceAccountKey.json")

print("1) Escribiendo 10 lecturas de sensores...")
for i in range(10):
    lectura = {"estado": "ASEGURADA",
               "distancia": round(random.uniform(110, 150) if i < 7 else random.uniform(25, 40), 1),
               "movimiento": round(0.42 if i == 8 else random.uniform(0.0, 0.06), 2),
               "inclinacion": round(random.uniform(0.5, 2.0), 1),
               "lazo": "ENTERO"}
    nube.guardar_lectura(lectura)
    nube.actualizar_estado(lectura)
    time.sleep(0.3)

print("2) Escribiendo una alerta...")
nube.guardar_alerta("PRUEBA: Alguien cerca de la bici", "ASEGURADA")
nube.actualizar_estado({"ultima_alerta": "PRUEBA: Alguien cerca de la bici"})

print("3) Analizando la foto de ejemplo con la IA...")
ruta = os.path.join("..", "media", "ia-deteccion-persona.jpg")
img = cv2.imread(ruta)
detector = DetectorPersonas(cfg.CONFIANZA_MINIMA, cfg.PROBAR_GIROS)
res = detector.analizar(img)
print("   IA:", res.clase, "{:.0f}%".format(res.confianza * 100))
ok, chico = cv2.imencode(".jpg", cv2.resize(detector.dibujar(img, res), (240, 180)))
nube.guardar_evento_ia(res, "alerta_ia" if res.hay_persona else "ninguna",
                       "PRUEBA", "Foto de ejemplo", chico.tobytes() if ok else None)
nube.actualizar_estado({"ultima_ia": res.clase,
                        "ultima_confianza": round(res.confianza, 3)})
print("Listo. Abran el dashboard o la consola de Firestore para verlo.")
