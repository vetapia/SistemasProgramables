import cv2
import paho.mqtt.client as mqtt
import time
import urllib.request
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- Configuración Firebase ---
ruta_credenciales = "credenciales.json" 
credencial = credentials.Certificate(ruta_credenciales)
firebase_admin.initialize_app(credencial)
db = firestore.client()
print("Conectado a Firebase Firestore.")

# --- Descarga automática del modelo de IA ---
xml_file = 'haarcascade_frontalface_default.xml'
if not os.path.isfile(xml_file):
    print("Descargando modelo de IA de OpenCV...")
    url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'
    urllib.request.urlretrieve(url, xml_file)

# --- Configuración MQTT ---
MQTT_BROKER = "192.168.1.69" 
MQTT_TOPIC_SERVO = "omniserve/servo1/cmd"

cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="IA_Laptop_Omniserve")
try:
    cliente_mqtt.connect(MQTT_BROKER)
    print("Conectado al Broker MQTT.")
except Exception as e:
    print(f"Error conectando a MQTT: {e}")

# --- Configuración IA de OpenCV ---
face_cascade = cv2.CascadeClassifier(xml_file)
cap = cv2.VideoCapture(0)
print("Iniciando cámara... Presiona 'q' para salir.")

tiempo_ultimo_comando = 0
cooldown_segundos = 3 

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    texto_estado = "Omniserve IA - Esperando rostro..."
    color_texto = (0, 255, 0) 

    if len(rostros) > 0:
        texto_estado = "Rostro detectado! Activando Servo..."
        color_texto = (0, 0, 255) 
        
        for (x, y, w, h) in rostros:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        tiempo_actual = time.time()
        if tiempo_actual - tiempo_ultimo_comando > cooldown_segundos:
            # 1. Activar MQTT
            cliente_mqtt.publish(MQTT_TOPIC_SERVO, "90")
            print("IA detecta rostro -> actuador activado")
            
            # 2. Registrar en Firebase
            try:
                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.collection('omniserve_logs').add({
                    'evento': 'Rostro detectado',
                    'accion': 'Servo 1 activado',
                    'timestamp': fecha_hora
                })
                print(f"Log guardado en Firebase exitosamente a las {fecha_hora}")
            except Exception as e:
                print(f"Error al subir a Firebase: {e}")
                
            tiempo_ultimo_comando = tiempo_actual

    cv2.putText(frame, texto_estado, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)
    cv2.imshow("Camara Omniserve - IA", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()