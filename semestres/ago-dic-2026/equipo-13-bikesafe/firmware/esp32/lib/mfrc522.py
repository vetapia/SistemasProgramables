# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   lib/mfrc522.py
# Objetivo:  Driver minimo del lector RFID RC522 (chip MFRC522)
#            por SPI: detecta una tarjeta y lee su numero (UID)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Basado en la libreria libre "micropython-mfrc522" (licencia MIT).
# Solo dejamos lo que BikeSafe necesita: pedir tarjeta y leer UID.
#
# NO necesitas entender este archivo para usar el lector.
# Solo se usa asi:
#
#     lector = MFRC522(sck=18, mosi=23, miso=19, rst=4, cs=5)
#     uid = lector.leer_uid()      # "A1B2C3D4" o None

import time
from machine import Pin, SPI


class MFRC522:
    OK = 0
    SIN_TARJETA = 1
    ERROR = 2

    PEDIR_TARJETA = 0x26     # comando REQA: "hay alguna tarjeta?"

    def __init__(self, sck, mosi, miso, rst, cs, bus=2):
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.rst = Pin(rst, Pin.OUT, value=0)
        self.spi = SPI(bus, baudrate=1000000, polarity=0, phase=0,
                       sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        time.sleep_ms(10)
        self.rst.value(1)            # soltar el reset del chip
        time.sleep_ms(50)
        self.iniciar()

    # ---------- leer y escribir registros del chip ----------
    def _escribir(self, registro, valor):
        self.cs.value(0)
        self.spi.write(bytes([(registro << 1) & 0x7E, valor & 0xFF]))
        self.cs.value(1)

    def _leer(self, registro):
        self.cs.value(0)
        self.spi.write(bytes([((registro << 1) & 0x7E) | 0x80]))
        dato = self.spi.read(1)
        self.cs.value(1)
        return dato[0]

    def _poner_bits(self, registro, mascara):
        self._escribir(registro, self._leer(registro) | mascara)

    def _quitar_bits(self, registro, mascara):
        self._escribir(registro, self._leer(registro) & (~mascara & 0xFF))

    # ---------- arranque ----------
    def iniciar(self):
        self._escribir(0x01, 0x0F)       # reinicio por software
        time.sleep_ms(50)
        self._escribir(0x2A, 0x8D)       # temporizador automatico
        self._escribir(0x2B, 0x3E)
        self._escribir(0x2D, 30)         # limite de espera ~15 ms
        self._escribir(0x2C, 0)
        self._escribir(0x15, 0x40)       # modulacion 100 % ASK
        self._escribir(0x11, 0x3D)       # modo CRC
        self._escribir(0x26, 0x70)       # ganancia maxima de antena
        self._poner_bits(0x14, 0x03)     # encender la antena

    def version(self):
        """Regresa el numero de version del chip (0x91 o 0x92 = bien;
        0x00 o 0xFF = revisa los cables)."""
        return self._leer(0x37)

    # ---------- hablar con la tarjeta ----------
    def _a_tarjeta(self, datos):
        recibido = []
        bits = 0
        estado = self.ERROR

        self._escribir(0x02, 0x77 | 0x80)   # habilitar avisos
        self._escribir(0x04, 0x7F)          # limpiar avisos viejos
        self._poner_bits(0x0A, 0x80)        # vaciar la cola (FIFO)
        self._escribir(0x01, 0x00)          # cancelar comando previo
        for d in datos:
            self._escribir(0x09, d)
        self._escribir(0x01, 0x0C)          # comando "transmitir y recibir"
        self._poner_bits(0x0D, 0x80)        # empezar a enviar

        intentos = 200
        avisos = 0
        while intentos > 0:
            avisos = self._leer(0x04)
            intentos -= 1
            if avisos & 0x31:               # llego respuesta o se acabo el tiempo
                break
        self._quitar_bits(0x0D, 0x80)

        if intentos == 0:
            return self.ERROR, recibido, bits
        if self._leer(0x06) & 0x1B:         # hubo error de comunicacion
            return self.ERROR, recibido, bits
        if avisos & 0x01:                   # se acabo el tiempo: no hay tarjeta
            return self.SIN_TARJETA, recibido, bits

        estado = self.OK
        n = self._leer(0x0A)
        ultimos = self._leer(0x0C) & 0x07
        bits = (n - 1) * 8 + ultimos if ultimos else n * 8
        if n == 0:
            n = 1
        if n > 16:
            n = 16
        for _ in range(n):
            recibido.append(self._leer(0x09))
        return estado, recibido, bits

    def pedir(self):
        """Pregunta si hay una tarjeta cerca. Regresa True/False."""
        self._escribir(0x0D, 0x07)          # el REQA usa solo 7 bits
        estado, _, bits = self._a_tarjeta([self.PEDIR_TARJETA])
        return estado == self.OK and bits == 0x10

    def anticolision(self):
        """Lee los 4 bytes del UID. Regresa la lista o None."""
        self._escribir(0x0D, 0x00)
        estado, recibido, _ = self._a_tarjeta([0x93, 0x20])
        if estado != self.OK or len(recibido) != 5:
            return None
        verificador = 0
        for b in recibido[:4]:
            verificador ^= b
        if verificador != recibido[4]:
            return None
        return recibido[:4]

    def leer_uid(self):
        """Regresa el UID como texto ("A1B2C3D4") o None si no hay tarjeta."""
        if not self.pedir():
            return None
        uid = self.anticolision()
        if uid is None:
            return None
        return "".join("{:02X}".format(b) for b in uid)
