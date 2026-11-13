# ============================================
# Proyecto:  SafeDrop
# Archivo:   ldr_mqtt.py
# Objetivo:  Leer el nivel de luz con LDR y publicar valores por MQTT.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import network
import time
from machine import Pin, ADC
from umqtt.simple import MQTTClient
from config import WIFI_SSID, WIFI_PASSWORD, BROKER_IP

# Modulo LDR LM393 de cuatro pines:
# VCC -> 3V3, GND -> GND, AO -> GPIO34; DO sin conectar.
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

TOPICO = b"safedrop/sensores/ldr"


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        for intento in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)

    if not wlan.isconnected():
        raise RuntimeError("Sin conexion WiFi")

    print("WiFi conectado:", wlan.ifconfig()[0])


def iniciar():
    conectar_wifi()

    cliente = MQTTClient(
        b"safedrop_ldr",
        BROKER_IP,
        port=1883,
        keepalive=60
    )

    cliente.connect()
    print("MQTT conectado")

    try:
        while True:
            valor = ldr.read()
            cliente.publish(TOPICO, str(valor))
            print("Luz ambiental:", valor)
            time.sleep(2)
    finally:
        cliente.disconnect()


iniciar()
