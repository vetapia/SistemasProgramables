from network_manager import NetworkManager
from auth_service import AuthService
from display_manager import DisplayManager
from spi_manager import SpiManager
from keypad_manager import KeyPadManager
from keypad_state import KeyPadState
from bucket_state import BucketState 
from nfc_manager import NfcManager
from i2c_manager import I2CManager
from mqtt_manager import MQQTTManager
import asyncio
import constants

class App:
    def __init__(self):
        self._network = NetworkManager("israel", "12345678")
        self._auth_service = AuthService()
        self._spi = SpiManager(2, 18,23)
        self._display = DisplayManager(self._spi.get_spi(), 2, 4, 5)
        self._keypad = KeyPadManager([26,25,33,32], [13,12,14,27])
        self._i2c = I2CManager(22, 21)
        self._nfc = NfcManager(self._i2c.get_i2c())
        self._state = 0

    def _init_mqtt(self):
        self._mqtt = MQQTTManager("esp-main", constants.mqtt_broker, self._network)
        self._mqtt.connect() 

    def _init_components(self):
        self._network.connect()
        self._display.init_display(1)
        self._display.clean()
        self._init_mqtt()

    def main(self):
        try:
            self._init_components()
            asyncio.run(self._main_async())            
        except Exception as e:
            raise e

    async def _main_async(self):
        nfc_task = asyncio.create_task(
            self._nfc.start(self._nfc_callback, lambda e: print(f"Hola {e}"))
        )

        try:
            while True:
                if(self._state == 0):
                    await self._login_with_keypad()
                elif(self._state == 1):
                    self._select_bucket()
                elif(self._state == 2):
                    pass
                else:
                    return
        except Exception as e:
            raise e

    def _nfc_callback(self, contro_number, pin):
        print("Hola")
        self._auth_service.loginWithNumberAndPin(contro_number, pin)
        if self._auth_service.isAuth():
            self._state = 1
        else:
            self._state = 0

    def _select_bucket(self):
        self._display.clean()
        bucket_state = BucketState(self._auth_service, self._display, self._keypad, self._mqtt)
        bucket_state.start()
        self._state = 2

    async def _login_with_keypad(self):
        self._display.clean()
        keypad_state = KeyPadState(self._keypad, self._auth_service, self._display)
        await keypad_state.start()
        self._state = 1
        print(self._auth_service._user)