# ============================================
# PLANTILLA: copien este archivo como config.py y llenen sus datos.
# config.py NO se sube a GitHub (esta en .gitignore).
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   config.example.py
# Objetivo:  Guardar en UN solo lugar todo lo que se puede ajustar:
#            pines, tarjetas autorizadas, umbrales, WiFi y MQTT
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# REGLA: si quieres cambiar algo del comportamiento del candado,
# casi siempre se cambia AQUI y no en main.py.

# ---------------------------------------------------------------
# 1. TARJETAS / LLAVEROS RFID QUE SI PUEDEN ABRIR
# ---------------------------------------------------------------
# Corre pruebas/p6_rfid.py, acerca tu llavero y copia aqui el
# codigo que aparece (8 letras/numeros). Puedes poner varios.
TARJETAS_AUTORIZADAS = [
    "00000000",      # <- cambia esto por el UID de tu llavero
]

# ---------------------------------------------------------------
# 2. PINES DE LA ESP32 NORMAL (los numeros son GPIO)
# ---------------------------------------------------------------
# Lector RFID RC522 (bus SPI)
PIN_RFID_SCK  = 18
PIN_RFID_MOSI = 23
PIN_RFID_MISO = 19
PIN_RFID_SDA  = 5      # tambien se llama SS o CS
PIN_RFID_RST  = 4

# Acelerometro MPU6050 (bus I2C)
PIN_I2C_SDA = 21
PIN_I2C_SCL = 22

# Sensor ultrasonico HC-SR04
PIN_TRIG = 26
PIN_ECHO = 27          # OJO: pasa por el divisor de 1k + 2k

# Actuadores
PIN_SERVO     = 13
PIN_BUZZER    = 25     # (+) del buzzer directo a D25 (sin el 2N2222)
PIN_LED_VERDE = 32
PIN_LED_ROJO  = 33

# Lazo anti-corte (un cable que va de este pin a GND)
PIN_LAZO = 14

# Enlace serie (UART2) con la placa de la camara
PIN_CAM_TX = 17        # ESP32 TX2 -> Freenove GPIO33 (RX)
PIN_CAM_RX = 16        # ESP32 RX2 <- Freenove GPIO32 (TX)

# ---------------------------------------------------------------
# 3. QUE PARTES ESTAN CONECTADAS
# ---------------------------------------------------------------
# Deja en False lo que todavia no tengas armado. Asi el programa
# principal funciona aunque falte una pieza (por ejemplo el RFID).
USAR_RFID         = True
USAR_ACELEROMETRO = True
USAR_ULTRASONICO  = True
USAR_LAZO         = False  # ponlo en True cuando conectes el lazo
USAR_CAMARA       = True
USAR_WIFI_MQTT    = True   # False = funciona sin red (solo Telegram)

# MIENTRAS NO LLEGA EL RFID: con True, el candado se asegura solo
# 5 segundos despues de prender. Sirve para probar la alarma sin
# llavero. Cuando ya tengas el RFID, regresalo a False.
ASEGURAR_AL_ARRANCAR = False

# ---------------------------------------------------------------
# 4. BUZZER Y SERVO
# ---------------------------------------------------------------
# True  = buzzer ACTIVO  (suena solo al darle 5 V)
# False = buzzer PASIVO  (necesita que le generemos el tono)
BUZZER_ACTIVO = True

# Angulos del servo. Ajustalos cuando armes el pestillo.
SERVO_ABIERTO = 0
SERVO_CERRADO = 90

# ---------------------------------------------------------------
# 5. SENSIBILIDAD DE LA ALARMA (acelerometro)
# ---------------------------------------------------------------
# Todo se mide en "g" (1 g = la gravedad). Entre mas chico el
# numero, mas sensible.
UMBRAL_TOQUE_G   = 0.18   # cambio minimo para contarlo como "toque"
UMBRAL_INCLINA_GRADOS = 25  # si la inclinan mas que esto...
TIEMPO_INCLINA_MS = 1200  # ...durante este tiempo = ROBO

# Nivel 2 (robo): tantos toques dentro de una ventana de tiempo
TOQUES_PARA_ROBO = 4
VENTANA_TOQUES_MS = 6000

# ---------------------------------------------------------------
# 6. ULTRASONICO (foto preventiva)
# ---------------------------------------------------------------
DISTANCIA_CERCA_CM = 50     # alguien a menos de 50 cm...
TIEMPO_CERCA_MS    = 3000   # ...durante 3 segundos = foto
ESPERA_ENTRE_FOTOS_MS = 20000  # no tomar fotos mas seguido que esto

# ---------------------------------------------------------------
# 7. ALARMA
# ---------------------------------------------------------------
DURACION_ALARMA_MS = 60000  # la sirena se calla sola al minuto

# ---------------------------------------------------------------
# 8. WIFI Y MQTT (solo si USAR_WIFI_MQTT = True)
# ---------------------------------------------------------------
WIFI_SSID = "TU_RED"
WIFI_PASS = "TU_PASSWORD"
MQTT_BROKER = "192.168.1.100"   # IP de la compu con Mosquitto
MQTT_PUERTO = 1883
MQTT_CLIENTE = "bikesafe-esp32"
PERIODO_PUBLICAR_MS = 2000      # cada cuanto manda los sensores
# Permitir abrir el candado desde el celular (para la demo).
PERMITIR_ABRIR_POR_MQTT = True
