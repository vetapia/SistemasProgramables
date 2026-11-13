# ============================================
# Proyecto:  SafeDrop
# Archivo:   ultrasonico_mqtt.py
# Objetivo:  Medir distancia con HC-SR04 y publicar centimetros por MQTT.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import network
import time
from machine import Pin, time_pulse_us
from umqtt.simple import MQTTClient
from config import WIFI_SSID, WIFI_PASSWORD, BROKER_IP

# IMPORTANTE: ECHO del HC-SR04 alimentado a 5V debe reducirse
# a 3.3V o menos usando un divisor de voltaje apropiado.
trig = Pin(18, Pin.OUT)
echo = Pin(19, Pin.IN)

TOPICO = b"safedrop/sensores/distancia"


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


def medir_distancia():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    duracion = time_pulse_us(echo, 1, 30000)
    if duracion <= 0:
        return None

    return round(duracion / 58.0, 2)


def iniciar():
    conectar_wifi()
    cliente = MQTTClient(
        b"safedrop_ultrasonico",
        BROKER_IP,
        port=1883,
        keepalive=60
    )
    cliente.connect()
    print("MQTT conectado")

    try:
        while True:
            distancia = medir_distancia()
            if distancia is not None:
                cliente.publish(TOPICO, str(distancia))
                print("Distancia:", distancia, "cm")
            else:
                print("Sin lectura valida")
            time.sleep(2)
    finally:
        cliente.disconnect()


iniciar()
