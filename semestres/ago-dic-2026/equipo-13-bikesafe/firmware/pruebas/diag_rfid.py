# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/diag_rfid.py
# Objetivo:  Diagnostico automatico del lector RFID RC522: prueba
#            velocidades, buses SPI y MISO/MOSI cruzados, y revisa
#            si el cable MISO de verdad trae respuesta del lector
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Solo corran este archivo con F5 y manden captura de TODO lo que salga.
# No necesita la libreria mfrc522.

import time
from machine import Pin, SPI, SoftSPI

SCK, MOSI, MISO, CS, RST = 18, 23, 19, 5, 4
BUENOS = (0x88, 0x90, 0x91, 0x92, 0xB2, 0x12, 0x15)


def reiniciar_lector(rst):
    rst.value(0)
    time.sleep_ms(50)
    rst.value(1)
    time.sleep_ms(100)


def leer_version(spi, cs):
    cs.value(0)
    spi.write(bytes([0xEE]))          # "quiero leer el registro 0x37"
    dato = spi.read(1, 0x00)
    cs.value(1)
    return dato[0]


def probar(nombre, crear_spi, cs, rst):
    try:
        spi = crear_spi()
    except Exception as e:
        print("  {:<32} no se pudo crear: {}".format(nombre, e))
        return None
    reiniciar_lector(rst)
    lecturas = [leer_version(spi, cs) for _ in range(3)]
    try:
        spi.deinit()
    except Exception:
        pass
    texto = " ".join("0x{:02x}".format(v) for v in lecturas)
    ok = all(v in BUENOS for v in lecturas)
    print("  {:<32} {}  {}".format(nombre, texto, "<<< FUNCIONA" if ok else ""))
    return lecturas[0] if ok else None


print("\n===== 1) Revisar los pines sueltos =====")
rst = Pin(RST, Pin.OUT, value=1)
cs = Pin(CS, Pin.OUT, value=1)
reiniciar_lector(rst)
miso_up = Pin(MISO, Pin.IN, Pin.PULL_UP).value()
miso_down = Pin(MISO, Pin.IN, Pin.PULL_DOWN).value()
print("  MISO con pull-up = {}, con pull-down = {}".format(miso_up, miso_down))
if miso_up == 1 and miso_down == 0:
    print("  -> MISO esta 'al aire' (normal mientras el lector no habla)")
elif miso_up == miso_down:
    print("  -> MISO esta pegado a {} (algo lo jala: corto o cable a otro lado)"
          .format("3.3V" if miso_up else "GND"))

print("\n===== 2) Probar todas las combinaciones =====")
combos = []
for vel in (100000, 400000, 1000000):
    for bus in (1, 2):
        combos.append(("SPI{} {} kHz".format(bus, vel // 1000),
                       lambda b=bus, v=vel: SPI(b, baudrate=v, polarity=0, phase=0,
                                                 sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))))
combos.append(("SoftSPI 100 kHz",
               lambda: SoftSPI(baudrate=100000, polarity=0, phase=0,
                               sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))))
combos.append(("SoftSPI MISO/MOSI cruzados",
               lambda: SoftSPI(baudrate=100000, polarity=0, phase=0,
                               sck=Pin(SCK), mosi=Pin(MISO), miso=Pin(MOSI))))

exito = None
for nombre, crear in combos:
    r = probar(nombre, crear, cs, rst)
    if r and not exito:
        exito = nombre

print("\n===== RESULTADO =====")
if exito:
    print("EL LECTOR FUNCIONA con:", exito)
    print("Manden captura a Claude para ajustar el codigo del candado.")
else:
    print("Ninguna combinacion funciono. Manden captura de todo esto a Claude.")
