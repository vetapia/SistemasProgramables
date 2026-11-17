# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e05_enlace.py
# Objetivo:  Probar el cable serie entre la ESP32 normal y la Freenove (se corre en la ESP32 NORMAL)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# ANTES: la Freenove debe estar prendida y corriendo su main.py.
# Cables: ESP32 GPIO17 (TX2) -> Freenove GPIO33
#         ESP32 GPIO16 (RX2) <- Freenove GPIO32
#         GND de una con GND de la otra  (sin esto NO funciona)
#
# QUE DEBES VER: cada 15 s pide una foto y la Freenove contesta
#   "OK|FOTO|guardada como foto_0.jpg"  (o "OK|FOTO|telegram").
# Si no contesta nada: TX y RX cruzados, o falta el GND comun.

import time
from machine import UART

uart = UART(2, baudrate=9600, tx=17, rx=16, timeout=0)
ultimo = time.ticks_add(time.ticks_ms(), -15000)
pendiente = b""

while True:
    if time.ticks_diff(time.ticks_ms(), ultimo) >= 15000:
        ultimo = time.ticks_ms()
        print("-> FOTO|PRUEBA|Foto de prueba")
        uart.write("FOTO|PRUEBA|Foto de prueba\n")
    dato = uart.read()
    if dato:
        pendiente += dato
        while b"\n" in pendiente:
            renglon, pendiente = pendiente.split(b"\n", 1)
            print("<-", renglon.decode().strip())
    time.sleep(0.05)
