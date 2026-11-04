# ============================================
# Proyecto:  EcoClasifica
# Archivo:   config.py
# Objetivo:  Configuración de pines, red y MQTT
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

WIFI_SSID = "TU_WIFI"
WIFI_PASS = "TU_PASSWORD"
MQTT_BROKER = "192.168.X.X" # Reemplaza con la IPv4 de tu laptop

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

# Lógica de actuadores (Cambiar a True si encienden en estado bajo)
RELE_ACTIVO_BAJO = False
BUZZER_ACTIVO_BAJO = False