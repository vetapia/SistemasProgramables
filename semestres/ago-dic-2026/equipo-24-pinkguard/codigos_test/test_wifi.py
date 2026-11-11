import network
import time

def conectar_wifi(ssid, password):
    # Inicializar la interfaz de red en modo estación
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Verificar si ya está conectado
    if not wlan.isconnected():
        print('Conectando a la red...')
        wlan.connect(ssid, password)
        
        # Esperar hasta que se establezca la conexión
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.', end='')
            
    print('\n¡Conexión exitosa!')
    # ifconfig() devuelve: (IP, Máscara de subred, Puerta de enlace, DNS)
    print('Configuración de red:', wlan.ifconfig())

# Sustituye por tus credenciales
conectar_wifi('iPhone de Yoscar', 'yoscar12')