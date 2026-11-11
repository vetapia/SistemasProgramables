# importamos Pin para seleccionar la salida y PWM para generar el pulso del servo
from machine import Pin, PWM


class ServoManager:
    """Convierte un angulo en la duracion de pulso esperada por el servomotor."""

    def __init__(self, pin, freq=50):
        """
        Creamos la salida PWM a 50 Hz, frecuencia comun en servomotores, y
        guardamos la ultima posicion solicitada para poder consultarla despues.
        """
        self._servo = PWM(Pin(pin), freq=freq)
        self._servo_deg = 0

    def get_deg(self):
        """Devuelve el ultimo angulo enviado al servo."""
        return self._servo_deg

    def update_deg(self, deg: int):
        """
        Limitamos el valor al recorrido fisico de 0 a 180 grados y lo mapeamos
        linealmente a pulsos de 1 a 2 milisegundos expresados en nanosegundos.
        """
        deg = max(0, min(180, deg))

        ton_ns = int(1_000_000 + (deg * 1_000_000 / 180))
        self._servo.duty_ns(ton_ns)
        self._servo_deg = deg
