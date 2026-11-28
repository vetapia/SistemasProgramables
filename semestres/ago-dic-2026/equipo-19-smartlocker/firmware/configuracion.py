# ============================================================
# configuracion.py - Pines, PIN, Wi-Fi y topicos MQTT
# ============================================================

# Pantalla OLED por I2C
OLED_SDA = 21
OLED_SCL = 22

# Sensores
DHT_PIN = 4
TRIG_PIN = 5
ECHO_PIN = 18

# Actuadores
BUZZER_PIN = 25

# Teclado matricial 4x4: filas y columnas
FILAS = [13, 12, 14, 27]
COLS = [26, 33, 32, 15]

TECLAS = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Seguridad local
PIN_CORRECTO = "2005"

# ------------------------------------------------------------
# Wi-Fi: agrega las redes a las que quieres que se conecte.
# El ESP32 probará cada red en orden. Solo admite Wi-Fi 2.4 GHz.
# Reemplaza los textos de ejemplo por tus datos reales.
# Para una red abierta, deja la contraseña como "".
# ------------------------------------------------------------
WIFI_REDES = [
    ("Red primer planta", "Q_w_e_r_t_y_10"),
    ("POCO X7", "12346678"),
    # ("NOMBRE_HOTSPOT_CELULAR", "CONTRASENA_HOTSPOT"),
]

TIEMPO_ESPERA_WIFI_S = 12

# ------------------------------------------------------------
# Broker MQTT público de prueba.
# Alternativas: "broker.emqx.io" o "broker.hivemq.com".
# Puerto 1883 = MQTT sin cifrado; solo para pruebas.
# ------------------------------------------------------------
BROKER = "test.mosquitto.org"
PUERTO = 1883
INTERVALO_REINTENTO_MQTT_MS = 10000

# IMPORTANTE: cambia este identificador por uno único para tu equipo.
# Un prefijo menos común ayuda a evitar colisiones, pero NO da seguridad.
TOPIC_PREFIX = b"smartlocker/equipo_7_esp32_6b29c81d"
TOPIC_TEMP = TOPIC_PREFIX + b"/temp"
TOPIC_HUM = TOPIC_PREFIX + b"/hum"
TOPIC_DIST = TOPIC_PREFIX + b"/dist"
TOPIC_ESTADO = TOPIC_PREFIX + b"/estado"
TOPIC_CMD = TOPIC_PREFIX + b"/cmd"

# Intervalo de publicación de sensores (milisegundos)
INTERVALO_MQTT_MS = 3000

