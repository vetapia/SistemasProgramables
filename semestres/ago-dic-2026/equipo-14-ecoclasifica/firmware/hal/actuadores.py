# ============================================
# Proyecto:  EcoClasifica
# Archivo:   actuadores.py
# Objetivo:  HAL de actuadores: servo de la compuerta, buzzer activo y relevador.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

from machine import Pin, PWM

from config import PINES, RELE_ACTIVO_BAJO, BUZZER_ACTIVO_BAJO, SERVO_ANGULOS


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

        # Un servo por tapa. La frecuencia va en el constructor (si se asigna después, zumba sin moverse).
        self._servos = {}
        self._angulos = {}
        for nombre in SERVO_ANGULOS:
            servo = PWM(Pin(PINES['SERVO_' + nombre.upper()]), freq=50)
            servo.duty_ns(0)  # sin señal hasta el primer comando: no se mueve al arrancar
            self._servos[nombre] = servo
            self._angulos[nombre] = None
            
            
        # ---------------- Servos (una tapa cada uno) ----------------

    def mover_servo(self, nombre, angulo):
        """Gira el servo de la tapa 'nombre' a 'angulo' (0-180). Pulso de 0.5 ms a 2.5 ms."""
        angulo = max(0, min(180, int(angulo)))
        ns = int(500000 + (angulo / 180) * 2000000)
        self._servos[nombre].duty_ns(ns)
        self._angulos[nombre] = angulo

    def abrir_tapa(self, nombre):
        self.mover_servo(nombre, SERVO_ANGULOS[nombre][1])

    def cerrar_tapa(self, nombre):
        self.mover_servo(nombre, SERVO_ANGULOS[nombre][0])

    def angulo_servo(self, nombre):
        return self._angulos[nombre]

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

