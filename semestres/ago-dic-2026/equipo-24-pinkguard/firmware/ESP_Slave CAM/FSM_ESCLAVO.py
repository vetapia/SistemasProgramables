# ============================================
# Proyecto:  Pink Ward Sentinel
# Archivo:   FSM_ESCLAVO.py
# Objetivo:  Implementar la Máquina de Estados Finitos (FSM) para controlar la captura, procesamiento y envío de imágenes de la cámara
# Equipo:    Montoya Chávez Ángel Eduardo
#            Rios López Jeremhy Damián
#            Torres Romero Yóscar Yemmen
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import camera
import time
import struct
import os
from machine import Pin

class FSM_Camara:
    ESTADO_BOOTEO = "BOOTEO"
    ESTADO_ESPERA = "ESPERA"
    ESTADO_CAPTURA_POSTEO = "CAPTURA_POSTEO"

    def __init__(self, mqtt_manager, pin_recepcion=13):
        self.mqtt = mqtt_manager
        self.gpio_recibo = Pin(pin_recepcion, Pin.IN, Pin.PULL_DOWN)
        self.estado_actual = self.ESTADO_BOOTEO
        print(f"[FSM-CAM] Sistema arrancó en estado: {self.estado_actual}")

    def transicionar(self, nuevo_estado):
        print(f"\n[FSM-CAM] Transicionando: [{self.estado_actual}] ---> [{nuevo_estado}]")
        self.estado_actual = nuevo_estado

    def _obtener_y_actualizar_contador(self):
        # Intentar leer el contador existente
        try:
            with open("/contador.txt", "r") as f:
                numero = int(f.read().strip())
        except OSError:
            # Si el archivo no existe (primer uso), iniciamos en 1
            numero = 1
        
        # Guardar el siguiente número
        with open("/contador.txt", "w") as f:
            f.write(str(numero + 1))
            
        return numero

    def actualizar(self):
        if self.estado_actual == self.ESTADO_BOOTEO:
            try:
                camera.deinit()
            except Exception:
                pass
            
            try:
                camera.init(
                    0, d0=4, d1=5, d2=18, d3=19, d4=36, d5=39, d6=34, d7=35,
                    format=camera.RGB565, framesize=camera.FRAME_QQVGA,
                    xclk_freq=camera.XCLK_10MHz, href=23, vsync=25,
                    reset=-1, pwdn=-1, sioc=27, siod=26, xclk=21, pclk=22
                )
                print("[BOOTEO] ¡Cámara inicializada!")
            except Exception as e:
                print("[BOOTEO] Fallo al inicializar:", e)

            self.transicionar(self.ESTADO_ESPERA)

        elif self.estado_actual == self.ESTADO_ESPERA:
            if self.gpio_recibo.value() == 1:
                self.transicionar(self.ESTADO_CAPTURA_POSTEO)
            else:
                time.sleep(0.1) 

        elif self.estado_actual == self.ESTADO_CAPTURA_POSTEO:
            print("[CAPTURA] Extrayendo frame de la cámara...")
            frame = camera.capture()
            
            if frame:
                num_foto = self._obtener_y_actualizar_contador()
                nombre_archivo = f"/ft{num_foto}.bmp"
                
                # 1. Escribir el archivo físicamente en la memoria del ESP32
                self._guardar_bmp_en_flash(frame, nombre_archivo)
                
                # 2. Enviar la ruta del archivo al hilo MQTT
                self.mqtt.postear_archivo_async("pinkguard/camara/foto", nombre_archivo)
            else:
                print("[CAPTURA] Error: Buffer de cámara vacío.")
            
            while self.gpio_recibo.value() == 1:
                time.sleep(0.05)
            
            self.transicionar(self.ESTADO_ESPERA)

    def _guardar_bmp_en_flash(self, frame, ruta):
        width = 160
        height = 120
        row_size = width * 3
        pixel_data_size = row_size * height
        file_size = 54 + pixel_data_size

        bmp_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
        dib_header = struct.pack('<IiiHHIIIIII', 40, width, -height, 1, 24, 0, pixel_data_size, 2835, 2835, 0, 0)
        bmp_pixels = bytearray(pixel_data_size)
        
        idx = 0
        for i in range(0, len(frame), 2):
            pixel = (frame[i] << 8) | frame[i + 1]
            r = ((pixel >> 11) & 0x1F) << 3
            g = ((pixel >> 5) & 0x3F) << 2
            b = (pixel & 0x1F) << 3
            bmp_pixels[idx] = b
            bmp_pixels[idx + 1] = g
            bmp_pixels[idx + 2] = r
            idx += 3

        # Escribimos los 3 bloques directamente en el almacenamiento interno
        print(f"[CAPTURA] Guardando archivo temporal: {ruta}")
        with open(ruta, "wb") as f:
            f.write(bmp_header)
            f.write(dib_header)
            f.write(bmp_pixels)