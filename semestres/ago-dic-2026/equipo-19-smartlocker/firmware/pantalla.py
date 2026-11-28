# ============================================================
# pantalla.py - Pantalla OLED SSD1306 128x64
# ============================================================

from machine import SoftI2C, Pin
import ssd1306
import configuracion


class Pantalla:
    def __init__(self):
        i2c = SoftI2C(
            scl=Pin(configuracion.OLED_SCL),
            sda=Pin(configuracion.OLED_SDA),
            freq=400000
        )
        self.oled = ssd1306.SSD1306_I2C(128, 64, i2c)

    def dibujar(self, estado, entrada, temp, hum, dist):
        self.oled.fill(0)
        self.oled.text("SmartLocker", 20, 0)
        self.oled.text("------------", 0, 10)
        self.oled.text("Estado: " + estado, 0, 22)
        self.oled.text("PIN: " + ("*" * len(entrada)), 0, 34)
        self.oled.text("T:{:.0f}C H:{:.0f}%".format(temp, hum), 0, 46)
        if dist >= 0:
            self.oled.text("D:{:.0f}cm".format(dist), 0, 56)
        else:
            self.oled.text("D: --", 0, 56)
        self.oled.show()
