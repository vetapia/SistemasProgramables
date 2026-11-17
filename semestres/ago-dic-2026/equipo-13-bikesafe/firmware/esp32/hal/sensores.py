# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   hal/sensores.py
# Objetivo:  Una clase por cada sensor (RFID, acelerometro,
#            ultrasonico y lazo anti-corte) para que main.py
#            solo pregunte "que esta pasando" sin saber de pines
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# HAL = "capa de abstraccion de hardware". Es la capa que habla
# directamente con las piezas. main.py nunca toca un pin: le pide
# las cosas a estas clases.

import math
import time
from machine import Pin, I2C, time_pulse_us


# ---------------------------------------------------------------
#  LECTOR RFID RC522
# ---------------------------------------------------------------
class LectorRFID:
    """Lee el numero (UID) de la tarjeta o llavero que se acerque."""

    def __init__(self, sck, mosi, miso, sda, rst):
        from mfrc522 import MFRC522
        self._chip = MFRC522(sck=sck, mosi=mosi, miso=miso, rst=rst, cs=sda)
        self._ultimo_uid = None
        self._ultimo_ms = 0

    def conectado(self):
        """True si el chip contesta (sirve para detectar cables mal)."""
        return self._chip.version() not in (0x00, 0xFF)

    def leer(self, ignorar_repetida_ms=2500):
        """Regresa el UID ("A1B2C3D4") solo UNA vez por pasada.

        Si dejas la tarjeta pegada, no la repite hasta que pasen
        'ignorar_repetida_ms' milisegundos. Asi no abre y cierra
        el candado como loco.
        """
        uid = self._chip.leer_uid()
        if uid is None:
            return None
        ahora = time.ticks_ms()
        repetida = (uid == self._ultimo_uid and
                    time.ticks_diff(ahora, self._ultimo_ms) < ignorar_repetida_ms)
        self._ultimo_uid = uid
        self._ultimo_ms = ahora
        return None if repetida else uid


# ---------------------------------------------------------------
#  ACELEROMETRO MPU6050
# ---------------------------------------------------------------
class Acelerometro:
    """Detecta si mueven o inclinan la bici.

    Idea: al asegurar la bici guardamos "hacia donde apunta la
    gravedad" (la referencia). Despues comparamos cada lectura
    contra esa referencia:
      - cambio():      cuanto cambio la aceleracion (en g)
      - inclinacion(): cuantos grados se inclino
    """

    DIRECCION = 0x68

    def __init__(self, sda, scl):
        self._i2c = I2C(0, sda=Pin(sda), scl=Pin(scl), freq=400000)
        self._buf = bytearray(6)
        self._ref = (0.0, 0.0, 1.0)
        # El MPU6050 arranca "dormido": escribir 0 en el registro
        # 0x6B lo despierta.
        self._i2c.writeto_mem(self.DIRECCION, 0x6B, b"\x00")
        time.sleep_ms(100)
        # Filtro interno (registro 0x1A) para quitar vibraciones
        # muy rapidas que no nos interesan.
        self._i2c.writeto_mem(self.DIRECCION, 0x1A, b"\x03")

    @staticmethod
    def _con_signo(alto, bajo):
        valor = (alto << 8) | bajo
        return valor - 65536 if valor > 32767 else valor

    def leer(self):
        """Regresa (ax, ay, az) en g. En reposo uno de los tres vale ~1."""
        self._i2c.readfrom_mem_into(self.DIRECCION, 0x3B, self._buf)
        b = self._buf
        # 16384 cuentas = 1 g (escala de +-2 g, la de fabrica)
        return (self._con_signo(b[0], b[1]) / 16384,
                self._con_signo(b[2], b[3]) / 16384,
                self._con_signo(b[4], b[5]) / 16384)

    def promedio(self, muestras=20):
        sx = sy = sz = 0.0
        for _ in range(muestras):
            x, y, z = self.leer()
            sx += x
            sy += y
            sz += z
            time.sleep_ms(5)
        return (sx / muestras, sy / muestras, sz / muestras)

    def guardar_referencia(self):
        """Llamar cuando la bici ya esta quieta y asegurada."""
        self._ref = self.promedio()
        return self._ref

    def cambio(self, lectura=None):
        """Cuanto se aleja la lectura de la referencia, en g."""
        x, y, z = lectura if lectura else self.leer()
        rx, ry, rz = self._ref
        return math.sqrt((x - rx) ** 2 + (y - ry) ** 2 + (z - rz) ** 2)

    def inclinacion(self, lectura=None):
        """Angulo (grados) entre la posicion actual y la referencia."""
        x, y, z = lectura if lectura else self.leer()
        rx, ry, rz = self._ref
        m1 = math.sqrt(x * x + y * y + z * z)
        m2 = math.sqrt(rx * rx + ry * ry + rz * rz)
        if m1 == 0 or m2 == 0:
            return 0.0
        coseno = (x * rx + y * ry + z * rz) / (m1 * m2)
        coseno = max(-1.0, min(1.0, coseno))
        return math.degrees(math.acos(coseno))


# ---------------------------------------------------------------
#  SENSOR ULTRASONICO HC-SR04
# ---------------------------------------------------------------
class Ultrasonico:
    """Mide distancia con sonido: manda un 'clic' y cuenta cuanto
    tarda en regresar el eco."""

    def __init__(self, trig, echo):
        self._trig = Pin(trig, Pin.OUT, value=0)
        self._echo = Pin(echo, Pin.IN)

    def distancia_cm(self):
        """Regresa la distancia en cm, o None si no hubo eco."""
        self._trig.value(0)
        time.sleep_us(3)
        self._trig.value(1)
        time.sleep_us(10)            # pulso de 10 microsegundos
        self._trig.value(0)
        # Esperamos el eco maximo 25 ms (unos 4 metros)
        duracion = time_pulse_us(self._echo, 1, 25000)
        if duracion < 0:
            return None
        # El sonido viaja a 0.0343 cm por microsegundo, ida y vuelta
        return duracion * 0.0343 / 2


# ---------------------------------------------------------------
#  LAZO ANTI-CORTE
# ---------------------------------------------------------------
class LazoAntiCorte:
    """Un cable que sale del pin, recorre el cable de acero y
    regresa a GND. Mientras este entero, el pin lee 0. Si lo
    cortan, la resistencia interna (pull-up) sube el pin a 1."""

    def __init__(self, pin):
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)

    def cortado(self):
        # Leemos 3 veces para no dar falsa alarma por ruido
        for _ in range(3):
            if self._pin.value() == 0:
                return False
            time.sleep_ms(2)
        return True
