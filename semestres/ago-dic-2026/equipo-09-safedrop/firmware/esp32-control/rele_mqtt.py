# Proyecto: SafeDrop
# Archivo: rele_mqtt.py
# Objetivo: Prueba del canal 1 de un modulo rele de 5V via MQTT, sin carga.
# Equipo: 09 Alan Medina Rivas 23240436
# Victor Hugo Ojeda Cabrera 23240390
# Materia: Sistemas Programables - ISC TecNM Leon
# Semestre: ago-dic-2026

import network
import time
from machine import Pin
from umqtt.simple import MQTTClient
from config import WIFI_SSID, WIFI_PASSWORD, BROKER_IP

TOPICO = b"safedrop/rele/cmd"
# Ajustar SOLO tras verificar si el modulo se activa por nivel bajo o alto.
RELE_ON = 0
RELE_OFF = 1
rele = Pin(26, Pin.OUT, value=RELE_OFF)

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    if not wlan.isconnected():
        raise RuntimeError("No se pudo conectar a WiFi")
    print("WiFi conectado:", wlan.ifconfig()[0])

def recibir_mensaje(topico, mensaje):
    print("Mensaje recibido:", mensaje)
    if topico == TOPICO and mensaje == b"ON":
        rele.value(RELE_ON)
        print("Rele activado")
    elif topico == TOPICO and mensaje == b"OFF":
        rele.value(RELE_OFF)
        print("Rele desactivado")

def iniciar_mqtt():
    cliente = MQTTClient(b"safedrop_rele_prueba", BROKER_IP, port=1883, keepalive=60)
    try:
        cliente.set_callback(recibir_mensaje)
        cliente.connect()
        cliente.subscribe(TOPICO)
        print("MQTT conectado. Esperando comandos rele...")
        while True:
            cliente.check_msg()
            time.sleep_ms(100)
    finally:
        rele.value(RELE_OFF)
        try:
            cliente.disconnect()
        except Exception:
            pass

try:
    conectar_wifi()
    iniciar_mqtt()
finally:
    rele.value(RELE_OFF)
