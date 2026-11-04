# ============================================
# Proyecto:  EcoClasifica
# Archivo:   config.py
# Objetivo:  Configuración de pines, red y MQTT
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

WIFI_SSID = "Totalplay-C6AE"
WIFI_PASS = "C6AEA94AGWhz5U5w"
MQTT_BROKER = "192.168.100.7"  # IPv4 de tu laptop
MQTT_PUERTO = 1883
MQTT_USER = "admin"
MQTT_PASS = "Ariel2026"

# Tiempos de red
KEEPALIVE_S = 60
TIMEOUT_WIFI_MS = 15000
INTERVALO_REINTENTO_RED_MS = 5000
INTERVALO_PING_MS = 20000  # siempre menor que KEEPALIVE_S

# Pines Sensores
PIN_TRIG = 19
PIN_ECHO = 34
PIN_LDR = 35
PIN_SDA = 21
PIN_SCL = 22

# Pines Actuadores Físicos Actuales
PIN_BUZZER = 26
PIN_RELE = 27
PIN_LED = 2  # Actuador 3 temporal (LED azul integrado)

# Pines Servomotores (Pendientes, físicos no conectados)
PIN_SERVO_PAPEL = 18
PIN_SERVO_PLASTICO = 5
PIN_SERVO_METAL = 15

# Lógica de actuadores (cambiar a True si encienden en estado bajo)
RELE_ACTIVO_BAJO = False
BUZZER_ACTIVO_BAJO = False

# --- Requeridos por hal/ ---
PINES = {
    'TRIG': PIN_TRIG, 'ECHO': PIN_ECHO, 'LDR': PIN_LDR,
    'SDA': PIN_SDA, 'SCL': PIN_SCL,
    'BUZZER': PIN_BUZZER, 'RELE': PIN_RELE,
    'SERVO_PAPEL': PIN_SERVO_PAPEL,
    'SERVO_PLASTICO': PIN_SERVO_PLASTICO,
    'SERVO_METAL': PIN_SERVO_METAL,
}

DISTANCIA_MIN_CM = 2
DISTANCIA_MAX_CM = 400
INTERVALO_DISTANCIA_MS = 100
INTERVALO_MPU_MS = 20
INTERVALO_RECONEXION_MPU_MS = 1000

# Ángulos de la compuerta por tipo de residuo (ajústalos al montaje real)
SERVO_ANGULOS = {
    'papel':    (0, 90),
    'plastico': (0, 90),
    'metal':    (0, 90),
}
