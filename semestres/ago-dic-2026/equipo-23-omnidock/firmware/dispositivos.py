from machine import Pin, PWM
import time

class SensorMoneda:
    def __init__(self, pin_num=13):
        self.sensor = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.ultimo_disparo = 0

    def detectado(self):
        if self.sensor.value() == 0:
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, self.ultimo_disparo) > 500:
                self.ultimo_disparo = ahora
                return True
        return False

class ServoPuerta:
    def __init__(self, pin_num=2):
        self.pwm = PWM(Pin(pin_num), freq=50)
        self.cerrar()

    def cerrar(self):
        self.pwm.duty(26)
        
    def abrir(self):
        self.pwm.duty(77)