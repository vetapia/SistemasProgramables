# ============================================================
# sensores.py - DHT11 + HC-SR04
# ============================================================

from machine import Pin, time_pulse_us
from time import sleep_us
import dht
import configuracion


class Sensores:
    def __init__(self):
        # Sensor fisico DHT11 (no DHT22)
        self.dht = dht.DHT11(Pin(configuracion.DHT_PIN))
        self.trig = Pin(configuracion.TRIG_PIN, Pin.OUT)
        self.echo = Pin(configuracion.ECHO_PIN, Pin.IN)
        self.temp = 0
        self.hum = 0
        self.dist = -1.0

    def leer_dht(self):
        try:
            self.dht.measure()
            self.temp = self.dht.temperature()
            self.hum = self.dht.humidity()
        except Exception as e:
            # Se conservan las ultimas lecturas validas si una medicion falla.
            print("Error DHT11:", e)
        return self.temp, self.hum

    def leer_distancia(self):
        self.trig.off()
        sleep_us(2)
        self.trig.on()
        sleep_us(10)
        self.trig.off()

        try:
            t = time_pulse_us(self.echo, 1, 30000)
            if t < 0:
                self.dist = -1.0
            else:
                # El pulso recorre la distancia de ida y vuelta.
                self.dist = (t * 0.0343) / 2
        except Exception:
            self.dist = -1.0
        return self.dist
