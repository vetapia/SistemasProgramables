# ============================================================
# SmartLocker - main.py
# DHT11 + HC-SR04 + Teclado 4x4 + Buzzer + OLED + MQTT
# PIN: 2005 + # abre | D = cerrar manualmente | * = borrar
# MQTT: mensaje "1" abre, mensaje "0" cierra
# ============================================================

from time import sleep, ticks_ms, ticks_diff
import configuracion
from sensores import Sensores
from actuadores import Actuadores
from pantalla import Pantalla
from mqtt_cliente import MqttCliente

estado = "CERRADO"
entrada = ""
sens = Sensores()
act = Actuadores()
pant = Pantalla()
mqtt = None
ultimo_mqtt = 0


def abrir():
    global estado, entrada
    estado = "ABIERTO"
    entrada = ""
    act.beep(100, 2)
    if mqtt:
        mqtt.publicar(configuracion.TOPIC_ESTADO, estado)
    actualizar_pantalla()


def cerrar():
    global estado, entrada
    estado = "CERRADO"
    entrada = ""
    act.beep(60, 1)
    if mqtt:
        mqtt.publicar(configuracion.TOPIC_ESTADO, estado)
    actualizar_pantalla()


def on_cmd(msg):
    # Comandos MQTT conservados: 1 = abrir, 0 = cerrar.
    if msg == "1":
        abrir()
    elif msg == "0":
        cerrar()


def actualizar_pantalla():
    pant.dibujar(estado, entrada, sens.temp, sens.hum, sens.dist)


def procesar_tecla(k):
    global entrada
    if k is None:
        return

    # La tecla D cierra manualmente el casillero desde el teclado.
    if k == "D":
        cerrar()
        return

    if k == "*":
        entrada = ""
    elif k == "#":
        if entrada == configuracion.PIN_CORRECTO:
            abrir()
        else:
            act.alarma()
            entrada = ""
    elif k in "0123456789" and len(entrada) < 6:
        entrada += k

    actualizar_pantalla()


def publicar_sensores():
    sens.leer_dht()
    sens.leer_distancia()
    if mqtt:
        # Formato con unidades para MQTT Dash.
        mqtt.publicar(configuracion.TOPIC_TEMP, "{} C".format(sens.temp))
        mqtt.publicar(configuracion.TOPIC_HUM, "{} %".format(sens.hum))
        if sens.dist >= 0:
            mqtt.publicar(configuracion.TOPIC_DIST, "{:.1f} cm".format(sens.dist))
        else:
            mqtt.publicar(configuracion.TOPIC_DIST, "--")
        mqtt.publicar(configuracion.TOPIC_ESTADO, estado)


def main():
    global mqtt, ultimo_mqtt
    actualizar_pantalla()

    # Conserva el objeto aunque MQTT falle al inicio: mqtt.check() reintentara conectar.
    mqtt = MqttCliente(callback_cmd=on_cmd)
    try:
        mqtt.conectar()
        mqtt.publicar(configuracion.TOPIC_ESTADO, estado)
    except Exception as e:
        print("MQTT no disponible al iniciar; se intentara reconectar:", e)

    print("PIN: 2005 + # abre | D cierra | * borra")

    while True:
        k = act.leer_teclado()
        if k:
            procesar_tecla(k)

        if mqtt:
            mqtt.check()

        if ticks_diff(ticks_ms(), ultimo_mqtt) > configuracion.INTERVALO_MQTT_MS:
            publicar_sensores()
            actualizar_pantalla()
            ultimo_mqtt = ticks_ms()

        sleep(0.05)


main()

