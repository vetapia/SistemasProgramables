# ============================================
# Proyecto:  AuraBot
# Archivo:   comunicacion.py
# Objetivo:  Manejar red WiFi y cliente MQTT (incluye Last Will)
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import network
import time
from umqtt.simple import MQTTClient
import config

# Tópicos
T_NODO = b"aurabot/actuador/nodo/central"

def conectar_wifi():
    estacion = network.WLAN(network.STA_IF)
    estacion.active(True)
    estacion.connect(config.WIFI_SSID, config.WIFI_CLAVE)
    print("Conectando a WiFi...")
    
    inicio = time.ticks_ms()
    while not estacion.isconnected():
        if time.ticks_diff(time.ticks_ms(), inicio) > 15000:
            print("Error: Timeout WiFi")
            return False
        time.sleep(0.5)
    print("WiFi conectado. IP:", estacion.ifconfig()[0])
    return True

def iniciar_mqtt(callback_recepcion):
    cliente = MQTTClient(
        client_id="aurabot_central", 
        server=config.IP_BROKER, 
        user=config.USUARIO_MQTT, 
        password=config.CLAVE_MQTT,
        keepalive=30
    )
    cliente.set_callback(callback_recepcion)
    
    # Last Will and Testament (LWT)
    cliente.set_last_will(T_NODO, b"offline", retain=True, qos=1)
    
    try:
        cliente.connect()
        # Publicar estado en línea
        cliente.publish(T_NODO, b"online", retain=True, qos=1)
        
        # Suscripciones
        cliente.subscribe(b"aurabot/comando/servo/central")
        cliente.subscribe(b"aurabot/comando/relevador/central")
        cliente.subscribe(b"aurabot/comando/oled/central")
        print("MQTT conectado y suscrito.")
        return cliente
    except Exception as e:
        print("Fallo MQTT:", e)
        return None