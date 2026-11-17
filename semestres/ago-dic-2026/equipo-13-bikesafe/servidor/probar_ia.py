# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/probar_ia.py
# Objetivo:  Probar la IA con fotos guardadas, sin MQTT ni placas
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Uso:  python probar_ia.py foto1.jpg foto2.jpg ...
# Guarda cada foto con su recuadro como  <nombre>_ia.jpg

import sys

import cv2

import config as cfg
from ia.detector import DetectorPersonas

detector = DetectorPersonas(cfg.CONFIANZA_MINIMA, cfg.PROBAR_GIROS)
for ruta in sys.argv[1:]:
    img = cv2.imread(ruta)
    if img is None:
        print(ruta, "-> no se pudo abrir")
        continue
    r = detector.analizar(img)
    print("{} -> {} ({:.0f}%, {}, giro {})".format(
        ruta, r.clase, r.confianza * 100, r.modelo, r.giro))
    cv2.imwrite(ruta.rsplit(".", 1)[0] + "_ia.jpg", detector.dibujar(img, r))
