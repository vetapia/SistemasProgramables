import paho.mqtt.client as mqtt
import json
from datetime import datetime

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_BASE = "omnivault/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[+] Backend conectado al Broker MQTT exitosamente.")
        client.subscribe(TOPIC_BASE)
        print(f"[*] Escuchando telemetría en: {TOPIC_BASE}")
    else:
        print(f"[-] Error de conexión. Código: {rc}")

def on_message(client, userdata, msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    payload = msg.payload.decode('utf-8')
    
    print(f"[{timestamp}] TOPIC: {msg.topic}")
    try:
        datos = json.loads(payload)
        print(f"    DATA (JSON): {json.dumps(datos, indent=2)}")
    except json.JSONDecodeError:
        print(f"    CMD (TEXT): {payload}")

if __name__ == "__main__":
    client = mqtt.Client(client_id="OmniVault_Backend_Eq23")
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("Iniciando Servidor OmniVault...")
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[!] Servidor apagado por el usuario.")
        client.disconnect()