# ============================================
# Proyecto:  AuraBot — Asistente Interactivo de Escritorio
# Archivo:   detector_rostro.py
# Objetivo:  Recibir frames RGB565 por MQTT, detectar rostros con OpenCV DNN y reconocer usuarios con LBPH
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import paho.mqtt.client as mqtt
import cv2
import numpy as np
import os
import sys
import json
from datetime import datetime  # <--- 1. Importamos datetime

IP_BROKER = "127.0.0.1"
PUERTO = 1883
TOPICO_CAMARA = "aurabot/sensor/camara/cam"
TOPICO_ESTADO_ROSTRO = "aurabot/estado_actual/rostro"
TOPICO_COMANDO_ESCANEAR = "aurabot/comando/ia/escanear"

script_dir = os.path.dirname(os.path.abspath(__file__))
ruta_modelos_dir = os.path.join(script_dir, "modelos")
ruta_modelo = os.path.join(ruta_modelos_dir, "modelo_rostro.yml")
ruta_nombres = os.path.join(ruta_modelos_dir, "usuarios.json")

if not os.path.exists(ruta_modelo):
    print("[!] ERROR: No existe 'ia/modelos/modelo_rostro.yml'. Ejecuta primero 'entrenar_ia.py'.")
    sys.exit()

def cargar_detector_facial():
    prototxt = os.path.join(ruta_modelos_dir, "deploy.prototxt")
    caffemodel = None
    for f in os.listdir(ruta_modelos_dir):
        if f.startswith("res10_300x300") and f.endswith(".caffemodel"):
            caffemodel = os.path.join(ruta_modelos_dir, f)
            break

    if hasattr(cv2.dnn, "readNetFromCaffe") and os.path.exists(prototxt) and caffemodel:
        try:
            modelo = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
            return ("dnn", modelo)
        except Exception:
            pass

    ruta_xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    return ("haar", cv2.CascadeClassifier(ruta_xml))

def detectar_rostros(detector, frame_bgr, grises):
    tipo, modelo = detector
    h, w = frame_bgr.shape[:2]
    rostros = []

    if tipo == "dnn":
        blob = cv2.dnn.blobFromImage(cv2.resize(frame_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        modelo.setInput(blob)
        detecciones = modelo.forward()

        for i in range(detecciones.shape[2]):
            if detecciones[0, 0, i, 2] > 0.6:
                box = detecciones[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 > x1 and y2 > y1:
                    rostros.append((x1, y1, x2 - x1, y2 - y1))
    else:
        rostros = modelo.detectMultiScale(grises, scaleFactor=1.1, minNeighbors=6, minSize=(30, 30))

    return rostros

detector = cargar_detector_facial()
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(ruta_modelo)

usuarios = {}
if os.path.exists(ruta_nombres):
    with open(ruta_nombres, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

escaneo_activo = False
conteo_conocidos = {}
intentos_desconocido = 0

def reiniciar_contadores():
    global conteo_conocidos, intentos_desconocido
    conteo_conocidos = {}
    intentos_desconocido = 0

def al_conectar(cliente, userdata, flags, rc, properties=None):
    print(f"[✓] Detector listo y en espera de proximidad (Código: {rc})")
    cliente.subscribe(TOPICO_CAMARA)
    cliente.subscribe(TOPICO_COMANDO_ESCANEAR)

def al_recibir_mensaje(cliente, userdata, msg):
    global escaneo_activo, conteo_conocidos, intentos_desconocido

    if msg.topic == TOPICO_COMANDO_ESCANEAR:
        orden = msg.payload.decode("utf-8").strip()
        hora_actual = datetime.now().strftime("%H:%M:%S")  # <--- Captura hora
        if orden == "iniciar":
            reiniciar_contadores()
            escaneo_activo = True
            print(f"[IA - {hora_actual}] Escaneo activado por proximidad...")
        elif orden == "detener":
            escaneo_activo = False
            cv2.destroyAllWindows()
            print(f"[IA - {hora_actual}] Escaneo detenido.")
        return

    if msg.topic == TOPICO_CAMARA and escaneo_activo:
        try:
            nparr = np.frombuffer(msg.payload, np.uint8)
            if len(nparr) != 38400:
                return

            frame16 = nparr.view(np.uint16).byteswap().reshape((120, 160))
            b = (frame16 & 0x1F) << 3
            g = ((frame16 >> 5) & 0x3F) << 2
            r = ((frame16 >> 11) & 0x1F) << 3

            frame = np.dstack((b, g, r)).astype(np.uint8)
            frame = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_LINEAR)

            grises = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            grises = cv2.equalizeHist(grises)

            rostros = detectar_rostros(detector, frame, grises)
            hora_actual = datetime.now().strftime("%H:%M:%S")  # <--- Hora del frame actual

            # 2. Mostrar la hora en la esquina superior izquierda del video
            cv2.putText(frame, f"Hora: {hora_actual}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            if len(rostros) > 0:
                rostro_principal = max(rostros, key=lambda r: r[2] * r[3])
                (x, y, w, h) = rostro_principal

                rostro_recortado = cv2.GaussianBlur(grises[y:y+h, x:x+w], (3, 3), 0)
                rostro_recortado = cv2.resize(rostro_recortado, (100, 100))

                id_predicho, distancia = recognizer.predict(rostro_recortado)

                if distancia < 85:
                    info = usuarios.get(str(id_predicho), {"nombre": "Desconocido"})
                    nombre = info["nombre"]
                    conteo_conocidos[nombre] = conteo_conocidos.get(nombre, 0) + 1
                    color = (0, 255, 0)

                    if conteo_conocidos[nombre] >= 3:
                        cliente.publish(TOPICO_ESTADO_ROSTRO, nombre.encode("utf-8"))
                        cliente.publish(TOPICO_COMANDO_ESCANEAR, b"detener")
                        # 3. Mostrar hora exacta en consola al identificar
                        print(f"[--> MQTT | {hora_actual}] Identificado: {nombre}. Cámara detenida.")
                        escaneo_activo = False
                        cv2.destroyAllWindows()
                        return
                else:
                    nombre = "Desconocido"
                    intentos_desconocido += 1
                    color = (0, 0, 255)

                    if intentos_desconocido >= 8:
                        cliente.publish(TOPICO_ESTADO_ROSTRO, b"Desconocido")
                        cliente.publish(TOPICO_COMANDO_ESCANEAR, b"detener")
                        # 3. Mostrar hora exacta en consola si es desconocido
                        print(f"[--> MQTT | {hora_actual}] Persona no registrada: Desconocido. Cámara detenida.")
                        escaneo_activo = False
                        cv2.destroyAllWindows()
                        return

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"{nombre} ({int(distancia)})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            cv2.imshow("AuraBot - Detector Facial", frame)
            cv2.waitKey(1)

        except Exception as e:
            print(f"[!] Error procesando imagen: {e}")

if __name__ == "__main__":
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = al_conectar
    cliente.on_message = al_recibir_mensaje

    cliente.connect(IP_BROKER, PUERTO, 60)
    cliente.loop_forever()
