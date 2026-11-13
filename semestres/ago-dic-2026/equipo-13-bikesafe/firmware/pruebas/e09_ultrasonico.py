# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e09_ultrasonico.py
# Objetivo:  Probar el sensor ultrasonico HC-SR04 (TRIG=GPIO26, ECHO=GPIO27 con divisor)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# QUE DEBES VER: la distancia en cm, 4 veces por segundo. Acerca y
# aleja la mano: el numero debe cambiar.
#
#   "sin eco" siempre  -> revisa VCC a 5 V, TRIG y ECHO cruzados,
#                         o el divisor de resistencias mal armado.
#   numeros locos      -> el sensor apunta a la mesa o a un cable.
#
# RECUERDA: ECHO sale a 5 V. Debe pasar por el divisor (1k + 2k)
# antes de llegar a la ESP32, que solo aguanta 3.3 V.

import time
from machine import Pin, time_pulse_us

trig = Pin(26, Pin.OUT, value=0)
echo = Pin(27, Pin.IN)


def distancia_cm():
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duracion = time_pulse_us(echo, 1, 25000)
    if duracion < 0:
        return None
    return duracion * 0.0343 / 2


while True:
    d = distancia_cm()
    if d is None:
        print("sin eco")
    else:
        print("{:6.1f} cm  {}".format(d, "#" * int(min(d, 100) / 4)))
    time.sleep(0.25)
