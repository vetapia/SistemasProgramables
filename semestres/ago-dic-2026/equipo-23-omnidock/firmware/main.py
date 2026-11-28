import network
import time
import ujson
from umqtt.simple import MQTTClient
from dispositivos import SensorMoneda, ServoPuerta

WIFI_SSID = "Israel"
WIFI_PASS = "12345678"
MQTT_BROKER = "broker.hivemq.com"
CLIENT_ID = "ESP32_OmniVault_Prod"

TOPIC_MONEDA = b"omnivault/sensor/moneda"
TOPIC_PUERTA = b"omnivault/actuador/puerta/cmd"

sensor = SensorMoneda(13)
puerta = ServoPuerta(2)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a red Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Red establecida. IP:", wlan.ifconfig()[0])

def callback_comandos(topic, msg):
    print("Comando recibido en", topic.decode(), "->", msg.decode())
    if topic == TOPIC_PUERTA:
        if msg == b"OPEN":
            puerta.abrir()
            print(">> Puerta ABIERTA")
        elif msg == b"CLOSE":
            puerta.cerrar()
            print(">> Puerta CERRADA")

def main():
    conectar_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(callback_comandos)
    client.connect()
    client.subscribe(TOPIC_PUERTA)
    print("Firmware OmniVault V1 en ejecución...")

    while True:
        try:
            client.check_msg()
            if sensor.detectado():
                print(">> Evento: Moneda ingresada")
                payload = ujson.dumps({"estado": 0, "timestamp": time.ticks_ms()})
                client.publish(TOPIC_MONEDA, payload.encode())
            time.sleep(0.05)
        except OSError as e:
            print("Error de conexión MQTT, reiniciando...", e)
            time.sleep(2)
            import machine
            machine.reset()

if __name__ == "__main__":
    main()