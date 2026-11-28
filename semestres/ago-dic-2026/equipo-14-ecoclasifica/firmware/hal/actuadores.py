# ============================================
# Proyecto:  EcoClasifica
# Archivo:   actuadores.py
# Objetivo:  HAL de actuadores: servo de la compuerta, buzzer activo y relevador.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

from machine import Pin, PWM

from config import PINES, RELE_ACTIVO_BAJO, BUZZER_ACTIVO_BAJO


def _nivel(encendido, activo_bajo):
    """Nivel lógico del pin para encender/apagar según la polaridad del módulo."""
    return int(bool(encendido) != activo_bajo)


class Actuadores:
    def __init__(self):
        # El nivel de "apagado" se fija desde el constructor para que el
        # relé/buzzer no se activen un instante al arrancar.
        self._buzzer = Pin(PINES['BUZZER'], Pin.OUT, value=_nivel(False, BUZZER_ACTIVO_BAJO))
        self._rele = Pin(PINES['RELE'], Pin.OUT, value=_nivel(False, RELE_ACTIVO_BAJO))
        self._buzzer_on = False
        self._rele_on = False

        # Servo: la frecuencia va en el constructor (si se asigna después, el servo zumba sin moverse).
        self._servo = PWM(Pin(PINES['SERVO']), freq=50)
        self._servo.duty_ns(0)  # sin señal hasta el primer comando: no se mueve al arrancar
        self._angulo = None

    # ---------------- Servo ----------------

    def mover_servo(self, angulo):
        """Gira el servo a 'angulo' (0-180). Pulso de 0.5 ms a 2.5 ms."""
        angulo = max(0, min(180, int(angulo)))
        ns = int(500000 + (angulo / 180) * 2000000)
        self._servo.duty_ns(ns)
        self._angulo = angulo

    def angulo_servo(self):
        return self._angulo

    # ---------------- Buzzer activo ----------------

    def buzzer(self, encendido):
        self._buzzer_on = bool(encendido)
        self._buzzer.value(_nivel(encendido, BUZZER_ACTIVO_BAJO))

    def buzzer_encendido(self):
        return self._buzzer_on

    # ---------------- Relevador ----------------

    def rele(self, encendido):
        self._rele_on = bool(encendido)
        self._rele.value(_nivel(encendido, RELE_ACTIVO_BAJO))

    def rele_encendido(self):
        return self._rele_on
