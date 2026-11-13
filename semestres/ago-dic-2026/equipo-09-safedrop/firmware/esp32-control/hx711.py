# SafeDrop: lectura HX711 de 24 bits por MicroPython
# Equipo 09: Alan Medina Rivas (23240436), Victor Hugo Ojeda Cabrera (23240390)
# Materia: Sistemas Programables - ISC TecNM Leon
# Semestre: ago-dic-2026
from machine import Pin, disable_irq, enable_irq
from time import sleep_us, sleep_ms, ticks_ms, ticks_diff

class HX711:
    def __init__(self, dout=32, sck=33):
        self.dt = Pin(dout, Pin.IN)
        self.ck = Pin(sck, Pin.OUT, value=0)
        self.cero = 0
        self.cuentas_por_gramo = None

    def leer(self, timeout_ms=1200):
        inicio = ticks_ms()
        while self.dt.value():
            if ticks_diff(ticks_ms(), inicio) >= timeout_ms:
                return None
            sleep_ms(2)
        n = 0
        irq = disable_irq()
        try:
            for i in range(24):
                self.ck.on()
                sleep_us(1)
                n = (n << 1) | self.dt.value()
                self.ck.off()
                sleep_us(1)
            self.ck.on()
            sleep_us(1)
            self.ck.off()
        finally:
            enable_irq(irq)
        return n - 0x1000000 if n & 0x800000 else n

    def promedio(self, muestras=5):
        total = 0
        for i in range(muestras):
            valor = self.leer()
            if valor is None:
                return None
            total += valor
        return total / muestras

    def tara(self, muestras=8):
        valor = self.promedio(muestras)
        if valor is None:
            return False
        self.cero = valor
        return True

    def calibrar(self, gramos, muestras=8):
        if gramos <= 0:
            raise ValueError("La masa de referencia debe ser positiva")
        valor = self.promedio(muestras)
        if valor is None:
            return False
        diferencia = valor - self.cero
        if abs(diferencia) < 1:
            raise ValueError("No hay variacion suficiente para calibrar")
        self.cuentas_por_gramo = diferencia / gramos
        return True

    def gramos(self, muestras=3):
        if self.cuentas_por_gramo is None:
            raise RuntimeError("Calibrar con masa conocida primero")
        valor = self.promedio(muestras)
        if valor is None:
            return None
        return (valor - self.cero) / self.cuentas_por_gramo
