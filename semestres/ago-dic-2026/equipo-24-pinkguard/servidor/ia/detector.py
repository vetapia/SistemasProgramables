import paho.mqtt.client as mqtt
import cv2
import numpy as np
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
from ultralytics import YOLO
import cloudinary
import cloudinary.uploader
import firebase_admin

# --- CONFIGURACIÓN DE CLOUDINARY ---
# API, campos dejados en blanco a proposito con el fin de no mostrar mis credenciales
cloudinary.config(
    cloud_name = "",
    api_key = "",
    api_secret = ""
)
# --- CONFIGURACIÓN DE FIREBASE (Realtime Database) ---
FIREBASE_URL = 'https://sistemas-programables-pinkg-default-rtdb.firebaseio.com/'
if not firebase_admin._apps:
    cred = credentials.Certificate('credenciales.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_URL
    })

ref_alertas = db.reference('Modelo')

# --- CONFIGURACIÓN DE YOLOv8 ---
print("[BOOT] Cargando red neuronal YOLOv8 Nano...")
modelo = YOLO("yolov8n.pt")

CARPETA_DESTINO = "capturas_test"
os.makedirs(CARPETA_DESTINO, exist_ok=True)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] Conectado al broker Mosquitto local.")
        client.subscribe("pinkguard/camara/foto")
        print("[MQTT] Suscrito a 'pinkguard/camara/foto'. Esperando imágenes...")
    else:
        print(f"[MQTT] Error de conexión, código: {rc}")

def on_message(client, userdata, msg):
    print(f"\n[RECEPCIÓN] Payload recibido. Tamaño: {len(msg.payload)} bytes.")
    
    try:
        # 1. Transformar bytes crudos a matriz NumPy
        buffer_np = np.frombuffer(msg.payload, dtype=np.uint8)
        imagen = cv2.imdecode(buffer_np, cv2.IMREAD_COLOR)
        
        if imagen is None:
            print("[ERROR] No se pudo decodificar la imagen.")
            return

        # 2. Inferencia con YOLO (Clase 0: persona)
        resultados = modelo(imagen, classes=[0], conf=0.4, verbose=False)
        hay_persona = len(resultados[0].boxes) > 0
        
        if hay_persona:
            print(f"[ALERTA] ¡Se detectaron {len(resultados[0].boxes)} persona(s)!")
            img_procesar = resultados[0].plot()
        else:
            print("[INFO] Área despejada. No hay personas.")
            img_procesar = imagen

        # Escalar para visualización limpia
        img_final = cv2.resize(img_procesar, (320, 240))

        # 3. Guardado local temporal en PC
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"intruso_{timestamp}.jpg" if hay_persona else f"captura_{timestamp}.jpg"
        ruta_local = os.path.join(CARPETA_DESTINO, nombre_archivo)
        cv2.imwrite(ruta_local, img_final)
        print(f"[GUARDADO LOCAL] {ruta_local}")

        # 4. Subir a Cloudinary SIEMPRE
        print("[CLOUDINARY] Subiendo imagen a la nube...")
        respuesta_cloud = cloudinary.uploader.upload(ruta_local, folder="pinkguard_intrusos")
        url_imagen = respuesta_cloud.get("secure_url")
        print(f"[CLOUDINARY] ¡Subida exitosa! URL: {url_imagen}")

        # 5. Postear la URL y metadatos en Firebase Realtime Database SIEMPRE
        tipo_evento = 'INTRUSION_DETECTADA' if hay_persona else 'MONITOREO_GENERAL'
        nueva_alerta = ref_alertas.push({
            'evento': tipo_evento,
            'humano_detectado': hay_persona,
            'imagen_url': url_imagen,
            'timestamp': {'.sv': 'timestamp'}
        })
        print(f"[FIREBASE] Registro guardado en la base de datos con ID: {nueva_alerta.key}")

    except Exception as e:
        print(f"[ERROR] Fallo durante el procesamiento: {e}")

if __name__ == "__main__":
    try:
        cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "detector_pc")
    except AttributeError:
        cliente = mqtt.Client("detector_pc")

    cliente.on_connect = on_connect
    cliente.on_message = on_message

    print("--- INICIANDO SISTEMA DE VISIÓN CLOUDINARY + FIREBASE ---")
    
    try:
        cliente.connect("127.0.0.1", 1883, 60)
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Apagando detector...")
    except ConnectionRefusedError:
        print("\n[ERROR] Conexión rechazada. Asegúrate de que Mosquitto esté corriendo.")