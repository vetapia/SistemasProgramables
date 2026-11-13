# ============================================
# Proyecto:  SafeDrop
# Archivo:   servo_mqtt.py
# Objetivo:  Controlar apertura y cierre del servomotor SG90 por MQTT.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import network
import time
from machine import Pin, PWM
from umqtt.simple import MQTTClient

from config import WIFI_SSID, WIFI_PASSWORD, BROKER_IP

# Alimentar el SG90 desde una fuente apropiada, con GND comun.
# Verificar capacidad de corriente y caidas de tension antes
# de instalar el mecanismo de bloqueo.
servo = PWM(Pin(23), freq=50)

TOPICO = b"safedrop/puerta/cmd"
CERRADO = 0
ABIERTO = 90


def mover(angulo):
    # Rango inicial de pulsos: 1000-2000 us, a 50 Hz.
    # Calibrar limites mecanicos antes de instalar.
    pulso = 1000000 + int(angulo * 1000000 / 180)
    servo.duty_ns(pulso)
    print("Servo en:", angulo, "grados")


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
    if topico != TOPICO:
        return

    if mensaje == b"ABRIR":
        print("Abriendo SafeDrop")
        mover(ABIERTO)

    elif mensaje == b"CERRAR":
        print("Cerrando SafeDrop")
        mover(CERRADO)


def iniciar():
    cliente = None
    try:
        mover(CERRADO)
        conectar_wifi()

        cliente = MQTTClient(
            b"safedrop_servo",
            BROKER_IP,
            port=1883,
            keepalive=60
        )

        cliente.set_callback(recibir_mensaje)
        cliente.connect()
        cliente.subscribe(TOPICO)

        print("MQTT conectado")
        print("Esperando ABRIR o CERRAR...")

        while True:
            cliente.check_msg()
            time.sleep_ms(100)

    finally:
        # Mantener el PWM desactivado al salir de la prueba.
        servo.deinit()
        if cliente is not None:
            cliente.disconnect()


iniciar()
