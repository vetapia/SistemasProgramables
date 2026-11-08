# ============================================
# Proyecto:  SmartClass
# Archivo:   Main.py
# Objetivo:  Funcionalidad de 3 sensores y 3 actuadores
# Equipo:    Juan Daniel Torres Uribe -23240326, Aldo Emmanuel Carrillo Gomez -23240343
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import machine
import time
import dht
import network
from umqtt.simple import MQTTClient
from hcsr04 import HCSR04 # Asegúrate de instalar esta librería en Thonny

# --- CONFIGURACIÓN RED Y MQTT ---
WIFI_SSID = "Redmi Note 11S"
WIFI_PASS = "1234abc$"
MQTT_BROKER = "broker.emqx.io" # Broker público para pruebas del Sprint 1
CLIENT_ID = "SmartClass_ESP32_01"

# --- DEFINICIÓN DE PINES (HAL) ---
# Sensores
sensor_ir = machine.Pin(13, machine.Pin.IN)
sensor_dht = dht.DHT11(machine.Pin(4))
sensor_dist = HCSR04(trigger_pin=32, echo_pin=35)

# Actuadores
bomba_gel = machine.Pin(25, machine.Pin.OUT)
buzzer = machine.Pin(26, machine.Pin.OUT)
ventilador = machine.Pin(27, machine.Pin.OUT)

# Apagar actuadores al inicio
bomba_gel.value(0)
buzzer.value(0)
ventilador.value(0)

# --- FUNCIÓN PARA RECIBIR COMANDOS MQTT (SUSCRIPCIÓN) ---
def mqtt_callback(topic, msg):
    print("Comando recibido en {}: {}".format(topic, msg))
    
    if topic == b'smartclass/a/bomba':
        bomba_gel.value(1 if msg == b'1' else 0)
    elif topic == b'smartclass/a/buzzer':
        buzzer.value(1 if msg == b'1' else 0)
    elif topic == b'smartclass/a/vent':
        ventilador.value(1 if msg == b'1' else 0)

# --- CONEXIÓN WIFI ---
print("Conectando a WiFi...", end="")
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)
while not wifi.isconnected():
    time.sleep(0.5)
    print(".", end="")
print("\nWiFi Conectado! IP:", wifi.ifconfig()[0])

# --- CONEXIÓN MQTT ---
client = MQTTClient(CLIENT_ID, MQTT_BROKER)
client.set_callback(mqtt_callback)
client.connect()
# Suscribirse a actuadores
client.subscribe(b"smartclass/a/bomba")
client.subscribe(b"smartclass/a/buzzer")
client.subscribe(b"smartclass/a/vent")
print("Conectado a MQTT y suscrito a actuadores.")

# --- BUCLE PRINCIPAL ---
ultimo_envio = time.ticks_ms()

while True:
    try:
        # Revisar si llegaron mensajes MQTT para los actuadores
        client.check_msg()
        
        # Publicar datos de sensores cada 5 segundos
        if time.ticks_diff(time.ticks_ms(), ultimo_envio) > 5000:
            # 1. Leer DHT11
            try:
                sensor_dht.measure()
                temp = sensor_dht.temperature()
                hum = sensor_dht.humidity()
                client.publish(b"smartclass/s/clima", '{{"temp":{}, "hum":{}}}'.format(temp, hum))
            except Exception as e:
                print("Error DHT11:", e)
                
            # 2. Leer Ultrasónico
            distancia = sensor_dist.distance_cm()
            client.publish(b"smartclass/s/distancia", str(distancia))
            
            # 3. Leer IR
            estado_ir = sensor_ir.value()
            client.publish(b"smartclass/s/ir", str(estado_ir))
            
            print("Datos publicados. Temp:{}C, Dist:{}cm, IR:{}".format(temp, distancia, estado_ir))
            ultimo_envio = time.ticks_ms()
            
    except Exception as e:
        print("Error en el bucle principal:", e)
        time.sleep(2)