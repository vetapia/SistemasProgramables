
# nec.py Decoder for IR remote control using synchronous code
# Supports NEC and Samsung protocols.

# Author: Peter Hinch
# Copyright Peter Hinch 2020-2022 Released under the MIT license

from utime import ticks_us, ticks_diff
from ir_rx import IR_RX

class NEC_ABC(IR_RX):
    def __init__(self, pin, extended, samsung, callback, *args):
        super().__init__(pin, 68, 80, callback, *args)
        self._extended = extended
        self._addr = 0
        self._leader = 2500 if samsung else 4000

    def decode(self, _):
        try:
            if self.edge > 68:
                raise RuntimeError(self.OVERRUN)
            width = ticks_diff(self._times[1], self._times[0])
            if width < self._leader:
                raise RuntimeError(self.BADSTART)
            width = ticks_diff(self._times[2], self._times[1])
            if width > 3000:
                if self.edge < 68:
                    raise RuntimeError(self.BADBLOCK)
                val = 0
                for edge in range(3, 68 - 2, 2):
                    val >>= 1
                    if ticks_diff(self._times[edge + 1], self._times[edge]) > 1120:
                        val |= 0x80000000
            elif width > 1700:
                raise RuntimeError(self.REPEAT if self.edge == 4 else self.BADREP)
            else:
                raise RuntimeError(self.BADSTART)
            addr = val & 0xff
            cmd = (val >> 16) & 0xff
            if cmd != (val >> 24) ^ 0xff:
                raise RuntimeError(self.BADDATA)
            if addr != ((val >> 8) ^ 0xff) & 0xff:
                if not self._extended:
                    raise RuntimeError(self.BADADDR)
                addr |= val & 0xff00
            self._addr = addr
        except RuntimeError as e:
            cmd = e.args[0]
            addr = self._addr if cmd == self.REPEAT else 0
        self.do_callback(cmd, addr, 0, self.REPEAT)

class NEC_8(NEC_ABC):
    def __init__(self, pin, callback, *args):
        super().__init__(pin, False, False, callback, *args)

class NEC_16(NEC_ABC):
    def __init__(self, pin, callback, *args):
        super().__init__(pin, True, False, callback, *args)

class SAMSUNG(NEC_ABC):
    def __init__(self, pin, callback, *args):
        super().__init__(pin, True, True, callback, *args)
