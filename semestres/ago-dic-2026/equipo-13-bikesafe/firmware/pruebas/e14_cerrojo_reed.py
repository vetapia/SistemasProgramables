# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e14_cerrojo_reed.py
# Objetivo:  Probar el interruptor magnetico (reed switch) del cerrojo
#            en GPIO18
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# CONEXION: el reed switch tiene 2 patitas (no tiene polaridad).
#   una patita -> D18      la otra -> GND
#   (no lleva resistencia: usamos la pull-up interna de la ESP32)
#
# OJO: el reed es una capsula de VIDRIO. No doblen las patitas pegado
# al vidrio porque se estrella; doblen a 3 mm del cuerpo.
#
# QUE DEBES VER: acerca el iman -> "CERRADO (iman cerca)".
# Alejalo -> "ABIERTO (iman lejos)". Sirve para encontrar la mejor
# posicion del iman en la punta del cable antes de pegarlo.

import time
from machine import Pin

reed = Pin(18, Pin.IN, Pin.PULL_UP)
anterior = None
cambios = 0
print("Acerca y aleja el iman del reed switch...")
while True:
    valor = reed.value()
    if valor != anterior:
        cambios += 1
        print("#{}  {}".format(cambios, "CERRADO (iman cerca)" if valor == 0
                               else "ABIERTO (iman lejos)"))
        anterior = valor
    time.sleep_ms(20)
