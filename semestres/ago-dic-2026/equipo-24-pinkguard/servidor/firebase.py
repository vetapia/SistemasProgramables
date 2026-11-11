import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db

# 1. Configuración de Firebase con tu URL exacta
FIREBASE_URL = 'https://sistemas-programables-pinkg-default-rtdb.firebaseio.com/' 

cred = credentials.Certificate('credenciales.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_URL
})

# Referencia al nodo "Modelo" que tienes en tu base de datos
ref_alertas = db.reference('Modelo')

# 2. Funciones del Broker MQTT
def on_connect(client, userdata, flags, rc):
    print("[MQTT] ¡Conectado al broker local Mosquitto!")
    client.subscribe("pinkguard/estado")
    print("[MQTT] Escuchando alertas de PinkGuard en el tópico 'pinkguard/estado'...")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    print(f"\n[MOSQUITTO] Mensaje recibido: {payload_str}")
    
    try:
        # Desarmamos tu string "Trig:PIR_DETECCION|PIR:1|LDR:259..." en un diccionario
        datos_json = {}
        pares = payload_str.split('|')
        for par in pares:
            clave, valor = par.split(':')
            # Convertimos valores para que se guarden con el tipo correcto (int o boolean)
            if valor.isdigit():
                datos_json[clave] = int(valor)
            elif valor == "True":
                datos_json[clave] = True
            elif valor == "False":
                datos_json[clave] = False
            else:
                datos_json[clave] = valor
        
        # 3. Subir a Firebase
        # Se guardará dentro del nodo "Modelo" con una clave única para cada alerta
        nueva_alerta_ref = ref_alertas.push({
            'sensores': datos_json,
            'timestamp': {'.sv': 'timestamp'} # Firebase agrega la hora oficial
        })
        print(f"[FIREBASE] ¡Guardado con éxito! ID: {nueva_alerta_ref.key}")
        
    except Exception as e:
        print(f"[ERROR] Hubo un problema procesando o subiendo el mensaje: {e}")

# 4. Inicialización del puente local
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Iniciando Puente Mosquitto -> Firebase...")
client.connect("localhost", 1883, 60) # Se conecta al Mosquitto de tu PC
client.loop_forever() # Mantiene el script vivo escuchando