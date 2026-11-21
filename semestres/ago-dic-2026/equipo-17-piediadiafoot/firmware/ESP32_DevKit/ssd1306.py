"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   ssd1306.py
 Objetivo:  Mantiene un framebuffer MONO_VLSB, envía comandos y datos por SPI y actualiza la memoria
              de la pantalla mediante show()
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |  
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import framebuf
import time

class SSD1306_SPI:
    def __init__(self, width, height, spi, dc, res, cs):
        self.width, self.height = width, height
        self.spi, self.dc, self.res, self.cs = spi, dc, res, cs
        self.buffer = bytearray(width * height // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, framebuf.MONO_VLSB)
        self.res.value(0); time.sleep_ms(10); self.res.value(1); time.sleep_ms(10)
        for cmd in (0xAE, 0x20, 0x00, 0x40, 0xA1, 0xC8, 0xA8, height - 1,
                    0xD3, 0x00, 0xDA, 0x12, 0xD5, 0x80, 0xD9, 0xF1,
                    0xDB, 0x30, 0x81, 0x7F, 0xA4, 0xA6, 0x8D, 0x14, 0xAF):
            self._cmd(cmd)
        self.fill(0)
        self.show()

    def _cmd(self, cmd):
        self.cs.value(0); self.dc.value(0); self.spi.write(bytes((cmd,))); self.cs.value(1)

    def _data(self, data):
        self.cs.value(0); self.dc.value(1); self.spi.write(data); self.cs.value(1)

    def fill(self, color): self.fb.fill(color)
    def text(self, text, x, y, color=1): self.fb.text(str(text), x, y, color)
    def pixel(self, x, y, color): self.fb.pixel(x, y, color)

    def show(self):
        self._cmd(0x21); self._cmd(0); self._cmd(self.width - 1)
        self._cmd(0x22); self._cmd(0); self._cmd((self.height // 8) - 1)
        self._data(self.buffer)
