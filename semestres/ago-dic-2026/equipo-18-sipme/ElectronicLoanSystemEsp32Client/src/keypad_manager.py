from DIYables_MicroPython_Keypad import Keypad
import constants

class KeyPadManager:
    def __init__(
            self, 
            row_pins: list[int], 
            column_pins: list[int],
            keymap: list[str] = constants.keymap,
            ):
        self._row_pins = row_pins
        self._column_pins = column_pins
        self._keymap = keymap
        self._rows = len(row_pins)
        self._columns = len(column_pins)
        self._keypad = Keypad(keymap, row_pins, column_pins, self._rows, self._columns)

    def set_deadbounce(self, deadbounce: int = 2000):
        self._keypad.set_debounce_time(deadbounce)

    def get_key(self):
        return self._keypad.get_key()