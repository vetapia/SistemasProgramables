# ============================================
# Proyecto:  AuraBot — Asistente Interactivo de Escritorio
# Archivo:   entrenar_ia.py
# Objetivo:  Capturar muestras faciales por MQTT, registrar usuarios y entrenar el modelo de reconocimiento LBPH
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import paho.mqtt.client as mqtt
import cv2
import numpy as np
import os
import json

IP_BROKER = "127.0.0.1"
PUERTO = 1883
TOPICO_CAMARA = "aurabot/sensor/camara/cam"
TOPICO_COMANDO_ESCANEAR = "aurabot/comando/ia/escanear"
MUESTRAS_OBJETIVO = 35

script_dir = os.path.dirname(os.path.abspath(__file__))
ruta_dataset = os.path.join(script_dir, "datos_validacion")
ruta_modelos_dir = os.path.join(script_dir, "modelos")
ruta_modelo = os.path.join(ruta_modelos_dir, "modelo_rostro.yml")
ruta_nombres = os.path.join(ruta_modelos_dir, "usuarios.json")

os.makedirs(ruta_dataset, exist_ok=True)
os.makedirs(ruta_modelos_dir, exist_ok=True)

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
            print("[✓] Detector facial DNN cargado desde 'ia/modelos/'.")
            return ("dnn", modelo)
        except Exception:
            pass

    ruta_xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    print("[✓] Detector facial Haar Cascade cargado.")
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

id_usuario = input("Ingresa el ID numérico del usuario (ej. 1 para carpeta 01): ").strip()
nombre_usuario = input("Ingresa el nombre del usuario (ej. Pedro): ").strip()

usuarios = {}
if os.path.exists(ruta_nombres):
    with open(ruta_nombres, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

usuarios[id_usuario] = {"nombre": nombre_usuario}
with open(ruta_nombres, "w", encoding="utf-8") as f:
    json.dump(usuarios, f, indent=4, ensure_ascii=False)

muestras_capturadas = 0
entrenamiento_listo = False

def entrenar_modelo():
    print("\n[*] Entrenando modelo LBPH con las muestras de 'datos_validacion/'...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    rostros = []
    ids = []

    for archivo in os.listdir(ruta_dataset):
        if archivo.endswith(".jpg") and archivo.startswith("user."):
            ruta_img = os.path.join(ruta_dataset, archivo)
            img_gris = cv2.imread(ruta_img, cv2.IMREAD_GRAYSCALE)
            id_img = int(archivo.split(".")[1])
            rostros.append(img_gris)
            ids.append(id_img)

    recognizer.train(rostros, np.array(ids))
    recognizer.save(ruta_modelo)
    print(f"[✓] Modelo guardado en '{ruta_modelo}'. Total de muestras: {len(rostros)}")

def al_conectar(cliente, userdata, flags, rc, properties=None):
    print(f"[✓] Conectado a Mosquitto. Activando cámara para {MUESTRAS_OBJETIVO} muestras...")
    cliente.subscribe(TOPICO_CAMARA)
    cliente.publish(TOPICO_COMANDO_ESCANEAR, b"iniciar")

def al_recibir_mensaje(cliente, userdata, msg):
    global muestras_capturadas, entrenamiento_listo

    if msg.topic != TOPICO_CAMARA or entrenamiento_listo:
        return

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

        for (x, y, w, h) in rostros:
            muestras_capturadas += 1
            rostro_proc = cv2.GaussianBlur(grises[y:y+h, x:x+w], (3, 3), 0)
            rostro_proc = cv2.resize(rostro_proc, (100, 100))

            nombre_archivo = os.path.join(ruta_dataset, f"user.{id_usuario}.{muestras_capturadas}.jpg")
            cv2.imwrite(nombre_archivo, rostro_proc)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Muestra {muestras_capturadas}/{MUESTRAS_OBJETIVO}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            break

        cv2.imshow("AuraBot - Entrenamiento Facial", frame)
        cv2.waitKey(1)

        if muestras_capturadas >= MUESTRAS_OBJETIVO:
            entrenamiento_listo = True
            cliente.publish(TOPICO_COMANDO_ESCANEAR, b"detener")
            cv2.destroyAllWindows()
            entrenar_modelo()
            cliente.disconnect()

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = al_conectar
    cliente.on_message = al_recibir_mensaje
    cliente.connect(IP_BROKER, PUERTO, 60)
    cliente.loop_forever()