"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   lcd1602.py
 Objetivo:  Inicializar el LCD en modo de 4 bits y escribir caracteres
            (Driver para LCD 1602 con adaptador I2C PCF8574 de mapeo común.)
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 | 
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import time

class LCD1602:
    RS = 0x01
    EN = 0x04
    BL = 0x08

    def __init__(self, i2c, addr, cols=16, rows=2):
        self.i2c, self.addr = i2c, addr
        self.cols, self.rows = cols, rows
        self.backlight = self.BL
        time.sleep_ms(50)
        self._nibble(0x03, 0); time.sleep_ms(5)
        self._nibble(0x03, 0); time.sleep_us(150)
        self._nibble(0x03, 0)
        self._nibble(0x02, 0)
        self.command(0x28)
        self.command(0x0C)
        self.command(0x06)
        self.clear()

    def _expander(self, value):
        self.i2c.writeto(self.addr, bytes((value | self.backlight,)))

    def _pulse(self, value):
        self._expander(value | self.EN)
        time.sleep_us(1)
        self._expander(value & ~self.EN)
        time.sleep_us(50)

    def _nibble(self, nibble, is_data):
        value = (nibble & 0x0F) << 4
        if is_data:
            value |= self.RS
        self._expander(value)
        self._pulse(value)

    def _send(self, value, is_data):
        self._nibble(value >> 4, is_data)
        self._nibble(value & 0x0F, is_data)

    def command(self, value):
        self._send(value, 0)
        if value in (0x01, 0x02):
            time.sleep_ms(2)

    def write_char(self, char):
        self._send(ord(char), 1)

    def clear(self):
        self.command(0x01)

    def move_to(self, col, row):
        offsets = (0x00, 0x40, 0x14, 0x54)
        self.command(0x80 | (col + offsets[row % self.rows]))

    def putstr(self, text):
        for char in str(text):
            if char != "\n":
                self.write_char(char if ord(char) < 128 else "?")

    def display(self, line1="", line2=""):
        self.clear()
        self.move_to(0, 0)
        self.putstr(str(line1)[:self.cols])
        self.move_to(0, 1)
        self.putstr(str(line2)[:self.cols])
