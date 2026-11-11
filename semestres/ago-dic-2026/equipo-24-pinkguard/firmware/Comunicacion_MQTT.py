import network
from umqtt.simple import MQTTClient
import time

class Comunicacion_MQTT:
    def __init__(self, ssid, password, broker_ip, client_id="esp32_maestro"):
        self.ssid = ssid
        self.password = password
        self.broker_ip = broker_ip
        self.client_id = client_id
        self.client = None

    def conectar_wifi(self):
        """Conecta el ESP32 a la red Wi-Fi"""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            print(f"[MQTT] Conectando a Wi-Fi: {self.ssid}...")
            wlan.connect(self.ssid, self.password)
            
            # Esperar a que conecte (timeout de 10 segundos)
            intentos = 0
            while not wlan.isconnected() and intentos < 20:
                time.sleep(0.5)
                intentos += 1
                
        return wlan.isconnected()

    def iniciar_comunicacion(self):
        """
        Conecta a Wi-Fi y al Broker MQTT. 
        Retorna True si todo salió bien, o False si falló.
        """
        try:
            # 1. Asegurar Wi-Fi
            if not self.conectar_wifi():
                print("[MQTT] Error: No se pudo conectar a la red Wi-Fi.")
                return False
            
            print("[MQTT] Wi-Fi conectado con éxito. Conectando al Broker MQTT...")
            
            # 2. Inicializar cliente MQTT
            self.client = MQTTClient(self.client_id, self.broker_ip)
            self.client.connect()
            
            print("[MQTT] ¡Conexión con el Broker MQTT establecida!")
            return True
            
        except Exception as e:
            print("[MQTT] Error crítico durante la conexión:", e)
            return False

    def postear_dato(self, topico, valor):
        """
        Método general para publicar cualquier dato.
        Ejemplo: postear_dato("casa/sensor/pir", "1")
        """
        try:
            if self.client:
                self.client.publish(topico, str(valor))
                print(f"[MQTT] Publicado -> [{topico}]: {valor}")
                return True
            else:
                print("[MQTT] Error: Cliente MQTT no inicializado.")
                return False
        except Exception as e:
            print(f"[MQTT] Error al publicar en {topico}:", e)
            return False