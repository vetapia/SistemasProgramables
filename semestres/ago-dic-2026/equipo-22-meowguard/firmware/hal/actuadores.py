# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   actuadores.py
# Objetivo:  Controla motores DC mediante PWM y la activación temporizada del atomizador
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import time
from machine import Pin, PWM

import config as cfg


class Motores:
    def __init__(self):
        self.outputs = [PWM(Pin(pin), freq=cfg.PWM_HZ, duty_u16=0)
                        for pin in cfg.MOTOR_PINS]
        self.signs = (0, 0)
        self.power = (0.0, 0.0)
        self.ready = time.ticks_ms()

    def _off(self):
        for pwm in self.outputs:
            pwm.duty_u16(0)
        self.power = (0.0, 0.0)

    def stop(self, now):
        if self.signs != (0, 0):
            self._off()
            self.signs = (0, 0)
            self.ready = time.ticks_add(now, 8)

    def apply(self, signs, target, now, elapsed_ms):
        if signs != self.signs:
            self._off()
            self.signs = signs
            self.ready = time.ticks_add(now, 8)
        if time.ticks_diff(now, self.ready) < 0:
            return
        # Reduce de inmediato. Incrementa ~3 puntos cada 20 ms.
        step = 0.15 * min(elapsed_ms, 45)
        left = min(target[0], self.power[0] + step)
        right = min(target[1], self.power[1] + step)
        for side, value in enumerate((left, right)):
            active = 2 * side + (1 if signs[side] < 0 else 0)
            self.outputs[active].duty_u16(int(value * 655.35))
        self.power = left, right


class Atomizador:
    def __init__(self):
        self.power = None
        self.fan = None
        self.servo = None
        self.phase = "apagado"
        self.until = None
        self.spray_end = None
        if cfg.ATOMIZER_POWER_PIN is not None:
            self.power = Pin(cfg.ATOMIZER_POWER_PIN, Pin.OUT, value=1 - cfg.ATOMIZER_ACTIVE)
            if cfg.FAN_PIN is not None:
                self.fan = Pin(cfg.FAN_PIN, Pin.OUT, value=1 - cfg.FAN_ACTIVE)
            if cfg.ATOMIZER_SERVO_PIN is not None:
                self.servo = PWM(Pin(cfg.ATOMIZER_SERVO_PIN), freq=50, duty_u16=0)
                self.servo.duty_ns(cfg.SERVO_REST_US * 1000)

    def start(self, now):
        if self.power is None or self.phase != "apagado":
            return False
        self.power.value(cfg.ATOMIZER_ACTIVE)
        if self.fan is not None:
            self.fan.value(cfg.FAN_ACTIVE)
        self.phase = "espera" if self.servo is not None else "atomizando"
        self.until = time.ticks_add(now, 450)
        extra = 800 if self.servo is not None else 0
        self.spray_end = time.ticks_add(now, min(max(cfg.SPRAY_MS, 250), 5000) + extra)
        return True

    def stop(self):
        if self.power is not None:
            self.power.value(1 - cfg.ATOMIZER_ACTIVE)
        if self.fan is not None:
            self.fan.value(1 - cfg.FAN_ACTIVE)
        if self.servo is not None and self.phase != "apagado":
            self.servo.duty_ns(cfg.SERVO_REST_US * 1000)
        self.phase = "apagado"

    def update(self, now):
        if self.phase == "apagado":
            return
        if time.ticks_diff(now, self.spray_end) >= 0:
            self.stop()
        elif self.phase == "espera" and time.ticks_diff(now, self.until) >= 0:
            self.servo.duty_ns(cfg.SERVO_PRESS_US * 1000)
            self.phase = "pulsando"
            self.until = time.ticks_add(now, 300)
        elif self.phase == "pulsando" and time.ticks_diff(now, self.until) >= 0:
            self.servo.duty_ns(cfg.SERVO_REST_US * 1000)
            self.phase = "atomizando"
