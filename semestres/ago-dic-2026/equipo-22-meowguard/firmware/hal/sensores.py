# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   config.py
# Objetivo:  Configuración de pines GPIO, parámetros de sensores y credenciales base del ESP32
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import time
from machine import Pin, SoftI2C, time_pulse_us

import config as cfg


class Obstaculos:
    def __init__(self):
        self.trig = Pin(cfg.TRIG_PIN, Pin.OUT, value=0)
        self.echo = Pin(cfg.ECHO_PIN, Pin.IN)
        self.ir = [
            Pin(gpio, Pin.IN) if gpio is not None else None
            for gpio in (cfg.REAR_PIN, cfg.REAR_LEFT_PIN, cfg.REAR_RIGHT_PIN)
        ]

    def frente(self):
        self.trig.off()
        time.sleep_us(3)
        self.trig.on()
        time.sleep_us(10)
        self.trig.off()
        pulse = time_pulse_us(self.echo, 1, 26000)
        cm = pulse / 58.0
        return round(cm, 1) if 2 <= cm <= 400 else None

    def posteriores(self):
        return tuple(pin is not None and pin.value() == cfg.REAR_ACTIVE for pin in self.ir)


class Giroscopio:
    MODELOS = {0x70: "MPU-6500", 0x71: "MPU-9250", 0x73: "MPU-9255"}

    def __init__(self):
        bus = SoftI2C(sda=Pin(cfg.SDA_PIN), scl=Pin(cfg.SCL_PIN), freq=100000, timeout=2000)
        for address in (0x68, 0x69):
            try:
                ident = bus.readfrom_mem(address, 0x75, 1)[0]
            except OSError:
                continue
            print("MPU WHO_AM_I:", hex(ident), "direccion:", hex(address))
            if ident in self.MODELOS:
                break
        else:
            raise OSError("No se encontro un MPU con identificador compatible")
        self.bus = bus
        self.address = address
        self.model = self.MODELOS[ident]
        self.buf = bytearray(2)
        self.offset = 0.0
        # Reloj automático, filtro de ~41 Hz y escala de ±500 grados/s.
        bus.writeto_mem(address, 0x6B, b"\x01")
        time.sleep_ms(100)
        bus.writeto_mem(address, 0x6C, b"\x00")
        bus.writeto_mem(address, 0x1A, b"\x03")
        bus.writeto_mem(address, 0x1B, b"\x08")
        bus.writeto_mem(address, 0x19, b"\x09")

    def _raw(self):
        self.bus.readfrom_mem_into(self.address, 0x47, self.buf)
        value = (self.buf[0] << 8) | self.buf[1]
        if value >= 32768:
            value -= 65536
        return value / 65.5

    def calibrar(self):
        total = 0.0
        minimum = 500.0
        maximum = -500.0
        for _ in range(120):
            sample = self._raw()
            total += sample
            minimum = min(minimum, sample)
            maximum = max(maximum, sample)
            time.sleep_ms(10)
        self.offset = total / 120
        if maximum - minimum > 8 or abs(self.offset) > 15:
            raise OSError("Calibracion inestable. Deja el carro inmovil y reinicia.")

    def yaw(self):
        value = (self._raw() - self.offset) * cfg.GYRO_Z_SIGN
        return value if abs(value) >= 0.5 else 0.0


class Encoders:
    def __init__(self):
        from machine import Counter
        if (len(cfg.ENCODER_PINS) != 4 or len(set(cfg.ENCODER_PINS)) != 4 or
                len(cfg.ENCODER_PULSES_PER_REV) != 4 or min(cfg.ENCODER_PULSES_PER_REV) <= 0):
            raise ValueError("Se requieren cuatro GPIO de encoder distintos y PPR positivo.")
        self.items = [Counter(index, Pin(gpio, Pin.IN))
                      for index, gpio in enumerate(cfg.ENCODER_PINS)]
        self.reset()

    def reset(self):
        self.previous = [counter.value() for counter in self.items]

    def speeds(self, seconds):
        counts = [counter.value() for counter in self.items]
        pulses = [a - b for a, b in zip(counts, self.previous)]
        self.previous = counts
        circumference = 3.14159 * cfg.WHEEL_DIAMETER_CM
        return [p * circumference / (ppr * seconds)
                for p, ppr in zip(pulses, cfg.ENCODER_PULSES_PER_REV)]
