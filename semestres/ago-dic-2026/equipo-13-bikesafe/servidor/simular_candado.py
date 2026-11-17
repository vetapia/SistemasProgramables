# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/simular_candado.py
# Objetivo:  Probar el servidor sin las placas: publica sensores y una
#            foto por MQTT como si fueran la ESP32 y la Freenove
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Uso:  python simular_candado.py  ruta/a/una_foto.jpg
# (con mosquitto y mqtt_bridge.py ya corriendo)

import json
import sys
import time

import paho.mqtt.client as mqtt

import config as cfg

recibidos = []


def al_recibir(cliente, userdata, msg):
    recibidos.append((msg.topic, msg.payload.decode(errors="replace")))
    print("  <- {}: {}".format(msg.topic, msg.payload.decode(errors="replace")[:120]))


c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bikesafe-simulador")
c.on_message = al_recibir
c.connect(cfg.BROKER, cfg.PUERTO)
c.subscribe("bikesafe/cmd")
c.subscribe("bikesafe/ia/resultado")
c.loop_start()
time.sleep(0.5)

print("-> estado ASEGURADA y 3 lecturas de sensores")
c.publish("bikesafe/estado", "ASEGURADA", retain=True)
for dist, mov, inc in ((120.0, 0.02, 1.1), (45.0, 0.05, 1.3), (30.0, 0.31, 2.0)):
    c.publish("bikesafe/sensor/distancia", str(dist))
    c.publish("bikesafe/sensor/movimiento", str(mov))
    c.publish("bikesafe/sensor/inclinacion", str(inc))
    c.publish("bikesafe/sensor/lazo", "ENTERO")
    c.publish("bikesafe/sensores", json.dumps(
        {"estado": "ASEGURADA", "dist": dist, "cambio": mov, "incl": inc}))
    time.sleep(0.3)
c.publish("bikesafe/alerta", "AVISO: Movimiento (1 de 4)")

if len(sys.argv) > 1:
    with open(sys.argv[1], "rb") as f:
        jpg = f.read()
    print("-> foto de", len(jpg), "bytes")
    c.publish("bikesafe/cam/info", json.dumps(
        {"nivel": "PRESENCIA", "motivo": "Alguien a 30 cm", "n": 1}))
    c.publish("bikesafe/cam/frame", jpg)

time.sleep(4)
c.loop_stop()
print("Listo. Mensajes recibidos de vuelta:", len(recibidos))
