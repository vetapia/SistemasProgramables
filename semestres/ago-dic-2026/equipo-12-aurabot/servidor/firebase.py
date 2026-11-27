# ============================================
# Proyecto:  AuraBot — Asistente Interactivo de Escritorio
# Archivo:   firebase.py
# Objetivo:  Sincronizar bidireccionalmente los mensajes MQTT de sensores, IA y actuadores con Firebase Realtime Database
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db
import os
import time
from datetime import datetime

IP_BROKER = "127.0.0.1"
PUERTO = 1883
URL_FIREBASE = "https://aurabot-4ba95-default-rtdb.firebaseio.com/"

script_dir = os.path.dirname(os.path.abspath(__file__))
ruta_credenciales = os.path.join(script_dir, "serviceAccountKey.json")

cred = credentials.Certificate(ruta_credenciales)
firebase_admin.initialize_app(cred, {"databaseURL": URL_FIREBASE})

ultimo_estado_actuador = {
    "servomotor": None,
    "relevador": None,
    "oled": None
}

cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def al_conectar_mqtt(cliente, userdata, flags, rc, properties=None):
    print(f"[✓] Puente Firebase conectado a Mosquitto (Código: {rc})")
    cliente.subscribe("aurabot/#")

def al_recibir_mqtt(cliente, userdata, msg):
    topic = msg.topic
    if topic == "aurabot/sensor/camara/cam":
        return

    payload = msg.payload.decode("utf-8").strip()

    try:
        if topic == "aurabot/sensor/pir/central":
            db.reference("sensores/telemetria").update({"pir": int(payload)})
        elif topic == "aurabot/sensor/ultrasonico/central":
            db.reference("sensores/telemetria").update({"distancia_cm": float(payload)})
        elif topic == "aurabot/sensor/luz/central":
            db.reference("sensores/telemetria").update({"luz_porcentaje": int(payload)})

        elif topic == "aurabot/actuador/servo/central":
            ultimo_estado_actuador["servomotor"] = payload
            db.reference("actuadores/servomotor").update({"estado": payload})
        elif topic == "aurabot/actuador/relevador/central":
            ultimo_estado_actuador["relevador"] = payload
            db.reference("actuadores/relevador").update({"estado": payload})
        elif topic == "aurabot/actuador/oled/central":
            ultimo_estado_actuador["oled"] = payload
            db.reference("actuadores/oled").update({"estado": payload})
        elif topic == "aurabot/actuador/nodo/central":
            db.reference("estado_sistema").update({"nodo_central": payload})

        elif topic == "aurabot/estado_actual/rostro":
            ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.reference("presencia/actual").update({
                "usuario": payload,
                "ultima_actualizacion": ahora_str
            })
            if payload != "ausente":
                db.reference("alertas").push({
                    "evento": "Acceso detectado",
                    "usuario": payload,
                    "fecha_hora": ahora_str
                })
                print(f"[Firebase] Alerta registrada: {payload} ({ahora_str})")

    except Exception as e:
        print(f"[!] Error actualizando Firebase: {e}")

def escuchar_cambios_firebase(event):
    if event.data is None:
        return

    ruta = event.path.strip("/")
    datos = event.data

    mapa_topicos = {
        "servomotor": "aurabot/comando/servo/central",
        "relevador": "aurabot/comando/relevador/central",
        "oled": "aurabot/comando/oled/central"
    }

    if ruta in mapa_topicos and isinstance(datos, dict) and "estado" in datos:
        nuevo_estado = str(datos["estado"])
        if nuevo_estado != ultimo_estado_actuador.get(ruta):
            ultimo_estado_actuador[ruta] = nuevo_estado
            cliente_mqtt.publish(mapa_topicos[ruta], nuevo_estado)
            print(f"[Firebase --> MQTT] {ruta}: {nuevo_estado}")

    elif "/estado" in ruta:
        actuador = ruta.split("/")[0]
        if actuador in mapa_topicos:
            nuevo_estado = str(datos)
            if nuevo_estado != ultimo_estado_actuador.get(actuador):
                ultimo_estado_actuador[actuador] = nuevo_estado
                cliente_mqtt.publish(mapa_topicos[actuador], nuevo_estado)
                print(f"[Firebase --> MQTT] {actuador}: {nuevo_estado}")

if __name__ == "__main__":
    cliente_mqtt.on_connect = al_conectar_mqtt
    cliente_mqtt.on_message = al_recibir_mqtt
    cliente_mqtt.connect(IP_BROKER, PUERTO, 60)
    cliente_mqtt.loop_start()

    print("[*] Escuchando cambios en Firebase Realtime Database...")
    db.reference("actuadores").listen(escuchar_cambios_firebase)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cliente_mqtt.loop_stop()
        cliente_mqtt.disconnect()