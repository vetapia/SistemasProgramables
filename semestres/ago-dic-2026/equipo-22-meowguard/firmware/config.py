# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   config.py
# Objetivo:  Configuración de pines GPIO, parámetros de sensores y credenciales base del ESP32
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

# GPIO del ESP32 principal. Orden: izquierda adelante/atrás, derecha adelante/atrás.
MOTOR_PINS = (13, 14, 23, 18)
PWM_HZ = 2000
TRIG_PIN = 25
ECHO_PIN = 26
REAR_PIN = 35
REAR_ACTIVE = 0
# Opcionales para el montaje anterior de dos sensores. Confirma el cableado.
REAR_LEFT_PIN = None
REAR_RIGHT_PIN = None
SDA_PIN = 21
SCL_PIN = 22
GYRO_Z_SIGN = 1  # Z arriba; giro a la izquierda visto desde arriba debe dar positivo.

# Etapa externa de potencia que corta la alimentación del atomizador.
ATOMIZER_POWER_PIN = None
ATOMIZER_ACTIVE = 1
ATOMIZER_SERVO_PIN = None  # Solo si el módulo necesita pulsar su botón al energizarse.
SERVO_REST_US = 1000
SERVO_PRESS_US = 1500
FAN_PIN = None
FAN_ACTIVE = 1
SPRAY_MS = 2500

# Encoders opcionales: delantera izq., trasera izq., delantera der., trasera der.
# Cuenta flancos ascendentes por vuelta de la rueda, ya incluida la reductora.
ENCODER_PINS = (None, None, None, None)
ENCODER_PULSES_PER_REV = (20, 20, 20, 20)
WHEEL_DIAMETER_CM = 6.5  # Punto de partida. Mide la rueda montada.
TRACK_CM = 15.0  # Punto de partida. Distancia entre centros izq./der.

DEFAULT_POWER = 55
FRONT_LIMIT_CM = 25
AP_SSID = "MEOWGUARD"
AP_PASSWORD = "CAMBIA-Esta-Clave-22"
WIFI_SSID = ""
WIFI_PASSWORD = ""
MQTT_HOST = ""  # IP del broker en la red local. Vacío desactiva MQTT.
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "meowguard-carrito-22"

# Opcional: crea config_local.py en la raíz de la placa para tus valores.
try:
    from config_local import *
except ImportError:
    pass
