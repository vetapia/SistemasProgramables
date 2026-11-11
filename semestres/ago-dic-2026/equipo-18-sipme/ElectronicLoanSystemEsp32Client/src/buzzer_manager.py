from machine import Pin, PWM

class BuzzerManeger:
    def __init__(self, pin):
        self._buzzer = Pin(pin, Pin.OUT)

    def on(self):
        self._buzzer.value(1)

    def off(self):
        self._buzzer.value(0)