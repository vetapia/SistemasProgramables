# ============================================
# Proyecto:  SmartClass
# Archivo:   main.py
# Objetivo:  Nodo dispensador (ESP32): sensor IR con bomba de gel, lectura del DHT11 y ventilador automático
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
# SmartClass - NODO DISPENSADOR (ESP32 DevKit)
# Sensor IR + bomba (dispensador de gel), DHT11 y ventilador automatico.
import gc
import json
import time

import dht
import machine
from machine import Pin

import red

try:
    import config
    USAR_WDT = getattr(config, "USAR_WDT", False)
except ImportError:
    USAR_WDT = False

# ---------------- Ajustes (puedes cambiarlos) ----------------
PIN_DHT = 4
PIN_IR = 18
PIN_RELE_BOMBA = 26
PIN_RELE_VENT = 27

IR_DETECTA = 0            # valor que da el sensor IR cuando hay una mano (0 en la mayoria)
RELE_ACTIVO = 1           # valor que ENCIENDE el relevador (cambia a 0 si tu modulo es activo en bajo)
BOMBA_MS = 1200           # cuanto tiempo corre la bomba por cada mano
BOMBA_ESPERA_MS = 2500    # tiempo minimo entre dosis
TEMP_ENCENDER = 30        # el ventilador enciende con MAS de esta temperatura
TEMP_APAGAR = 28          # y se apaga con esta temperatura o menos
INTERVALO_CLIMA_MS = 10000    # cada cuanto lee y publica temperatura y humedad
INTERVALO_IR_MS = 15000       # el IR se publica al cambiar y, como minimo, cada tanto
INTERVALO_ESTADO_MS = 15000   # estado de bomba y ventilador (ademas de al cambiar)

# ---------------- Topicos MQTT ----------------
CLIENT_ID = b"SmartClass_Dispensador"
T_CLIMA = b"smartclass/s/clima"
T_IR_DISP = b"smartclass/s/ir_disp"
T_NODO = b"smartclass/nodo/dispensador"
T_CFG_WIFI = b"smartclass/config/wifi"
T_BOMBA = b"smartclass/a/bomba"     # "1" = una dosis (para pruebas)
T_VENT = b"smartclass/a/vent"       # "1" encender, "0" apagar, "auto" = automatico
T_E_BOMBA = b"smartclass/e/bomba"   # estado: "ON" / "OFF" (lo guarda el servidor en Firebase)
T_E_VENT = b"smartclass/e/vent"
TOPICOS = (T_CFG_WIFI, T_BOMBA, T_VENT)

# ---------------- Hardware ----------------
RELE_APAGADO = 1 - RELE_ACTIVO
sensor_dht = dht.DHT11(Pin(PIN_DHT))
sensor_ir = Pin(PIN_IR, Pin.IN)
rele_bomba = Pin(PIN_RELE_BOMBA, Pin.OUT, value=RELE_APAGADO)
rele_vent = Pin(PIN_RELE_VENT, Pin.OUT, value=RELE_APAGADO)

# ---------------- Estado ----------------
wdt = None
temp = None
hum = None
t_temp = 0
ventilador_encendido = False
vent_manual = None        # None = automatico, True/False = forzado desde MQTT
bomba_hasta = 0
bomba_libre_en = 0
bomba_activa = False
dosis_pedida = False
wifi_nuevo = None
ultimo_ir_publicado = None
estados_pendientes = True


def alimentar():
    if wdt is not None:
        wdt.feed()


def mostrar(lineas):
    print(" | ".join(lineas))


# ---------------- Mensajes MQTT ----------------
def on_msg(topico, msg):
    global wifi_nuevo, vent_manual, dosis_pedida
    try:
        if topico == T_CFG_WIFI:
            wifi_nuevo = json.loads(msg)
        elif topico == T_BOMBA:
            if msg == b"1":
                dosis_pedida = True
        elif topico == T_VENT:
            if msg == b"1":
                vent_manual = True
            elif msg == b"0":
                vent_manual = False
            elif msg == b"auto":
                vent_manual = None
    except (ValueError, TypeError, AttributeError):
        pass


# ---------------- Bomba ----------------
def publicar_estados(client):
    global estados_pendientes
    estados_pendientes = False
    red.publicar(client, T_E_BOMBA, "ON" if bomba_activa else "OFF")
    red.publicar(client, T_E_VENT, "ON" if ventilador_encendido else "OFF")


def iniciar_dosis(ahora):
    global bomba_activa, bomba_hasta, bomba_libre_en, estados_pendientes
    estados_pendientes = True
    rele_bomba.value(RELE_ACTIVO)
    bomba_activa = True
    bomba_hasta = time.ticks_add(ahora, BOMBA_MS)
    bomba_libre_en = time.ticks_add(ahora, BOMBA_MS + BOMBA_ESPERA_MS)


def atender_bomba(client):
    global bomba_activa, dosis_pedida, ultimo_ir_publicado, estados_pendientes
    ahora = time.ticks_ms()
    mano = (sensor_ir.value() == IR_DETECTA)
    if bomba_activa and time.ticks_diff(ahora, bomba_hasta) >= 0:
        rele_bomba.value(RELE_APAGADO)
        bomba_activa = False
        estados_pendientes = True
    libre = (not bomba_activa) and time.ticks_diff(ahora, bomba_libre_en) >= 0
    if libre and (mano or dosis_pedida):
        iniciar_dosis(ahora)
    dosis_pedida = False
    if mano != ultimo_ir_publicado:
        ultimo_ir_publicado = mano
        red.publicar(client, T_IR_DISP, "1" if mano else "0")
    return mano


# ---------------- Clima y ventilador ----------------
def leer_clima(client):
    global temp, hum, t_temp
    try:
        sensor_dht.measure()
        temp = sensor_dht.temperature()
        hum = sensor_dht.humidity()
        t_temp = time.ticks_ms()
    except OSError as e:
        print("Error DHT11:", e)
        return
    red.publicar(client, T_CLIMA, json.dumps({"temp": temp, "hum": hum}))
    print("Clima -> Temp:%s C | Hum:%s %%" % (temp, hum))


def decidir_ventilador():
    global ventilador_encendido, estados_pendientes
    if vent_manual is not None:
        objetivo = vent_manual
    else:
        sin_dato = temp is None or time.ticks_diff(time.ticks_ms(), t_temp) > 60000
        if sin_dato:
            objetivo = False              # sin lectura confiable: apagado
        elif temp > TEMP_ENCENDER:
            objetivo = True
        elif temp <= TEMP_APAGAR:
            objetivo = False
        else:
            objetivo = ventilador_encendido   # zona intermedia: se queda como esta
    if objetivo != ventilador_encendido:
        ventilador_encendido = objetivo
        estados_pendientes = True
        rele_vent.value(RELE_ACTIVO if objetivo else RELE_APAGADO)
        print("Ventilador", "ENCENDIDO" if objetivo else "apagado")


# ---------------- Wi-Fi nuevo desde la pagina ----------------
def procesar_wifi_nuevo():
    global wifi_nuevo
    if not wifi_nuevo:
        return
    datos = wifi_nuevo
    wifi_nuevo = None
    ssid = str(datos.get("ssid", "")).strip()
    clave = str(datos.get("password", ""))
    actual = red.cargar()
    if ssid and not (ssid == actual["ssid"] and clave == actual["password"]):
        print("Red nueva recibida:", ssid, "- reiniciando")
        red.guardar(ssid, clave)
        time.sleep_ms(1500)
        machine.reset()


# ---------------- Programa principal ----------------
def reconectar(datos):
    return red.conectar_servidor(datos, CLIENT_ID, on_msg, TOPICOS, alimentar, mostrar)


def main():
    global wdt
    if USAR_WDT:
        wdt = machine.WDT(timeout=30000)
    datos = red.asegurar_wifi(alimentar, mostrar)
    client = reconectar(datos)

    ultimo_clima = time.ticks_add(time.ticks_ms(), -INTERVALO_CLIMA_MS)
    ultimo_latido = 0
    ultimo_ir_envio = 0
    ultimo_estado = 0
    while True:
        try:
            alimentar()
            client.check_msg()
            procesar_wifi_nuevo()
            mano = atender_bomba(client)
            ahora = time.ticks_ms()

            if time.ticks_diff(ahora, ultimo_clima) >= INTERVALO_CLIMA_MS:
                ultimo_clima = ahora
                leer_clima(client)
            decidir_ventilador()

            if time.ticks_diff(ahora, ultimo_latido) >= 10000:
                ultimo_latido = ahora
                red.publicar(client, T_NODO, "online")
            if time.ticks_diff(ahora, ultimo_ir_envio) >= INTERVALO_IR_MS:
                ultimo_ir_envio = ahora
                red.publicar(client, T_IR_DISP, "1" if mano else "0")
            if estados_pendientes or time.ticks_diff(ahora, ultimo_estado) >= INTERVALO_ESTADO_MS:
                ultimo_estado = ahora
                publicar_estados(client)
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
        except Exception as e:
            print("Error:", repr(e))
            gc.collect()
            time.sleep_ms(500)


main()
