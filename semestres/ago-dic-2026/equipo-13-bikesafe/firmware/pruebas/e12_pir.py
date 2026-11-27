# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e12_pir.py
# Objetivo:  Probar el sensor de movimiento PIR HC-SR501 (OUT en D34)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# CONEXION:  VCC -> riel 5 V   |   GND -> riel -   |   OUT -> D34
#
# QUE DEBES VER: al encenderlo, el PIR tarda ~1 minuto en "calentarse".
# Despues, al mover la mano frente al domo blanco sale
# "ALGUIEN SE MUEVE" y al quedarse quieto, unos segundos despues, "nadie".
#
# El PIR tiene 2 perillas naranjas:
#   - Sx (sensibilidad): que tan lejos detecta (giren a la mitad)
#   - Tx (tiempo): cuanto dura la senal (giren todo a la izquierda = ~3 s)

import time
from machine import Pin

pir = Pin(34, Pin.IN)
anterior = None
print("Esperando... (el PIR tarda ~1 min en estabilizarse)")
while True:
    estado = pir.value()
    if estado != anterior:
        print("ALGUIEN SE MUEVE" if estado else "nadie")
        anterior = estado
    time.sleep(0.1)
