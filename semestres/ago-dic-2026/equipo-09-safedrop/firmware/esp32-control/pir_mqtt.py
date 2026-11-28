# ============================================
# Proyecto:  SafeDrop
# Archivo:   pir_mqtt.py
# Objetivo:  Publicar por MQTT los cambios de movimiento del sensor PIR HC-SR501.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import network
import time
from machine import Pin
from umqtt.simple import MQTTClient

# Este archivo debe estar en la placa junto con config.py (privado).
from config import WIFI_SSID, WIFI_PASSWORD, BROKER_IP

pir = Pin(27, Pin.IN)
TOPICO = b"safedrop/sensores/pir"


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
        raise RuntimeError("No se conecto al WiFi")

    print("WiFi conectado:", wlan.ifconfig()[0])


def iniciar():
    conectar_wifi()

    cliente = MQTTClient(
        b"safedrop_pir",
        BROKER_IP,
        port=1883,
        keepalive=60
    )

    cliente.connect()
    print("MQTT conectado")
    print("Esperando estabilizacion del PIR...")
    time.sleep(30)

    estado_anterior = pir.value()
    cliente.publish(TOPICO, str(estado_anterior))
    print("Estado inicial:", estado_anterior)

    try:
        while True:
            estado_actual = pir.value()

            if estado_actual != estado_anterior:
                cliente.publish(TOPICO, str(estado_actual))

                if estado_actual == 1:
                    print("Movimiento detectado - MQTT: 1")
                else:
                    print("Sin movimiento - MQTT: 0")

                estado_anterior = estado_actual

            time.sleep_ms(200)
    finally:
        cliente.disconnect()


iniciar()
