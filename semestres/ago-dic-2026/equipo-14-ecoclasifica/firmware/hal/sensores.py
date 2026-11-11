# ============================================
# Proyecto:  EcoClasifica
# Archivo:   sensores.py
# Objetivo:  HAL de sensores: HC-SR04, LDR digital y MPU6050 (detección de golpes), sin bloquear el loop.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

from machine import Pin, I2C, time_pulse_us
import math
import time

from config import (
    PINES, DISTANCIA_MIN_CM, DISTANCIA_MAX_CM,
    INTERVALO_DISTANCIA_MS, INTERVALO_MPU_MS, INTERVALO_RECONEXION_MPU_MS,
)
from hal.mpu6050 import MPU6050


class Sensores:
    def __init__(self):
        # --- LDR digital (0 = luz, 1 = oscuridad) ---
        self._ldr = Pin(PINES['LDR'], Pin.IN)

        # --- HC-SR04 ---
        self._trig = Pin(PINES['TRIG'], Pin.OUT, value=0)
        self._echo = Pin(PINES['ECHO'], Pin.IN)
        self._distancia = None
        self._ultima_distancia_ms = 0

        # --- MPU6050 (I2C). Si se desconecta no truena: se reintenta solo. ---
        self._i2c = I2C(0, scl=Pin(PINES['SCL']), sda=Pin(PINES['SDA']))
        self._mpu = None
        self._ultimo_intento_mpu = 0
        self._ultima_lectura_mpu = 0
        self._pico_golpe = 0.0
        self._conectar_mpu()

    # ---------------- Actualización (llamar una vez por vuelta del loop) ----------------

    def actualizar(self):
        ahora = time.ticks_ms()

        if time.ticks_diff(ahora, self._ultima_distancia_ms) >= INTERVALO_DISTANCIA_MS:
            self._ultima_distancia_ms = ahora
            self._distancia = self._medir_distancia()

        self._actualizar_mpu(ahora)

    # ---------------- HC-SR04 ----------------

    def _medir_distancia(self):
        self._trig.value(0)
        time.sleep_us(2)
        self._trig.value(1)
        time.sleep_us(10)
        self._trig.value(0)
        try:
            duracion = time_pulse_us(self._echo, 1, 30000)  # timeout 30 ms
        except OSError:
            return None
        if duracion < 0:
            return None
        distancia = (duracion / 2) / 29.1  # cm: el sonido recorre ~29.1 us por cm (ida y vuelta /2)
        if distancia < DISTANCIA_MIN_CM or distancia > DISTANCIA_MAX_CM:
            return None  # fuera del rango confiable
        return distancia

    # ---------------- MPU6050 ----------------

    def _conectar_mpu(self):
        try:
            self._mpu = MPU6050(self._i2c)
        except OSError:
            self._mpu = None

    def _actualizar_mpu(self, ahora):
        if self._mpu is None:
            if time.ticks_diff(ahora, self._ultimo_intento_mpu) >= INTERVALO_RECONEXION_MPU_MS:
                self._ultimo_intento_mpu = ahora
                self._conectar_mpu()
            return

        if time.ticks_diff(ahora, self._ultima_lectura_mpu) < INTERVALO_MPU_MS:
            return
        self._ultima_lectura_mpu = ahora

        try:
            ax, ay, az, _gx, _gy, _gz = self._mpu.get_values()
        except OSError:
            # Se desconectó: se descarta el sensor y se reintenta cada segundo.
            self._mpu = None
            self._ultimo_intento_mpu = ahora
            return

        # En reposo la magnitud de la aceleración vale ~1 g; un golpe la desvía.
        magnitud = math.sqrt(ax * ax + ay * ay + az * az)
        desviacion = abs(magnitud - 1.0)
        if desviacion > self._pico_golpe:
            self._pico_golpe = desviacion

    # ---------------- Contrato público ----------------

    def obtener_luz(self):
        """0 = luz, 1 = oscuridad."""
        return self._ldr.value()

    def leer_distancia(self):
        """cm, o None si no hay lectura válida."""
        return self._distancia

    def obtener_golpe(self):
        """Desviación máxima (g) respecto al reposo desde la última llamada.
        Se reinicia al leerse. None si el MPU6050 está desconectado."""
        if self._mpu is None:
            return None
        pico = self._pico_golpe
        self._pico_golpe = 0.0
        return pico

    def mpu_conectado(self):
        return self._mpu is not None
