import network
import time
import dht
from machine import Pin, PWM, time_pulse_us
from umqtt.simple import MQTTClient

# --- DATOS DE RED ---
WIFI_SSID = 'INFINITUM0AAF' 
WIFI_PASS = 'GKqMpD3zdx'
MQTT_BROKER = '192.168.1.69' 
CLIENT_ID = 'ESP32_Omniserve'

# --- PINES DE LOS SENSORES ---
sensor_dht = dht.DHT11(Pin(4))
trig = Pin(13, Pin.OUT)
echo = Pin(34, Pin.IN)

# --- PINES DE LOS ACTUADORES ---
# Módulo de Relés 1 (Bombas 1 y 2)
rele1 = Pin(26, Pin.OUT) 
rele2 = Pin(27, Pin.OUT) 
# Módulo de Relés 2 (Bombas 3 y 4)
rele3 = Pin(14, Pin.OUT) # Ajusta este pin si usas otro
rele4 = Pin(23, Pin.OUT) # Ajusta este pin si usas otro

# Servomotores (Dispensadores de cereal/polvo)
servo1 = PWM(Pin(18), freq=50) 
servo2 = PWM(Pin(19), freq=50) # Ajusta este pin si usas otro

# --- RECEPCIÓN DE COMANDOS (Desde MQTT Dash) ---
def recibir_mensaje(topic, msg):
    t = topic.decode()
    m = msg.decode()
    print("Comando ->", t, ":", m)
    
    if t == "omniserve/rele1/cmd":
        rele1.value(int(m))
    elif t == "omniserve/rele2/cmd":
        rele2.value(int(m))
    elif t == "omniserve/rele3/cmd":
        rele3.value(int(m))
    elif t == "omniserve/rele4/cmd":
        rele4.value(int(m))
    elif t == "omniserve/servo1/cmd":
        duty = int(40 + (int(m) / 180) * 75)
        servo1.duty(duty)
    elif t == "omniserve/servo2/cmd":
        duty = int(40 + (int(m) / 180) * 75)
        servo2.duty(duty)

# --- FUNCIÓN ULTRASÓNICO ---
def leer_distancia():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duracion = time_pulse_us(echo, 1, 30000)
    if duracion > 0:
        return (duracion * 0.0343) / 2
    return -1

# --- CONEXIÓN WI-FI ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('Conectando a Wi-Fi...')
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        time.sleep(0.5)
print('¡Wi-Fi conectado!')

# --- CONEXIÓN MQTT Y SUSCRIPCIONES ---
cliente = MQTTClient(CLIENT_ID, MQTT_BROKER)
cliente.set_callback(recibir_mensaje)
cliente.connect()

cliente.subscribe(b"omniserve/rele1/cmd")
cliente.subscribe(b"omniserve/rele2/cmd")
cliente.subscribe(b"omniserve/rele3/cmd")
cliente.subscribe(b"omniserve/rele4/cmd")
cliente.subscribe(b"omniserve/servo1/cmd")
cliente.subscribe(b"omniserve/servo2/cmd")
print("Suscrito a los 6 actuadores.")

# --- BUCLE PRINCIPAL ---
ultimo_envio = time.ticks_ms()
time.sleep(2) # Dar tiempo al DHT11

try:
    while True:
        cliente.check_msg()
        
        if time.ticks_diff(time.ticks_ms(), ultimo_envio) > 3000:
            try:
                # Lectura Temp y Humedad
                sensor_dht.measure()
                temp = str(sensor_dht.temperature())
                hum = str(sensor_dht.humidity())
                cliente.publish(b"omniserve/temp", temp.encode())
                cliente.publish(b"omniserve/hum", hum.encode())
                
                # Lectura Ultrasónico
                dist = leer_distancia()
                if dist > 0:
                    dist_str = str(round(dist, 1))
                    cliente.publish(b"omniserve/dist", dist_str.encode())
                    
                print(f"Enviado -> Temp: {temp}C | Hum: {hum}% | Dist: {dist_str}cm")
                
            except Exception as e:
                pass # Evita que el código se caiga si un sensor falla una lectura
                
            ultimo_envio = time.ticks_ms()
            
        time.sleep(0.1)
except KeyboardInterrupt:
    cliente.disconnect()
