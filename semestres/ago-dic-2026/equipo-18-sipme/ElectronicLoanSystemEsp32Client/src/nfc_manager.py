from pn532 import PN532_I2C, DEFAULT_KEYA, A
from buzzer_manager import BuzzerManeger
import asyncio
import time

class NfcManager:
    def __init__(self, i2c):
        self._nfc = PN532_I2C(i2c)
        self._nfc.set_mode()
        self._buzzer = BuzzerManeger(19)

    def _red_data(self, tg, uid):
        try:
            self._nfc.mifare_classic_auth(uid, tg, DEFAULT_KEYA, A, 4)
            control_number_d = self._nfc.mifare_classic_read(tg, 4)
            control_number_str = "".join([chr(b) for b in control_number_d if b != 0])
        
            pin_d = self._nfc.mifare_classic_read(tg, 5)
            pin_str = "".join([chr(b) for b in pin_d if b != 0])

            return control_number_str, pin_str
        except Exception as e:
            raise e

    async def start(self, success, err):
        last_uid = ""
        last_time = 0

        while True:
            try:
                target = self._nfc.list_passive_target(timeout=100)
                if target:
                    self._buzzer.on()
                    current_time = time.time()
                    tg = target[0]
                    uid = target[3]
                    uid_hex = "".join([f"{b:02X}" for b in uid])

                    if last_uid != uid_hex or (current_time - last_time) > 2:
                        
                        last_uid = uid_hex
                        last_time = current_time

                        control_number, pin = self._red_data(tg, uid)
                        
                        if control_number and pin:
                            await asyncio.sleep(0.5)
                            self._buzzer.off()
                            
                            success(control_number, pin)
                
                await asyncio.sleep_ms(15)

            except Exception as e:
                await asyncio.sleep(0.5)
                self._buzzer.off()
                err(e)