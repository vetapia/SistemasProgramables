# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   prueba_giro.py
# Objetivo:  Script de calibración y lectura de velocidad angular (yaw) del giroscopio MPU
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (2324XXXX)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import time

from hal.sensores import Giroscopio


def probar():
    gyro = Giroscopio()
    print("Deja el carro quieto para calibrar:", gyro.model)
    gyro.calibrar()
    print("Gira el chasis a la izquierda visto desde arriba. Debe marcar positivo.")
    try:
        while True:
            print(round(gyro.yaw(), 1), "grados/s")
            time.sleep_ms(100)
    except KeyboardInterrupt:
        pass
