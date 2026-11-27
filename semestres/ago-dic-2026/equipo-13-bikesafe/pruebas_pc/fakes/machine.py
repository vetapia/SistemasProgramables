# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/fakes/machine.py
# Objetivo:  Falso del modulo machine de MicroPython (pines, PWM, UART, I2C) para probar en la PC
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
# Falsos de MicroPython para probar en CPython
import time as _t
PINES = {}      # numero -> FakePin
class Pin:
    OUT=1; IN=0; PULL_UP=2
    def __init__(self, n, modo=0, pull=None, value=None):
        self.n=n; self.modo=modo; self.pull=pull
        prev = PINES.get(n)
        self._v = value if value is not None else (prev._v if prev else (1 if pull==Pin.PULL_UP else 0))
        self.forzado = prev.forzado if prev else None
        PINES[n]=self
    def value(self, v=None):
        if v is None:
            return self.forzado if self.forzado is not None else self._v
        self._v = 1 if v else 0
def forzar(n, v):
    p = PINES.get(n)
    if p is None: p = Pin(n)
    p.forzado = v
class PWM:
    def __init__(self, pin, freq=50, duty=None): self.pin=pin; self.f=freq; self.d=0; PWMS.append(self)
    def duty(self, d=None):
        if d is None: return self.d
        self.d=d
    def freq(self, f=None):
        if f is None: return self.f
        self.f=f
PWMS=[]
UARTS={}
class UART:
    def __init__(self, n, baudrate=9600, tx=None, rx=None, timeout=0):
        self.n=n; self.entrada=b""; self.salida=[]; UARTS[n]=self
    def write(self, s):
        if isinstance(s,str): s=s.encode()
        self.salida.append(s.decode()); return len(s)
    def read(self):
        d=self.entrada; self.entrada=b""; return d or None
class I2C:
    lectura=(0.0,0.0,1.0); falla=False
    def __init__(self, *a, **k): pass
    def writeto_mem(self, *a):
        if I2C.falla: raise OSError(19)
    def readfrom_mem_into(self, addr, reg, buf):
        if I2C.falla: raise OSError(19)
        vals=[int(v*16384) for v in I2C.lectura]
        for i,v in enumerate(vals):
            v &= 0xFFFF; buf[2*i]=v>>8; buf[2*i+1]=v&0xFF
DISTANCIA=[150.0]
def time_pulse_us(pin, nivel, tmax):
    d=DISTANCIA[0]
    return -1 if d is None else int(d*2/0.0343)
class WDT:
    def __init__(self, timeout): pass
    def feed(self): pass
def unique_id(): return b"\x24\x0a\xc4\x12\x34\x56"
