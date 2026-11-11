"""Proporciona una interfaz sencilla para la comunicación mediante MQTT."""

from mqtt_lib import MQTTClient
from network_manager import NetworkManager

class MQQTTManager:
    """Gestiona un cliente MQTT que depende de una conexión Wi-Fi activa."""

    def __init__(self, client: str, broker: str, nm: NetworkManager):
        """Configura el cliente para conectarse al broker por el puerto 1883.

        La construcción se detiene con OSError si el administrador de red
        informa que el ESP32 todavía no está conectado.
        """
        if not nm.isConnected():
            raise OSError("Not connected to wifi is necesaraly for connect to pull")

        self._client = client
        self._broker = broker
        self._mqqt_client = MQTTClient(client, broker, 1883)

    def set_callback(self, callback):
        """Registra la función que recibirá los mensajes publicados."""
        self._callback = callback
        self._mqqt_client.set_callback(self._callback)

    def suscribe(self, topic: bytes):
        """Suscribe el cliente al tema MQTT recibido en formato bytes."""
        self._mqqt_client.subscribe(topic)

    def connect(self):
        """Abre la conexión con el broker configurado."""
        self._mqqt_client.connect()

    def check_msg(self):
        """Comprueba de forma no bloqueante si existe un mensaje pendiente."""
        self._mqqt_client.check_msg()
