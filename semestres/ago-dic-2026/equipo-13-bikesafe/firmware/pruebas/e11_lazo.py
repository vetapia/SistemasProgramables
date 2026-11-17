# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e11_lazo.py
# Objetivo:  Probar el lazo anti-corte (un cable de GPIO14 a GND)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# QUE DEBES VER: "ENTERO" mientras el cable une GPIO14 con GND.
# Desconecta una punta (como si lo cortaran) y debe decir "CORTADO".

import time
from machine import Pin

lazo = Pin(14, Pin.IN, Pin.PULL_UP)
anterior = None
while True:
    estado = "CORTADO" if lazo.value() else "ENTERO"
    if estado != anterior:
        print("Lazo:", estado)
        anterior = estado
    time.sleep(0.1)
