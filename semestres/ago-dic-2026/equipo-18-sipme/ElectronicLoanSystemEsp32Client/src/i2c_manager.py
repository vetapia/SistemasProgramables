"""Configura y expone el bus I2C por software utilizado por la pantalla."""

import machine

class I2CManager:
    """Encapsula los pines y la instancia SoftI2C de MicroPython."""

    def __init__(self, scl, sda, freq=400000):
        """Crea el bus con los GPIO de reloj y datos indicados.

        La frecuencia predeterminada es de 400 kHz, correspondiente al modo
        rápido de I2C.
        """
        self._scl = machine.Pin(scl)
        self._sda = machine.Pin(sda)
        self._i2c = machine.SoftI2C(scl=self._scl, sda=self._sda, freq=freq)

    def get_scl(self):
        """Devuelve el objeto Pin utilizado como señal de reloj."""
        return self._scl

    def get_sda(self):
        """Devuelve el objeto Pin utilizado para transmitir los datos."""
        return self._sda

    def get_i2c(self):
        """Devuelve el bus configurado para conectarlo a un periférico."""
        return self._i2c
