# ============================================
# Proyecto:  Pink Ward Sentinel
# Archivo:   Comunicacion_MQTT_cam.py
# Objetivo:  Establecer la conexión Wi-Fi y la publicación de datos hacia el broker MQTT (Cámara)
# Equipo:    Montoya Chávez Ángel Eduardo
#            Rios López Jeremhy Damián
#            Torres Romero Yóscar Yemmen
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import network
from umqtt.simple import MQTTClient
import time
import _thread
import os

class Comunicacion_MQTT_Cam:
    def __init__(self, ssid, password, broker_ip, client_id="esp32_esclavo_cam"):
        self.ssid = ssid
        self.password = password
        self.broker_ip = broker_ip
        self.client_id = client_id
        self.client = None
        self.publicando = False

    def conectar_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print(f"[MQTT] Conectando a Wi-Fi: {self.ssid}...")
            wlan.connect(self.ssid, self.password)
            intentos = 0
            while not wlan.isconnected() and intentos < 20:
                time.sleep(0.5)
                intentos += 1
        return wlan.isconnected()

    def iniciar_comunicacion(self):
        try:
            if not self.conectar_wifi():
                return False
            self.client = MQTTClient(self.client_id, self.broker_ip)
            self.client.connect()
            print("[MQTT] ¡Broker conectado!")
            return True
        except Exception as e:
            print("[MQTT] Error crítico en conexión:", e)
            return False

    def _tarea_publicacion(self, topico, ruta_archivo):
        self.publicando = True
        try:
            if self.client:
                # 1. Leer el archivo desde la memoria flash
                with open(ruta_archivo, "rb") as f:
                    datos = f.read()
                
                # 2. Publicar (umqtt arroja excepción si falla la conexión)
                self.client.publish(topico, datos)
                print(f"\n[MQTT-HILO] ¡Publicado en {topico}! Eliminando {ruta_archivo}...")
                
                # 3. Eliminar el archivo solo si el envío fue exitoso
                os.remove(ruta_archivo)
            else:
                print("\n[MQTT-HILO] Error: Cliente no inicializado.")
        except OSError as e:
            print(f"\n[MQTT-HILO] Error de archivo o red al procesar {ruta_archivo}:", e)
        except Exception as e:
            print(f"\n[MQTT-HILO] Error inesperado:", e)
        finally:
            self.publicando = False

    def postear_archivo_async(self, topico, ruta_archivo):
        if self.publicando:
            print("[MQTT] Publicación en curso. Ignorando este disparo para evitar cruce de hilos.")
            return False
            
        print(f"[MQTT] Despachando lectura y envío de {ruta_archivo} al hilo secundario...")
        _thread.start_new_thread(self._tarea_publicacion, (topico, ruta_archivo))
        return True