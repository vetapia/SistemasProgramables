# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Detección y Control de Plagas
# Archivo:   main.py
# Objetivo:  Lectura de sensores, suscripción MQTT y control de motores y atomizador
# Equipo:    Mónica Moreno Torres [23241119], Leonardo Gael Niño Cabrera [MATRÍCULA]
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import network
import time
import json
from machine import Pin
from umqtt.simple import MQTTClient

WIFI_SSID = "TU_RED_WIFI"
WIFI_PASS = "TU_PASSWORD"
MQTT_BROKER = "broker.hivemq.com"
CLIENT_ID = "esp32_meowguard_carrito"
TOPIC_SUB = b"tecnm/leon/meowguard/alertas"
TOPIC_PUB = b"tecnm/leon/meowguard/telemetria"

# Actuadores (Ajustar según Tabla HAL)
atomizador = Pin(25, Pin.OUT)
motor_izq = Pin(26, Pin.OUT)
motor_der = Pin(27, Pin.OUT)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("WiFi conectado:", wlan.ifconfig()[0])

def callback_mqtt(topic, msg):
    data = json.loads(msg.decode())
    print("Alerta recibida:", data)
    if data.get("activarAtomizador"):
        atomizador.value(1)
        time.sleep(2)
        atomizador.value(0)

conectar_wifi()
client = MQTTClient(CLIENT_ID, MQTT_BROKER)
client.set_callback(callback_mqtt)
client.connect()
client.subscribe(TOPIC_SUB)
print("ESP32 suscrito a:", TOPIC_SUB)

while True:
    client.check_msg()
    time.sleep(0.1)
