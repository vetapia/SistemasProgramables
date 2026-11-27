# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e13_led_rgb.py
# Objetivo:  Probar el LED RGB (R=GPIO33, G=GPIO32, B=GPIO19) y saber
#            si es de catodo comun o de anodo comun
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# CONEXION: el LED RGB tiene 4 patitas; la MAS LARGA es la comun.
#   R  -> resistencia 220 ohm -> D33
#   G  -> resistencia 220 ohm -> D32
#   B  -> resistencia 220 ohm -> D19
#   comun (larga) -> GND   (si es de catodo comun)
#                 -> 3.3 V (si es de anodo comun)
#
# QUE DEBES VER: ROJO, VERDE, AZUL, AMARILLO, MORADO, CIAN, BLANCO.
# Si ves los colores "al reves" (todo prendido y se apaga un color),
# es de ANODO comun: cambia ANODO_COMUN = True aqui y en config.py
# (RGB_ANODO_COMUN = True). Si no prende nada, voltea la patita comun
# de GND a 3.3 V y vuelve a probar.

import time
from machine import Pin

ANODO_COMUN = False

r = Pin(33, Pin.OUT)
g = Pin(32, Pin.OUT)
b = Pin(19, Pin.OUT)

COLORES = [("ROJO", 1, 0, 0), ("VERDE", 0, 1, 0), ("AZUL", 0, 0, 1),
           ("AMARILLO", 1, 1, 0), ("MORADO", 1, 0, 1), ("CIAN", 0, 1, 1),
           ("BLANCO", 1, 1, 1), ("APAGADO", 0, 0, 0)]


def poner(vr, vg, vb):
    for pin, v in ((r, vr), (g, vg), (b, vb)):
        pin.value(1 - v if ANODO_COMUN else v)


while True:
    for nombre, vr, vg, vb in COLORES:
        print("Debe verse:", nombre)
        poner(vr, vg, vb)
        time.sleep(1)
