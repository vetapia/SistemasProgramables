# ============================================
# Proyecto:  SafeDrop
# Archivo:   buzzer_mqtt.py
# Objetivo:  Controlar buzzer activo de 3.3 V mediante MQTT.
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

from config import WIFI_SSID, WIFI_PASSWORD, BROKER_IP

# GPIO directo solo si el consumo del buzzer se verifico
# y no supera la capacidad del pin. En caso contrario,
# utilizar una etapa de transistor adecuada.
buzzer = Pin(25, Pin.OUT)
buzzer.value(0)

TOPICO = b"safedrop/buzzer/cmd"


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


def recibir_mensaje(topico, mensaje):
    if mensaje == b"ON":
        buzzer.value(1)
        print("Buzzer encendido")

    elif mensaje == b"OFF":
        buzzer.value(0)
        print("Buzzer apagado")


def iniciar():
    conectar_wifi()

    cliente = MQTTClient(
        b"safedrop_buzzer",
        BROKER_IP,
        port=1883,
        keepalive=60
    )

    cliente.set_callback(recibir_mensaje)
    cliente.connect()
    cliente.subscribe(TOPICO)

    print("MQTT conectado")
    print("Esperando comandos ON/OFF...")

    try:
        while True:
            cliente.check_msg()
            time.sleep_ms(100)
    finally:
        buzzer.value(0)
        cliente.disconnect()


iniciar()
