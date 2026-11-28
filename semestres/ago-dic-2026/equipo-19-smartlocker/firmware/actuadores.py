# ============================================================
# actuadores.py - Buzzer PWM + teclado matricial 4x4
# ============================================================

from machine import Pin, PWM
from time import sleep
import configuracion


class Actuadores:
    def __init__(self):
        self.buzzer = PWM(Pin(configuracion.BUZZER_PIN), freq=1000, duty=0)
        self.filas = [Pin(p, Pin.OUT) for p in configuracion.FILAS]
        self.cols = [Pin(p, Pin.IN, Pin.PULL_UP) for p in configuracion.COLS]
        for f in self.filas:
            f.on()

    def beep(self, ms=80, veces=1, freq=1000):
        self.buzzer.freq(freq)
        for _ in range(veces):
            self.buzzer.duty(512)  # sonido
            sleep(ms / 1000)
            self.buzzer.duty(0)    # silencio
            sleep(0.05)

    def alarma(self):
        for _ in range(3):
            self.buzzer.freq(800)
            self.buzzer.duty(512)
            sleep(0.15)
            self.buzzer.duty(0)
            sleep(0.08)

    def leer_teclado(self):
        for i, f in enumerate(self.filas):
            f.off()
            for j, c in enumerate(self.cols):
                if c.value() == 0:
                    sleep(0.02)  # antirrebote
                    if c.value() == 0:
                        while c.value() == 0:
                            pass  # esperar a que se suelte la tecla
                        f.on()
                        return configuracion.TECLAS[i][j]
            f.on()
        return None
