# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e02_servo.py
# Objetivo:  Probar el servomotor SG90 (GPIO13) y encontrar los angulos de abierto y cerrado
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# QUE DEBES VER: el brazo va a 0, 90 y 180 grados y regresa.
# Despues te deja escribir angulos a mano para encontrar en cual
# queda ABIERTO y en cual CERRADO tu pestillo. Apuntalos en
# config.py (SERVO_ABIERTO y SERVO_CERRADO).
#
# Si la ESP32 se reinicia cuando se mueve el servo: falta el
# capacitor de 1000 uF en el riel de 5 V, o el servo esta
# conectado a 3.3 V en vez de 5 V.

import time
from machine import Pin, PWM

servo = PWM(Pin(13), freq=50, duty=0)


def mover(grados):
    grados = max(0, min(180, grados))
    servo.duty(int(26 + grados * 102 / 180))   # 26 = 0.5 ms, 128 = 2.5 ms
    time.sleep(0.6)
    servo.duty(0)                              # relajar el servo


for angulo in (0, 90, 180, 90, 0):
    print("Voy a", angulo, "grados")
    mover(angulo)
    time.sleep(0.5)

print("\nAhora tu: escribe un angulo (0 a 180) y Enter. Vacio = salir")
while True:
    texto = input("angulo> ").strip()
    if not texto:
        break
    try:
        mover(int(texto))
    except ValueError:
        print("Escribe solo un numero")
print("Fin")
