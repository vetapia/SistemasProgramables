"""Administra la conexión Wi-Fi del ESP32 mediante MicroPython."""

import network
import time

class NetworkManager:
    """Configura una interfaz de red y establece su conexión Wi-Fi."""

    def __init__(self, siid: str, password: str, mode: int = network.STA_IF):
        """Guarda las credenciales y activa la interfaz indicada.

        El modo normalmente corresponde a network.STA_IF cuando el ESP32 debe
        conectarse a un punto de acceso existente.
        """
        self._SIID = siid
        self._PASSWORD = password
        self._MODE = mode
        self._initilize_default_config()

    def _initilize_default_config(self):
        """Crea y activa la interfaz WLAN antes de intentar conectarla."""
        self._wifi = network.WLAN(self._MODE)
        self._wifi.active(False)
        time.sleep(1)
        self._wifi.active(True)

    def connect(self):
        """Conecta la interfaz en modo estación y muestra la IP asignada.

        Se realizan hasta veinte comprobaciones, separadas por un segundo. Si
        no se obtiene conexión, se genera OSError para que el programa
        principal pueda manejar el fallo.
        """
        if self._MODE == network.STA_IF:
            self._wifi.connect(self._SIID, self._PASSWORD)

            count = 20
            while not self._wifi.isconnected() and count > 0:
                count-=1
                time.sleep(1)
    
            if not self._wifi.isconnected():
                raise OSError("Wifi not exist or bad credrentials")

        print(self._wifi.ifconfig()[0])
        
    def isConnected(self):
        """Indica si la interfaz Wi-Fi se encuentra conectada."""
        return self._wifi.isconnected()
