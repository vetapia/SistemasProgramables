# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e03_mpu6050.py
# Objetivo:  Probar el acelerometro MPU6050 (SDA=GPIO21, SCL=GPIO22)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# QUE DEBES VER:
#   1) "Encontre: ['0x68']"  -> la ESP32 ve al sensor.
#      Si sale una lista vacia: SDA y SCL cruzados, falta 3.3 V o GND.
#   2) Tres numeros (X, Y, Z) en g. Con el sensor acostado y quieto,
#      Z vale cerca de 1.00 y X, Y cerca de 0. Inclinalo y cambian.
#   3) "cambio" = cuanto se movio respecto a como estaba al iniciar.
#      Dale golpecitos a la mesa: asi eliges UMBRAL_TOQUE_G.

import math
import time
from machine import Pin, I2C

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
print("Encontre:", [hex(d) for d in i2c.scan()])

MPU = 0x68
i2c.writeto_mem(MPU, 0x6B, b"\x00")     # despertar al sensor
time.sleep(0.1)


def leer():
    b = i2c.readfrom_mem(MPU, 0x3B, 6)
    valores = []
    for i in (0, 2, 4):
        v = (b[i] << 8) | b[i + 1]
        if v > 32767:
            v -= 65536
        valores.append(v / 16384)
    return valores


ref = leer()
print("Referencia:", ["{:.2f}".format(v) for v in ref])
maximo = 0
while True:
    x, y, z = leer()
    cambio = math.sqrt((x - ref[0]) ** 2 + (y - ref[1]) ** 2 +
                       (z - ref[2]) ** 2)
    maximo = max(maximo, cambio)
    print("X={:5.2f}  Y={:5.2f}  Z={:5.2f}   cambio={:4.2f} g  (max {:4.2f})"
          .format(x, y, z, cambio, maximo))
    time.sleep(0.2)
