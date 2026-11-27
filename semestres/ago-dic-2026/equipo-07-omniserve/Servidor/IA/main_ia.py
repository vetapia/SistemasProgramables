"""
Proyecto: OmniServe - Sistema Dispensador Automatizado
Materia: Sistemas Programables
Equipo: 07
Integrantes: Diego Jahzeel Méndez Martínez (23240829), Joshua Maximiliano Anguiano Contreras (23240329)
Archivo: main_ia.py (Servidor de Visión Artificial)

Objetivo:
Detectar rostros humanos frontales en tiempo real mediante OpenCV (Haar Cascade) 
a través de la cámara web para disparar la secuencia automatizada de dispensación 
enviando comandos por MQTT a la ESP32, mientras registra el historial de eventos 
y estados en Cloud Firestore (Firebase).
"""

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
try:
    firebase_admin.initialize_app(credencial)
except ValueError:
    pass # Previene crasheos si reinicias el script rápido
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

cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="IA_Laptop_Omniserve")
try:
    cliente_mqtt.connect(MQTT_BROKER)
    cliente_mqtt.loop_start() # Mantiene el flujo de red abierto en segundo plano
    print("Conectado al Broker MQTT.")
except Exception as e:
    print(f"Error conectando a MQTT: {e}")

# --- Configuración IA de OpenCV ---
face_cascade = cv2.CascadeClassifier(xml_file)
cap = cv2.VideoCapture(0)
print("Iniciando cámara... Presiona 'q' para salir.")

tiempo_ultimo_comando = 0
cooldown_segundos = 4 # Aumentado a 4s para dar margen a toda la secuencia

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rostros = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    
    texto_estado = "Omniserve IA - Esperando rostro..."
    color_texto = (0, 255, 0) 

    if len(rostros) > 0:
        texto_estado = "Rostro detectado! Activando sistema completo..."
        color_texto = (0, 0, 255) 
        
        for (x, y, w, h) in rostros:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        tiempo_actual = time.time()
        if tiempo_actual - tiempo_ultimo_comando > cooldown_segundos:
            print("IA detecta rostro -> enviando secuencia escalonada al ESP32...")
            
# 1. Enviar órdenes (Cambiamos "ON" por "1" para evitar crasheo en el ESP32)
            cliente_mqtt.publish("omniserve/servo1/cmd", "90")
            time.sleep(0.3)
            cliente_mqtt.publish("omniserve/servo2/cmd", "90")
            time.sleep(0.3)
            
            # Si en tu MQTT Dash usas otro valor para encender (ej. "true"), ponlo aquí en lugar de "1"
            cliente_mqtt.publish("omniserve/rele1/cmd", "0")
            time.sleep(0.3)
            cliente_mqtt.publish("omniserve/rele2/cmd", "0")
            time.sleep(0.3)
            cliente_mqtt.publish("omniserve/rele3/cmd", "0")
            time.sleep(0.3)
            cliente_mqtt.publish("omniserve/rele4/cmd", "0")
            
            print("Secuencia completa activada en hardware.")
            
            # 2. Registrar el bloque entero en Firebase
            try:
                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.collection('omniserve_logs').add({
                    'evento': 'Rostro detectado',
                    'accion': 'Activacion: 2 Servos (90), 4 Reles (ON)',
                    'timestamp': fecha_hora
                })
                print(f"Log guardado en Firebase exitosamente a las {fecha_hora}")
            except Exception as e:
                print(f"Error al subir a Firebase: {e}")
                
            # Reiniciar el temporizador usando el tiempo exacto en el que terminó la secuencia
            tiempo_ultimo_comando = time.time()

    cv2.putText(frame, texto_estado, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)
    cv2.imshow("Camara Omniserve - IA", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cliente_mqtt.loop_stop()
cliente_mqtt.disconnect()
cv2.destroyAllWindows()