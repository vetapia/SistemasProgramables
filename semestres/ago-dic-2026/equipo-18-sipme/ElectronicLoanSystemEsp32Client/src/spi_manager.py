from machine import SPI, Pin

class SpiManager:
    def __init__(self, a0: int, sck: int, mosi: int):
        self._spi = SPI(
            a0,
            baudrate=20000000,
            polarity=0,
            phase=0,
            sck=Pin(sck),
            mosi=Pin(mosi)
        )

    def get_spi(self):
        return self._spi