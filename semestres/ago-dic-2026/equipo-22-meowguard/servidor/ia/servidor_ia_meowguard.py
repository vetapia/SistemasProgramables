# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Detección y Control de Plagas
# Archivo:   servidor_ia_meowguard.py
# Objetivo:  Procesar stream de video con YOLOv8 y publicar alertas vía MQTT y Firebase
# Equipo:    Mónica Moreno Torres [MATRÍCULA], Leonardo Gael Niño Cabrera [MATRÍCULA]
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import cv2
import time
import json
import paho.mqtt.client as mqtt
import requests
from ultralytics import YOLO

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA MEOWGUARD
# ==========================================
MODELO_PATH = "best_meowguard.pt"

# URL de la cámara:
# - Usa 0 para probar ahorita con la cámara web de tu laptop.
# - Cuando tengan el carrito listo, pon: "http://192.168.X.X:81/stream" (IP de la ESP32-CAM)
FUENTE_VIDEO = 0 

# Configuración MQTT (Broker público gratuito HiveMQ para pruebas rápidas)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "tecnm/leon/meowguard/alertas"

# URL de tu Firebase Realtime Database
FIREBASE_URL = "https://meowguard-e1e06-default-rtdb.firebaseio.com/meowguard"

# ==========================================
# 2. INICIALIZAR MODELO IA Y MQTT
# ==========================================
print("🐱 Cargando cerebro IA MEOWGUARD...")
model = YOLO(MODELO_PATH)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print(f"📡 Conectado al Broker MQTT: {MQTT_BROKER}")
except Exception as e:
    print(f"⚠️ No se pudo conectar a MQTT: {e}")

cap = cv2.VideoCapture(FUENTE_VIDEO)
ultima_alerta = 0
COOLDOWN_SEGUNDOS = 4  # Evita enviar 50 alertas por segundo de la misma plaga

print("🚀 Sistema de visión activo. Presiona 'q' en la ventana de video para salir.")

# ==========================================
# 3. BUCLE DE DETECCIÓN EN TIEMPO REAL
# ==========================================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Error leyendo video. Reintentando...")
        time.sleep(1)
        continue

    # Ejecutar inferencia con YOLOv8 (confianza mínima del 65%)
    results = model(frame, imgsz=640, conf=0.65, verbose=False)
    
    # Dibujar los recuadros (bounding boxes) sobre la imagen
    annotated_frame = results[0].plot()

    # Revisar qué detectó la IA en este cuadro
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        nombre_clase = model.names[cls_id]  # Cucaracha, Rata, Persona o Estanteria
        confianza = round(float(box.conf[0]) * 100, 1)

        # Coordenadas del centro del objeto detectado en pantalla
        x1, y1, x2, y2 = box.xyxy[0]
        centro_x = int((x1 + x2) / 2)
        centro_y = int((y1 + y2) / 2)

        # Si detecta PLAGA (Cucaracha o Rata) y ya pasó el tiempo de espera
        if nombre_clase in ["Cucaracha", "Rata"] and (time.time() - ultima_alerta > COOLDOWN_SEGUNDOS):
            ultima_alerta = time.time()
            hora_actual = time.strftime("%H:%M:%S")
            
            mensaje_alerta = {
                "event": "PLAGA_DETECTADA",
                "pestType": f"{nombre_clase} (IA YOLOv8)",
                "confidence": confianza,
                "x": int(centro_x * 0.7), # Escalar al mapa 2D de la web
                "y": int(centro_y * 0.5),
                "area": "Sector Patrullado",
                "timestamp": hora_actual,
                "activarAtomizador": True
            }

            print(f"🚨 ¡PLAGA DETECTADA! -> {nombre_clase} ({confianza}%) en X:{centro_x}, Y:{centro_y}")

            # A) Enviar alerta por MQTT (Para el carrito y suscripciones)
            client.publish(MQTT_TOPIC, json.dumps(mensaje_alerta), qos=1, retain=True)

            # B) Enviar a Firebase Realtime Database (Para el Mapa de Calor Web)
            try:
                requests.post(f"{FIREBASE_URL}/detections.json", json=mensaje_alerta, timeout=2)
                # Activar orden de spray en el robot
                requests.patch(f"{FIREBASE_URL}/telemetry.json", json={"isSpraying": True}, timeout=2)
            except Exception as e:
                print("⚠️ Error enviando a Firebase:", e)

        elif nombre_clase == "Persona":
            # Si ve una persona, solo lo muestra en pantalla sin activar el atomizador
            cv2.putText(annotated_frame, "HUMANO DETECTADO - ATOMIZADOR BLOQUEADO", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Mostrar ventana de visión de la IA en tu PC
    cv2.imshow("MEOWGUARD - Vision Artificial ESP32-CAM", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
