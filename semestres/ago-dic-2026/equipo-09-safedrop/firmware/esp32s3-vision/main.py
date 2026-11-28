# ============================================
# Proyecto:  SafeDrop
# Archivo:   main.py
# Objetivo:  Capturar imagen RGB565 desde OV3660 y enviarla al servidor TCP.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import network
import socket
import camera
import struct
import time

# --- CONFIGURACIÓN DE RED ---
from config import WIFI_SSID, WIFI_PASSWORD, SERVER_IP, SERVER_PORT

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a red WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
    print('WiFi Conectado. IP:', wlan.ifconfig()[0])

def tomar_y_enviar_foto():
    cam = camera.Camera()
    
    print("Esperando 5 segundos antes de tomar la foto...")
    # time.sleep(5)

    # --- INTENTO DE CAMBIO DE RESOLUCIÓN ---
    try:
        cam.framesize = 8
    except Exception as e:
        print("Aviso: No se pudo usar cam.framesize =", e)

    time.sleep(1)

    ancho = cam.get_pixel_width()
    alto = cam.get_pixel_height()
    foto = cam.capture()
    
    if foto is None:
        print("No se recibió imagen del sensor")
        cam.deinit()
        return

    print(f"📸 Resolución capturada: {ancho} x {alto}")
    
    datos = bytes(foto)
    cam.free_buffer()
    cam.deinit()

    # --- TRANSMISIÓN SÚPER RÁPIDA ---
    print(f"Conectando al Servidor IA en {SERVER_IP}:{SERVER_PORT}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        
        # 1. Enviamos un "Header" (Cabecera) de 8 bytes indicando Ancho y Alto
        s.sendall(struct.pack("<II", ancho, alto))
        
        # 2. Enviamos todos los píxeles crudos de golpe (Cero procesamiento)
        s.sendall(datos)
        
        s.close()
        print("¡Bytes RAW enviados con éxito a la PC!")
    except Exception as e:
        print("Error al enviar. ¿Está el servidor Python encendido?", e)

# Ejecución
conectar_wifi()
tomar_y_enviar_foto()