# ============================================
# Proyecto:   AuraBot
# Archivo:    dispositivos.py (HAL)
# Objetivo:   Control de sensores y actuadores (3 Servos, OLED, Relevador, DFPlayer)
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:    Sistemas Programables — ISC TecNM León
# Semestre:   ago-dic-2026
# ============================================

from machine import Pin, PWM, ADC, I2C, UART, time_pulse_us
import time

try:
    import ssd1306
    TIENE_OLED = True
except ImportError:
    TIENE_OLED = False
    print("Aviso: Librería ssd1306 no encontrada.")

# --- SENSORES ---
pir = Pin(13, Pin.IN)
trig = Pin(25, Pin.OUT)
echo = Pin(26, Pin.IN)

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)  # Lectura completa de 0 a 3.3V

# --- ACTUADORES ---
relevador = Pin(23, Pin.OUT)
relevador.value(0)

# Servomotores (50Hz estándar SG90)
servo_cabeza = PWM(Pin(18), freq=50)
servo_brazo_izq = PWM(Pin(19), freq=50)
servo_brazo_der = PWM(Pin(27), freq=50)

# Pantalla OLED I2C
oled = None
if TIENE_OLED:
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    except Exception as e:
        print("Error iniciando OLED:", e)

# DFPlayer Mini (UART 2)
dfplayer = UART(2, baudrate=9600, tx=17, rx=16)


# ============================================
# FUNCIONES DE LECTURA (SENSORES)
# ============================================

def leer_pir():
    return pir.value()

def leer_distancia():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    duracion = time_pulse_us(echo, 1, 30000)
    if duracion < 0:
        return -1
    distancia = (duracion * 0.0343) / 2
    return round(distancia, 1)

def leer_luz():
    valor_crudo = ldr.read()  # 0 a 4095
    porcentaje = int((valor_crudo / 4095) * 100)
    return porcentaje


# ============================================
# FUNCIONES DE SERVOMOTORES (CABEZA Y BRAZOS)
# ============================================

def mover_servo(servo, angulo):
    if angulo < 0: angulo = 0
    if angulo > 180: angulo = 180
    duty = int((angulo / 180) * 102 + 26)
    servo.duty(duty)

def reposo_servos():
    """Centra cabeza y baja ambos brazos escalonadamente"""
    mover_servo(servo_cabeza, 90)
    time.sleep(0.15)
    # Nota: Como los brazos van en lados opuestos, sus ángulos van invertidos
    mover_servo(servo_brazo_izq, 20)
    time.sleep(0.15)
    mover_servo(servo_brazo_der, 160)

def saludar_servos():
    """Gira cabeza y levanta ambos brazos para saludar"""
    mover_servo(servo_cabeza, 70)
    time.sleep(0.15)
    mover_servo(servo_brazo_izq, 130)
    time.sleep(0.15)
    mover_servo(servo_brazo_der, 50)
    time.sleep(0.6)
    
    mover_servo(servo_cabeza, 110)
    time.sleep(0.6)
    reposo_servos()

def respirar_servos():
    """Movimiento lento de brazos y cabeza para guiar inhalación/exhalación"""
    # Inhalar (suben brazos despacio)
    for paso in range(0, 61, 5):
        mover_servo(servo_brazo_izq, 20 + paso)
        mover_servo(servo_brazo_der, 160 - paso)
        time.sleep(0.08)
    time.sleep(0.5)
    # Exhalar (bajan brazos despacio)
    for paso in range(60, -1, -5):
        mover_servo(servo_brazo_izq, 20 + paso)
        mover_servo(servo_brazo_der, 160 - paso)
        time.sleep(0.08)


# ============================================
# FUNCIONES DE RELEVADOR, OLED Y AUDIO
# ============================================

def controlar_relevador(estado):
    if estado == "encender":
        relevador.value(1)
    elif estado == "apagar":
        relevador.value(0)

def cambiar_oled(expresion):
    if not oled:
        return
    oled.fill(0)
    if expresion == "feliz":
        oled.text("^   ^", 42, 20)
        oled.text("\\___/", 42, 40)
    elif expresion == "neutral":
        oled.text("o   o", 42, 20)
        oled.text(" --- ", 42, 40)
    elif expresion == "apagada":
        pass  # Deja la pantalla en negro
    oled.show()

def set_volumen_dfplayer(volumen=20):
    if volumen > 30: volumen = 30
    comando = bytearray([0x7E, 0xFF, 0x06, 0x06, 0x00, 0x00, volumen, 0xEF])
    dfplayer.write(comando)

def reproducir_pista_mp3(numero_pista):
    comando = bytearray([0x7E, 0xFF, 0x06, 0x12, 0x00, 0x00, numero_pista, 0xEF])
    dfplayer.write(comando)

def detener_audio():
    comando = bytearray([0x7E, 0xFF, 0x06, 0x16, 0x00, 0x00, 0x00, 0xEF])
    dfplayer.write(comando)
