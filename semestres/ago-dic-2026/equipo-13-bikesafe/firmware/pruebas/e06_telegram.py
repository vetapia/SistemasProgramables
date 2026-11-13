# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e06_telegram.py
# Objetivo:  Probar que la Freenove puede mandar un mensaje al bot de Telegram (se corre en la FREENOVE)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# ANTES: sube config.py y telegram.py a la Freenove y llena en
# config.py el WiFi, TELEGRAM_TOKEN y TELEGRAM_CHAT_ID.
#
# QUE DEBES VER: "Mensaje enviado: True" y el mensaje en tu Telegram.
#   False -> el token o el chat_id estan mal, o no le has escrito
#            "hola" a tu bot desde tu cuenta (es obligatorio la 1a vez).
#   OSError -> la red no tiene internet o bloquea Telegram.

import time
import network
import config as cfg
import telegram

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Conectando a", cfg.WIFI_SSID)
    wlan.disconnect()
    time.sleep(1)
    wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
    for _ in range(60):
        if wlan.isconnected():
            break
        time.sleep(0.25)
print("WiFi conectado:", wlan.isconnected(), wlan.ifconfig()[0])

bien = telegram.enviar_mensaje(cfg.TELEGRAM_TOKEN, cfg.TELEGRAM_CHAT_ID,
                               "Hola, soy BikeSafe. La prueba funciono.")
print("Mensaje enviado:", bien)
