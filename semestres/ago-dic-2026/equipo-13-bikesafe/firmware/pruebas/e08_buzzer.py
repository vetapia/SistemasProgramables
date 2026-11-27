# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e08_buzzer.py
# Objetivo:  Probar el buzzer con el transistor 2N2222 (GPIO25) y saber si es activo o pasivo
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# QUE DEBES OIR:
#   Parte 1 (3 pitidos):  si suenan fuerte  -> tu buzzer es ACTIVO.
#                         si solo hace "clic" -> es PASIVO.
#   Parte 2 (escala de tonos): un buzzer PASIVO canta la escala;
#                         uno ACTIVO suena raro o igual siempre.
# Apunta el resultado en config.py:  BUZZER_ACTIVO = True / False
#
# Si no suena NADA: revisa el transistor (patas E-B-C), la
# resistencia de 1k en la base y que el + del buzzer vaya a 5 V.

import time
from machine import Pin, PWM

PIN = 25

print("Parte 1: tres pitidos (prueba de buzzer ACTIVO)")
salida = Pin(PIN, Pin.OUT, value=0)
for _ in range(3):
    salida.value(1)
    time.sleep(0.2)
    salida.value(0)
    time.sleep(0.3)

time.sleep(1)
print("Parte 2: escala de tonos (prueba de buzzer PASIVO)")
pwm = PWM(Pin(PIN), freq=1000, duty=0)
for tono in (1000, 1500, 2000, 2500, 3000, 3500):
    print("  tono", tono, "Hz")
    pwm.freq(tono)
    pwm.duty(512)
    time.sleep(0.3)
pwm.duty(0)
pwm.deinit()
Pin(PIN, Pin.OUT, value=0)
print("Listo. Si la parte 1 sono fuerte: BUZZER_ACTIVO = True")
