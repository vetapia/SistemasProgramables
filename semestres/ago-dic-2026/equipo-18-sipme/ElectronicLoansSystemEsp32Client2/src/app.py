from network_manager import NetworkManager
from mqtt_manager import MQQTTManager
import constants
from machine import Pin
from servo_manager import ServoManager
import time

class App:
    def __init__(self):
        self._network_manager = NetworkManager("israel", "12345678")
        self._servo = ServoManager(19)

    def _init_mqtt(self):
        self._mqtt = MQQTTManager("esp-buckets", constants.mqtt_broker, self._network_manager)
        self._mqtt.connect()
        self._mqtt.set_callback(self._mqtt_callback)
        self._mqtt.suscribe(b"/buckets")

    def _init_components(self):
        self._network_manager.connect()
        self._init_mqtt()

    def _mqtt_callback(self, topic, msg):
        if(topic == b"/buckets"):
            if msg == b"/1/open":
                self._servo.update_deg(180)
            elif msg == b"/1/close":
                self._servo.update_deg(0)

    def start(self):
        try:
            self._init_components()
        except Exception as e:
            raise e

        while True:
            self._mqtt.check_msg()
            time.sleep(0.1)
