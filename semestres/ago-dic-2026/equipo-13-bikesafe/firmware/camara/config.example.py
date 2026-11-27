# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   config.example.py   (va en la FREENOVE, la placa de la camara)
# Objetivo:  Datos del WiFi, del bot de Telegram y ajustes de la foto
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# PLANTILLA: copien este archivo como config.py y llenen sus datos.
# config.py NO se sube a GitHub (esta en .gitignore).

# ---------------- WiFi ----------------
# Debe ser una red de 2.4 GHz CON internet (para Telegram).
# El hotspot del celular funciona bien.
WIFI_SSID = "TU_RED"
WIFI_PASS = "TU_PASSWORD"     # "" si la red es abierta

# ---------------- Telegram ----------------
# Ponlo en True cuando ya tengas el token y el chat_id
# (la guia explica como sacarlos, son 5 minutos).
USAR_TELEGRAM = False
TELEGRAM_TOKEN = "123456789:AAAA-pega-aqui-tu-token"
TELEGRAM_CHAT_ID = "000000000"

# ---------------- Foto ----------------
# Tamanos: "QVGA" (320x240), "VGA" (640x480), "SVGA" (800x600)
TAMANO_FOTO = "VGA"
VOLTEAR_VERTICAL = False      # True si la foto sale de cabeza
ESPEJO = False                # True si sale como espejo
FOTOS_GUARDADAS = 5           # cuantas fotos guarda en su memoria
# Solo para camaras sin JPEG propio (como la GC0308 de su Freenove):
# True = foto a color. Si los colores salen raros, pongan False
# (blanco y negro, siempre se ve bien).
FOTO_A_COLOR = True

# ---------------- Enlace con la ESP32 normal ----------------
PIN_RX = 33      # <- llega del TX2 (GPIO17) de la ESP32 normal
PIN_TX = 32      # -> va al RX2 (GPIO16) de la ESP32 normal

# ---------------- Pagina web ----------------
# Si esta en True, puedes ver una foto en vivo escribiendo la IP
# de la Freenove en el navegador del celular (misma red WiFi).
USAR_WEB = True

# LED azul integrado de la Freenove (GPIO2): destella al tomar foto
PIN_LED = 2

# Cada cuantos segundos revisa si le escribieron al bot
# (botones Cerrar, Abrir, Foto, Estado, Buscar, Silenciar)
REVISAR_BOT_CADA_S = 3

# Reinicio automatico si algo se traba (watchdog). True SOLO para la
# exposicion: con True, Thonny ya no puede detener el programa.
USAR_WATCHDOG = False

# ---------------------------------------------------------------
# MQTT: mandar cada foto al servidor Python con IA (deteccion de
# personas). Si la laptop esta apagada no pasa nada: Telegram y la
# alarma funcionan igual.
# ---------------------------------------------------------------
USAR_MQTT = True
MQTT_BROKER = "broker.hivemq.com"   # el mismo que en la ESP32 normal
MQTT_PUERTO = 1883
MQTT_CLIENTE = "bikesafe-cam"
