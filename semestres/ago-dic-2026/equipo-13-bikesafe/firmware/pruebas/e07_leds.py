# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e07_leds.py
# Objetivo:  Probar los LEDs verde (GPIO32) y rojo (GPIO33)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# QUE DEBES VER: parpadea el verde 3 veces, luego el rojo 3 veces,
# y se repite. Si uno no prende: voltealo (pata larga hacia la
# resistencia) y revisa que la pata corta llegue a GND.
# Para detenerlo: boton STOP de Thonny.

import time
from machine import Pin

verde = Pin(32, Pin.OUT)
rojo = Pin(33, Pin.OUT)

while True:
    for led, nombre in ((verde, "VERDE"), (rojo, "ROJO")):
        print("Parpadea el", nombre)
        for _ in range(3):
            led.value(1)
            time.sleep(0.3)
            led.value(0)
            time.sleep(0.3)
