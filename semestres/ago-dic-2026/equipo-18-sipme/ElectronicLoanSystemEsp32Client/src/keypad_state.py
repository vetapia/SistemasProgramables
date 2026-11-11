import asyncio

class KeyPadState:
    def __init__(self, keypad, auth_service, display):
        self._controlNumber = ""
        self._pin = ""
        self._step = 0
        self._keypad = keypad
        self._auth_service = auth_service
        self._display = display

    async def start(self):
        while True:
            if self._step == 0:
                await self._step_one()
            elif self._step == 1:
                await self._step_two()
            else:
                return

    async def _step_one(self):
        self._display.draw_login_screen("LOGIN - NO. CONTROL", "No. de Control:", self._controlNumber, is_pin=False)
        
        while True:
            key = self._keypad.get_key()
                        
            if key is not None:
                if key == "C":
                    if not self._controlNumber:
                        self._display.show_login_error("! Error:\nIngresa No. Control")
                    else:
                        self._step = 1
                        return
                elif key == "D":
                    if self._controlNumber:
                        self._controlNumber = ""
                        self._display.update_login_input(self._controlNumber, is_pin=False)
                    self._display.clear_login_error()
                elif key == "*":
                    if self._controlNumber:
                        self._controlNumber = self._controlNumber[:-1]
                        self._display.update_login_input(self._controlNumber, is_pin=False)
                        self._display.clear_login_error()
                elif key.isdigit():
                    if len(self._controlNumber) < 12:
                        self.concanete_controlNumber(key)
                        self._display.update_login_input(self._controlNumber, is_pin=False)
                        self._display.clear_login_error()
            
            await asyncio.sleep_ms(15)

    async def _step_two(self):
        self._display.draw_login_screen("LOGIN - PIN", "Ingresa tu PIN:", self._pin, is_pin=True)

        while True:
            key = self._keypad.get_key()

            if key is not None:
                if key == "C":
                    if not self._pin:
                        self._display.show_login_error("! Error:\nIngresa tu PIN")
                    else:
                        self._display.show_login_status("Validando acceso...")
                        login = self._login(self._controlNumber, self._pin)
                        if login:
                            self._step = 2
                            return
                        else:
                            self._display.show_login_error("! Error:\nCredenciales invalidas")
                            self._pin = ""
                            self._display.update_login_input(self._pin, is_pin=True)
                elif key == "D":
                    self._pin = ""
                    self._step = 0
                    return
                elif key == "*":
                    if self._pin:
                        self._pin = self._pin[:-1]
                        self._display.update_login_input(self._pin, is_pin=True)
                        self._display.clear_login_error()
                elif key.isdigit():
                    if len(self._pin) < 8:
                        self._concanete_pin(key)
                        self._display.update_login_input(self._pin, is_pin=True)
                        self._display.clear_login_error()

            await asyncio.sleep_ms(15)

    def _login(self, controlNumber, pin):
        try:
            self._auth_service.loginWithNumberAndPin(controlNumber, pin)
            return True
        except Exception:
            return False

    def concanete_controlNumber(self, newControl):
        self._controlNumber += newControl

    def _concanete_pin(self, newPin: str):
        self._pin += newPin

    def _reset(self):
        self._controlNumber = ""
        self._pin = ""
        self._step = 0
