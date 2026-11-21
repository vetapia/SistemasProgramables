# ============================================
# Proyecto:  SmartClass
# Archivo:   main.py
# Objetivo:  Nodo puerta (ESP32-CAM): detecta personas, envía fotos al servidor y muestra el resultado en anillo, buzzer y pantalla
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
# SmartClass - NODO PUERTA (ESP32 con camara)
# Detecta a la persona, enciende el anillo, manda fotos al servidor y muestra el resultado
# en el anillo, el buzzer y la pantalla. Tambien hace el registro de alumnos nuevos.
import gc
import json
import time

import camera
import machine
import neopixel
from machine import Pin, SoftI2C

import red
import ssd1306
from hcsr04 import HCSR04

try:
    import config
    USAR_WDT = getattr(config, "USAR_WDT", False)
except ImportError:
    USAR_WDT = False

# ---------------- Ajustes (puedes cambiarlos) ----------------
PIN_OLED_SDA = 13
PIN_OLED_SCL = 14
PIN_TRIG = 32
PIN_ECHO = 33
PIN_IR = 15
PIN_ANILLO = 2
PIN_BUZZER = 12
LEDS_ANILLO = 12

IR_DETECTA = 0              # valor que da el sensor IR cuando hay alguien (0 en la mayoria)
DIST_PERSONA_CM = 60        # una persona a menos de esta distancia activa el reconocimiento
INTENTOS_RECONOCER = 4      # fotos que se prueban antes de declarar "no registrado"
ESPERA_RESULTADO_MS = 3000  # cuanto espera la respuesta del servidor por cada foto
BRILLO_BLANCO = 120         # 0 a 255: luz para iluminar el rostro
BRILLO_COLOR = 80           # 0 a 255: verde, rojo y azul
RESOLUCION = camera.FRAME_VGA
CALIDAD_JPEG = 15
INTERVALO_SENSORES_MS = 3000   # cada cuanto se publican distancia e IR hacia la pagina
TIMEOUT_CAPTURA_REGISTRO_MS = 100000
TIMEOUT_NOMBRE_MS = 300000

# ---------------- Topicos MQTT ----------------
CLIENT_ID = b"SmartClass_Puerta"
T_FRAME = b"smartclass/cam/frame"
T_RESULTADO = b"smartclass/puerta/resultado"
T_CMD = b"smartclass/puerta/cmd"
T_CFG_WIFI = b"smartclass/config/wifi"
T_CLIMA = b"smartclass/s/clima"
T_DIST = b"smartclass/s/distancia"
T_IR = b"smartclass/s/ir"
T_NODO = b"smartclass/nodo/puerta"
TOPICOS = (T_RESULTADO, T_CMD, T_CLIMA, T_CFG_WIFI)

# ---------------- Colores ----------------
C_APAGADO = (0, 0, 0)
C_BLANCO = (BRILLO_BLANCO, BRILLO_BLANCO, BRILLO_BLANCO)
C_VERDE = (0, BRILLO_COLOR, 0)
C_ROJO = (BRILLO_COLOR, 0, 0)
C_AZUL = (0, 0, BRILLO_COLOR)

# ---------------- Hardware ----------------
sensor_ir = Pin(PIN_IR, Pin.IN)
sensor_dist = HCSR04(trigger_pin=PIN_TRIG, echo_pin=PIN_ECHO)
buzzer = Pin(PIN_BUZZER, Pin.OUT, value=0)
anillo = neopixel.NeoPixel(Pin(PIN_ANILLO), LEDS_ANILLO)
i2c = SoftI2C(scl=Pin(PIN_OLED_SCL), sda=Pin(PIN_OLED_SDA), freq=400000)
try:
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
except OSError:
    oled = None
    print("Pantalla OLED no detectada")

# ---------------- Estado compartido ----------------
wdt = None
resultado = None          # ultima respuesta del servidor a una foto
cmd = None                # ultimo comando del servidor (registro)
wifi_nuevo = None         # red Wi-Fi nueva enviada desde la pagina
temp = None
hum = None
t_clima = 0
lineas_actuales = []
ultima_dist = None
ultimo_ir = False
presente_cuenta = 0
ausente_cuenta = 0
ultima_lectura = 0
ultimo_pie = 0
ultimo_latido = 0
ultimo_envio_sensores = 0


def alimentar():
    if wdt is not None:
        wdt.feed()


# ---------------- Pantalla ----------------
def envolver(texto, ancho=16):
    lineas = []
    actual = ""
    for palabra in texto.split():
        while len(palabra) > ancho:
            if actual:
                lineas.append(actual)
                actual = ""
            lineas.append(palabra[:ancho])
            palabra = palabra[ancho:]
        if not actual:
            actual = palabra
        elif len(actual) + 1 + len(palabra) <= ancho:
            actual += " " + palabra
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def dibujar():
    if oled is None:
        return
    oled.fill(0)
    y = 0
    for linea in lineas_actuales[:5]:
        oled.text(linea, 0, y)
        y += 10
    vigente = temp is not None and time.ticks_diff(time.ticks_ms(), t_clima) < 30000
    t = "%d" % temp if vigente else "--"
    h = "%d" % hum if vigente and hum is not None else "--"
    oled.text("T:%sC  H:%s%%" % (t, h), 0, 56)
    oled.show()


def pantalla(lineas):
    global lineas_actuales
    lineas_actuales = lineas
    try:
        dibujar()
    except OSError:
        pass


def reposo():
    luz(C_APAGADO)
    pantalla(["SmartClass", "Pase de lista", "", "Acerquese al", "sensor"])


# ---------------- Anillo y buzzer ----------------
def luz(color):
    anillo.fill(color)
    anillo.write()


def pitar(ms):
    buzzer.value(1)
    time.sleep_ms(ms)
    buzzer.value(0)


# ---------------- Camara ----------------
def iniciar_camara():
    try:
        camera.deinit()
    except Exception:
        pass
    for tam in (RESOLUCION, camera.FRAME_QVGA):
        try:
            camera.init(0,
                        d0=4, d1=5, d2=18, d3=19, d4=36, d5=39, d6=34, d7=35,
                        xclk=21, pclk=22, vsync=25, href=23,
                        siod=26, sioc=27, pwdn=-1, reset=-1,
                        format=camera.JPEG,
                        framesize=tam,
                        xclk_freq=camera.XCLK_20MHz,
                        fb_location=camera.PSRAM)
            camera.quality(CALIDAD_JPEG)
            print("Camara lista")
            return True
        except Exception as e:
            print("Camara fallo:", e)
            try:
                camera.deinit()
            except Exception:
                pass
    return False


def tomar_foto():
    try:
        camera.capture()          # descarta el cuadro viejo que queda en el buffer
    except Exception:
        pass
    gc.collect()
    for _ in range(5):
        try:
            foto = camera.capture()
            if foto:
                return foto
        except Exception as e:
            print("Error de captura:", e)
        time.sleep_ms(300)
    return None


def enviar_frame(client):
    foto = tomar_foto()
    if not foto:
        return False
    red.publicar(client, T_FRAME, foto)
    foto = None
    gc.collect()
    return True


# ---------------- Mensajes MQTT ----------------
def on_msg(topico, msg):
    global resultado, cmd, temp, hum, t_clima, wifi_nuevo
    try:
        if topico == T_RESULTADO:
            resultado = json.loads(msg)
        elif topico == T_CMD:
            cmd = json.loads(msg)
        elif topico == T_CLIMA:
            datos = json.loads(msg)
            temp = datos.get("temp")
            hum = datos.get("hum")
            t_clima = time.ticks_ms()
        elif topico == T_CFG_WIFI:
            wifi_nuevo = json.loads(msg)
    except (ValueError, TypeError, AttributeError):
        pass


# ---------------- Sensores ----------------
def leer_distancia():
    try:
        return round(sensor_dist.distance_cm(), 1)
    except OSError:
        return None


def actualizar_sensores():
    """Lee los sensores cada 150 ms y cuenta lecturas seguidas con/sin persona."""
    global ultima_lectura, ultima_dist, ultimo_ir, presente_cuenta, ausente_cuenta
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultima_lectura) < 150:
        return
    ultima_lectura = ahora
    ultima_dist = leer_distancia()
    ultimo_ir = (sensor_ir.value() == IR_DETECTA)
    detecta = ultimo_ir or (ultima_dist is not None and 0 < ultima_dist < DIST_PERSONA_CM)
    if detecta:
        presente_cuenta += 1
        ausente_cuenta = 0
    else:
        presente_cuenta = 0
        ausente_cuenta += 1


def tareas_periodicas(client):
    """Latido, sensores hacia la pagina y refresco del pie de la pantalla."""
    global ultimo_latido, ultimo_envio_sensores, ultimo_pie
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_latido) >= 10000:
        ultimo_latido = ahora
        red.publicar(client, T_NODO, "online")
    if time.ticks_diff(ahora, ultimo_envio_sensores) >= INTERVALO_SENSORES_MS:
        ultimo_envio_sensores = ahora
        if ultima_dist is not None:
            red.publicar(client, T_DIST, str(ultima_dist))
        red.publicar(client, T_IR, "1" if ultimo_ir else "0")
    if time.ticks_diff(ahora, ultimo_pie) >= 5000:
        ultimo_pie = ahora
        pantalla(lineas_actuales)


def esperar(client, ms):
    """Pausa que sigue atendiendo MQTT y el watchdog."""
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < ms:
        alimentar()
        client.check_msg()
        tareas_periodicas(client)
        time.sleep_ms(20)


# ---------------- Reconocimiento ----------------
def esperar_resultado(client):
    global resultado
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < ESPERA_RESULTADO_MS:
        alimentar()
        client.check_msg()
        if resultado is not None:
            r = resultado
            resultado = None
            return r
        time.sleep_ms(20)
    return None


def mostrar_exito(client, r):
    luz(C_VERDE)
    pitar(150)
    lineas = ["BIENVENIDO"] + envolver(r.get("nombre_oled", ""))[:2]
    lineas += ["", "Hora: " + str(r.get("hora", ""))]
    pantalla(lineas)
    esperar(client, 3000)


def mostrar_fallo(client, hubo_desconocido, sin_servidor):
    luz(C_ROJO)
    pitar(1200)
    if sin_servidor:
        pantalla(["Sin conexion", "con el servidor"])
    elif hubo_desconocido:
        pantalla(envolver("Alumno no registrado, intente nuevamente"))
    else:
        pantalla(["No se detecta", "su rostro.", "Mire la camara", "e intente", "nuevamente"])
    esperar(client, 3000)


def ciclo_reconocimiento(client):
    """Devuelve True si terminó el ciclo (con exito o fallo), False si la persona se fue."""
    global resultado
    luz(C_BLANCO)
    pantalla(["Reconociendo...", "", "Mire la camara"])
    esperar(client, 400)                 # el anillo ilumina y la camara se ajusta
    hubo_desconocido = False
    hubo_respuesta = False
    for _ in range(INTENTOS_RECONOCER):
        alimentar()
        actualizar_sensores()
        if ausente_cuenta >= 4:          # la persona se alejo
            reposo()
            return False
        resultado = None
        if not enviar_frame(client):
            continue
        r = esperar_resultado(client)
        if r is None:
            continue
        hubo_respuesta = True
        estado = r.get("estado")
        if estado == "reconocido":
            mostrar_exito(client, r)
            return True
        if estado == "desconocido":
            hubo_desconocido = True
    mostrar_fallo(client, hubo_desconocido, not hubo_respuesta)
    return True


# ---------------- Registro de alumnos ----------------
def modo_registro(client):
    global cmd
    cmd = None
    luz(C_AZUL)
    pantalla(["REGISTRO", "", "Preparese..."])
    esperar(client, 2000)
    luz(C_BLANCO)        # misma luz que en el reconocimiento: mejores resultados
    pantalla(["REGISTRO", "Mire la camara", "y mueva un poco", "la cabeza"])
    t0 = time.ticks_ms()
    t_listo = None
    while True:
        alimentar()
        client.check_msg()
        if cmd:
            c = cmd
            cmd = None
            accion = c.get("accion")
            if accion == "registro_cancelado":
                break
            if accion == "registro_listo" and t_listo is None:
                t_listo = time.ticks_ms()
                luz(C_VERDE)
                pitar(150)
                pantalla(["Registro listo", "", "Escriba el nombre", "en la pagina"])
            elif accion == "registro_ok":
                luz(C_VERDE)
                pitar(150)
                pantalla(["Alumno", "registrado"] + envolver(c.get("nombre_oled", ""))[:2])
                esperar(client, 3000)
                break
        if t_listo is None:
            if time.ticks_diff(time.ticks_ms(), t0) > TIMEOUT_CAPTURA_REGISTRO_MS:
                break
            enviar_frame(client)
            esperar(client, 450)
        else:
            if time.ticks_diff(time.ticks_ms(), t_listo) > TIMEOUT_NOMBRE_MS:
                break
            esperar(client, 200)
    reposo()


# ---------------- Comandos desde la pagina ----------------
def procesar_comandos(client):
    global cmd, wifi_nuevo
    if wifi_nuevo:
        datos = wifi_nuevo
        wifi_nuevo = None
        ssid = str(datos.get("ssid", "")).strip()
        clave = str(datos.get("password", ""))
        actual = red.cargar()
        if ssid and not (ssid == actual["ssid"] and clave == actual["password"]):
            pantalla(["Red nueva:", ssid[:16], "Reiniciando..."])
            red.guardar(ssid, clave)
            time.sleep_ms(1500)
            machine.reset()
    if cmd:
        c = cmd
        cmd = None
        accion = c.get("accion")
        if accion == "registro_inicio":
            modo_registro(client)
        elif accion == "registro_ok":
            luz(C_VERDE)
            pitar(150)
            pantalla(["Alumno", "registrado"] + envolver(c.get("nombre_oled", ""))[:2])
            esperar(client, 3000)
            reposo()


# ---------------- Programa principal ----------------
def reconectar(datos):
    return red.conectar_servidor(datos, CLIENT_ID, on_msg, TOPICOS, alimentar, pantalla)


def main():
    global wdt
    pantalla(["SmartClass", "Iniciando..."])
    if USAR_WDT:
        wdt = machine.WDT(timeout=30000)

    datos = red.asegurar_wifi(alimentar, pantalla)
    if not iniciar_camara():
        pantalla(["Error de camara", "Reiniciando..."])
        time.sleep(5)
        machine.reset()
    client = reconectar(datos)
    reposo()

    esperando_salida = False
    t_salida = 0
    while True:
        try:
            alimentar()
            client.check_msg()
            procesar_comandos(client)
            actualizar_sensores()
            tareas_periodicas(client)

            ahora = time.ticks_ms()
            if esperando_salida and (presente_cuenta == 0
                                     or time.ticks_diff(ahora, t_salida) > 20000):
                esperando_salida = False
            if presente_cuenta >= 2 and not esperando_salida:
                ciclo_reconocimiento(client)
                reposo()
                esperando_salida = True
                t_salida = time.ticks_ms()
            time.sleep_ms(30)
        except OSError as e:
            print("Conexion perdida:", e)
            try:
                client.sock.close()
            except Exception:
                pass
            gc.collect()
            time.sleep_ms(1500)
            client = reconectar(red.cargar())
            reposo()
        except Exception as e:
            print("Error:", repr(e))
            gc.collect()
            time.sleep_ms(500)


main()
