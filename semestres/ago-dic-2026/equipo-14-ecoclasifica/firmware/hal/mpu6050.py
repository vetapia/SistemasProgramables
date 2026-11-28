# ============================================
# Proyecto:  EcoClasifica
# Archivo:   mpu6050.py
# Objetivo:  Driver mínimo del MPU6050 (acelerómetro y giroscopio) sobre machine.I2C.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import struct


class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr

        quien_es = self.i2c.readfrom_mem(self.addr, 0x75, 1)[0]
        if quien_es != 0x68:
            raise OSError("MPU6050 no responde como se esperaba (WHO_AM_I distinto)")

        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # despierta el sensor

    def _leer_16(self, registro):
        datos = self.i2c.readfrom_mem(self.addr, registro, 2)
        return struct.unpack('>h', datos)[0]

    def get_values(self):
        """Regresa ax, ay, az en g  y  gx, gy, gz en grados/segundo."""
        ax = self._leer_16(0x3B) / 16384.0
        ay = self._leer_16(0x3D) / 16384.0
        az = self._leer_16(0x3F) / 16384.0
        gx = self._leer_16(0x43) / 131.0
        gy = self._leer_16(0x45) / 131.0
        gz = self._leer_16(0x47) / 131.0
        return ax, ay, az, gx, gy, gz
