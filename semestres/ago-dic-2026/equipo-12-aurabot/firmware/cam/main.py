# ============================================
# Proyecto:  AuraBot — Asistente Interactivo de Escritorio
# Archivo:   main.py (Cámara — Freenove WROVER)
# Objetivo:  Capturar y publicar frames RGB565 bajo demanda por MQTT
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import network
import time
import camera
import gc
from umqtt.simple import MQTTClient
import config
from machine import Pin, I2C

T_NODO = b"aurabot/actuador/nodo/cam"
T_CAM = b"aurabot/sensor/camara/cam"
T_ESCANEAR = "aurabot/comando/ia/escanear"

enviando_fotos = False

def conectar_wifi():
    estacion = network.WLAN(network.STA_IF)
    estacion.active(True)
    estacion.connect(config.WIFI_SSID, config.WIFI_CLAVE)
    print("Conectando a WiFi...")
    inicio = time.ticks_ms()
    while not estacion.isconnected():
        if time.ticks_diff(time.ticks_ms(), inicio) > 15000:
            print("Error: Timeout WiFi")
            return False
        time.sleep(0.5)
    print("WiFi conectado. IP:", estacion.ifconfig()[0])
    return True

def callback_mqtt(topic, msg):
    global enviando_fotos
    if isinstance(topic, bytes):
        topic = topic.decode("utf-8")
    if isinstance(msg, bytes):
        msg = msg.decode("utf-8").strip()

    if topic == T_ESCANEAR:
        if msg == "iniciar":
            enviando_fotos = True
            print("[CAM] Iniciando captura bajo demanda...")
        elif msg == "detener":
            enviando_fotos = False
            gc.collect()
            print("[CAM] Captura detenida (Reposo).")

def iniciar_mqtt():
    cliente = MQTTClient(
        client_id="aurabot_camara",
        server=config.IP_BROKER,
        user=config.USUARIO_MQTT,
        password=config.CLAVE_MQTT,
        keepalive=30
    )
    cliente.set_callback(callback_mqtt)
    cliente.set_last_will(T_NODO, b"offline", retain=True, qos=1)
    try:
        cliente.connect()
        cliente.publish(T_NODO, b"online", retain=True, qos=1)
        cliente.subscribe(T_ESCANEAR.encode("utf-8"))
        print("MQTT conectado y suscrito a:", T_ESCANEAR)
        return cliente
    except Exception as e:
        print("Fallo MQTT:", e)
        return None

def main():
    global enviando_fotos

    if not conectar_wifi():
        return

    cliente_mqtt = iniciar_mqtt()
    if not cliente_mqtt:
        return

    # ==============================================
    # INICIALIZACIÓN DE CÁMARA (FREENOVE WROVER)
    # ==============================================
    try:
        print("Mapeando pines de la Freenove WROVER...")
        i2c_cam = I2C(0, scl=Pin(27), sda=Pin(26), freq=100000)

        cam = camera.Camera(
            data_pins=[4, 5, 18, 19, 36, 39, 34, 35],
            vsync_pin=25,
            href_pin=23,
            pclk_pin=22,
            xclk_pin=21,
            i2c=i2c_cam,
            pixel_format=camera.PixelFormat.RGB565,
            frame_size=camera.FrameSize.QQVGA
        )

        time.sleep(1)
        print("Cámara inicializada exitosamente (160x120 RGB565).")
    except Exception as e:
        print("Error al iniciar cámara:", e)
        return

    # ==============================================
    # CICLO DE CAPTURA Y PUBLICACIÓN BAJO DEMANDA
    # ==============================================
    while True:
        try:
            cliente_mqtt.check_msg()

            if enviando_fotos:
                buf = cam.capture()
                if buf and len(buf) == 38400:
                    cliente_mqtt.publish(T_CAM, buf, retain=False, qos=0)
                del buf
                gc.collect()
                time.sleep(0.12)
            else:
                time.sleep(0.05)

        except OSError:
            print("Pérdida de conexión MQTT. Reconectando...")
            enviando_fotos = False
            time.sleep(5)
            cliente_mqtt = iniciar_mqtt()

if __name__ == "__main__":
    main()