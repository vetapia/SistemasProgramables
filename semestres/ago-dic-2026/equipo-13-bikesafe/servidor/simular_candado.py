# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/simular_candado.py
# Objetivo:  Probar el servidor sin las placas: publica sensores, eventos
#            y una foto por MQTT como si fueran la ESP32 y la Freenove, y
#            revisa que la IA conteste con un mensaje FIRMADO
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Uso:  python simular_candado.py  ruta/a/una_foto.jpg
# (con mqtt_bridge.py ya corriendo en otra ventana)

import json
import os
import sys
import time

import paho.mqtt.client as mqtt

import config as cfg

sys.path.append(os.path.join(cfg.AQUI, "..", "firmware", "esp32"))
import firma  # noqa: E402

recibidos = []


def al_recibir(cliente, userdata, msg):
    texto = msg.payload.decode(errors="replace")
    recibidos.append((msg.topic, texto))
    print("  <- {}: {}".format(msg.topic, texto[:140]))
    if cfg.MQTT_CLAVE:
        valido, extra = firma.verificar(cfg.MQTT_CLAVE, texto, 0)
        print("     firma:", "VALIDA" if valido is not None else "INVALIDA (" + extra + ")")


c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                client_id="bikesafe13-simulador-{}".format(os.getpid()))
c.on_message = al_recibir
c.connect(cfg.BROKER, cfg.PUERTO)
c.subscribe("bikesafe/cmd")
c.subscribe("bikesafe/ia/resultado")
c.loop_start()
time.sleep(0.5)

print("-> conexion online, estado ASEGURADA y 3 lecturas de sensores")
c.publish("bikesafe/conexion", "online", retain=True)
c.publish("bikesafe/estado", "ASEGURADA", retain=True)
c.publish("bikesafe/evento", json.dumps({"tipo": "estado", "detalle": "LIBRE -> ASEGURADA",
                                         "origen": "simulador", "estado": "ASEGURADA"}))
for dist, mov, inc in ((120.0, 0.02, 1.1), (45.0, 0.05, 1.3), (30.0, 0.31, 2.0)):
    c.publish("bikesafe/sensores", json.dumps(
        {"estado": "ASEGURADA", "dist": dist, "cambio": mov, "incl": inc,
         "cerrojo": "CERRADO", "lazo": "ENTERO", "luz": "azul"}))
    time.sleep(0.3)
c.publish("bikesafe/alerta", "AVISO: Movimiento (1 de 4)")

if len(sys.argv) > 1:
    with open(sys.argv[1], "rb") as f:
        jpg = f.read()
    print("-> foto de", len(jpg), "bytes")
    c.publish("bikesafe/cam/info", json.dumps(
        {"nivel": "PRESENCIA", "motivo": "Alguien a 30 cm", "n": 1}))
    c.publish("bikesafe/cam/frame", jpg)

time.sleep(5)
c.loop_stop()
print("Listo. Mensajes recibidos de vuelta:", len(recibidos))
