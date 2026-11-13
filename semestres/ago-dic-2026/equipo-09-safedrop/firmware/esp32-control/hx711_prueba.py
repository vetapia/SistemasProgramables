# ============================================
# Proyecto:  SafeDrop
# Archivo:   hx711_prueba.py
# Objetivo:  Verificar la celda de carga de 5 kg antes de calibrar.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import time
from hx711 import HX711

# Deben estar unidos a la ESP32: HX711 VCC 3V3, GND,
# DT/DOUT GPIO32 y SCK GPIO33.
# Celda de carga: rojo E+, negro E-, blanco A-, verde A+.

sensor = HX711(dout=32, sck=33)

print("SafeDrop - Prueba HX711")
print("Deja la plataforma vacia y sin tocar durante la tara.")
time.sleep(3)

if not sensor.tara(muestras=10):
    raise RuntimeError("HX711 no responde. Revisar VCC/GND/DT/SCK y soldaduras.")

print("Tara terminada. Cero:", sensor.cero)
print("Coloca y retira un objeto de la plataforma.")
print("Se mostraran CUENTAS relativas, no gramos calibrados.")

while True:
    valor = sensor.promedio(muestras=3)
    if valor is None:
        print("Sin lectura HX711; revisar cableado.")
    else:
        print("Cuentas relativas:", round(valor - sensor.cero, 1))
    time.sleep_ms(500)
