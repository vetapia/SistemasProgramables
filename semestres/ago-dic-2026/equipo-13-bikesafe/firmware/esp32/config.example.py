# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   config.example.py
# Objetivo:  Guardar en UN solo lugar todo lo que se puede ajustar:
#            pines, piezas conectadas, umbrales, WiFi y MQTT
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# PLANTILLA: copien este archivo como config.py y llenen sus datos.
# config.py NO se sube a GitHub (esta en .gitignore).
#
# REGLA: si quieres cambiar algo del comportamiento del candado,
# casi siempre se cambia AQUI y no en main.py.

# ---------------------------------------------------------------
# 1. PINES DE LA ESP32 NORMAL (los numeros son GPIO)
# ---------------------------------------------------------------
# Acelerometro MPU6050 (bus I2C)
PIN_I2C_SDA = 21
PIN_I2C_SCL = 22

# Sensor ultrasonico HC-SR04
PIN_TRIG = 26
PIN_ECHO = 27          # OJO: pasa por el divisor de 1k + 2k

# Sensor magnetico del cerrojo (reed switch): una patita al pin y la
# otra a GND. El iman va en la punta del cable / en el pasador.
PIN_REED = 18

# Actuadores
PIN_SERVO     = 13
PIN_BUZZER    = 25     # (+) del buzzer directo a D25 (sin el 2N2222)

# LED RGB (cada color con su resistencia de 220 ohm)
PIN_RGB_R = 33         # el rojo va donde estaba el LED rojo
PIN_RGB_G = 32         # el verde va donde estaba el LED verde
PIN_RGB_B = 19         # el azul es el unico cable nuevo
# Si todavia no tienen el RGB, se usan los 2 LEDs de antes:
PIN_LED_VERDE = 32
PIN_LED_ROJO  = 33

# Lazo anti-corte (un cable que va de este pin a GND)
PIN_LAZO = 14

# Sensor de movimiento PIR HC-SR501 (OUT), opcional
PIN_PIR = 34           # D34 solo sirve como entrada: perfecto para el PIR

# Enlace serie (UART2) con la placa de la camara
PIN_CAM_TX = 17        # ESP32 TX2 -> Freenove GPIO33 (RX)
PIN_CAM_RX = 16        # ESP32 RX2 <- Freenove GPIO32 (TX)

# ---------------------------------------------------------------
# 2. QUE PARTES ESTAN CONECTADAS
# ---------------------------------------------------------------
# Deja en False lo que todavia no tengas armado. Asi el programa
# principal funciona aunque falte una pieza.
USAR_ACELEROMETRO = True
USAR_ULTRASONICO  = True
USAR_SENSOR_CERROJO = True # reed switch (3er sensor)
USAR_LAZO         = True
USAR_PIR          = False  # True cuando conecten el PIR
USAR_CAMARA       = True
USAR_WIFI_MQTT    = True   # False = funciona sin red (solo Telegram)
USAR_LED_RGB      = True   # False = LEDs verde y rojo de antes

# MODO PRUEBA: con True, el candado se asegura solo 5 segundos
# despues de prender (para probar la alarma sin Telegram).
ASEGURAR_AL_ARRANCAR = False

# ---------------------------------------------------------------
# 3. BUZZER, SERVO Y LED
# ---------------------------------------------------------------
# True  = buzzer ACTIVO  (suena solo al darle 5 V)
# False = buzzer PASIVO  (necesita que le generemos el tono)
BUZZER_ACTIVO = True

# Angulos del servo. Ajustalos cuando armes el pestillo.
SERVO_ABIERTO = 0
SERVO_CERRADO = 90

# LED RGB: False = catodo comun (patita larga a GND)
#          True  = anodo comun  (patita larga a 3.3 V)
# Si al prender sale "al reves" (todo prendido menos un color),
# cambien este valor. Prueba: pruebas/e13_led_rgb.py
RGB_ANODO_COMUN = False

# ---------------------------------------------------------------
# 4. SENSIBILIDAD DE LA ALARMA (acelerometro)
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
# 5. ULTRASONICO (foto preventiva)
# ---------------------------------------------------------------
DISTANCIA_CERCA_CM = 50     # alguien a menos de 50 cm...
TIEMPO_CERCA_MS    = 3000   # ...durante 3 segundos = foto
ESPERA_ENTRE_FOTOS_MS = 20000  # no tomar fotos mas seguido que esto

# ---------------------------------------------------------------
# 6. SENSOR MAGNETICO DEL CERROJO
# ---------------------------------------------------------------
REED_CERRADO_ES = 0          # 0 = el pin lee 0 con el iman cerca
REED_OBLIGATORIO = True      # no cierra si el cable no esta metido
TIEMPO_CERROJO_ABIERTO_MS = 500  # abierto asi de tiempo asegurada = ROBO

# ---------------------------------------------------------------
# 7. IA (la decision la toma ESTA placa, no la laptop)
# ---------------------------------------------------------------
# El servidor solo manda "vi una persona con 82 %". Aqui se decide:
IA_CONFIANZA_MINIMA = 0.45   # menos que esto se ignora
IA_VENTANA_MS = 120000       # se recuerdan las personas de 2 minutos
IA_PERSONAS_PARA_ROBO = 2    # 2 personas + la bici se movio = ROBO

# ---------------------------------------------------------------
# 8. ALARMA
# ---------------------------------------------------------------
DURACION_ALARMA_MS = 60000  # la sirena se calla sola al minuto
FOTOS_EXTRA_ROBO   = 2      # en un robo: 1 foto + estas extra
ESPERA_RAFAGA_MS   = 6000   # tiempo entre fotos de la rafaga
DURACION_BUSCAR_MS = 5000   # boton "Buscar": cuanto suena

# Reinicio automatico (watchdog). True SOLO para la exposicion: si
# algo se traba, la placa se reinicia sola. Con True, Thonny no podra
# detener el programa (la placa se reinicia 20 s despues de STOP).
USAR_WATCHDOG = False

# ---------------------------------------------------------------
# 9. WIFI Y MQTT (solo si USAR_WIFI_MQTT = True)
# ---------------------------------------------------------------
WIFI_SSID = "TU_RED"
WIFI_PASS = "TU_PASSWORD"       # "" si la red es abierta
MQTT_BROKER = "broker.hivemq.com"   # o la IP de la laptop con Mosquitto
MQTT_PUERTO = 1883
MQTT_CLIENTE = "bikesafe-esp32"
PERIODO_PUBLICAR_MS = 2000      # cada cuanto manda los sensores
# Clave secreta para FIRMAR los mensajes MQTT (ver firma.py). Debe
# ser IGUAL a la de servidor/clave_mqtt.txt. Sin clave, el candado
# no acepta "abrir" por MQTT (el broker publico lo ve cualquiera).
MQTT_CLAVE = ""
# Permitir abrir el candado desde el dashboard (solo con clave).
PERMITIR_ABRIR_POR_MQTT = True
