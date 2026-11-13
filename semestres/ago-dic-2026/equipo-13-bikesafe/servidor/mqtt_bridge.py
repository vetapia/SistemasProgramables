# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/mqtt_bridge.py
# Objetivo:  Servidor central: recibe sensores y fotos por MQTT, la IA
#            (OpenCV) decide si hay una persona, activa el actuador y
#            guarda todo en Firebase
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Flujo (el mismo del curso):
#
#   ESP32-CAM (Freenove) --bikesafe/cam/frame--> este servidor
#       OpenCV + YuNet: ¿hay una persona en la foto?
#           si -> publica "alerta_ia" en bikesafe/cmd  -> ESP32 pita
#                 y prende el LED rojo
#       guarda la decision en Firebase (eventos_ia)
#   ESP32 normal --bikesafe/sensor/*--> este servidor --> Firebase
#
# Como correrlo:
#   1) mosquitto -v                (en otra terminal)
#   2) pip install -r requirements.txt
#   3) python mqtt_bridge.py

import json
import os
import sys
import time
from datetime import datetime

import cv2
import paho.mqtt.client as mqtt

import config as cfg
from ia.detector import DetectorPersonas
from nube import Nube

T_TODO = "bikesafe/#"
T_FRAME = "bikesafe/cam/frame"
T_INFO = "bikesafe/cam/info"
T_CMD = "bikesafe/cmd"
T_IA = "bikesafe/ia/resultado"


def hora():
    return datetime.now().strftime("%H:%M:%S")


class Servidor:
    def __init__(self):
        print("=== BikeSafe servidor ===")
        self.detector = DetectorPersonas(cfg.CONFIANZA_MINIMA, cfg.PROBAR_GIROS)
        print("[ia] Detector listo (YuNet + HOG), confianza minima",
              cfg.CONFIANZA_MINIMA)
        self.nube = Nube(cfg.FIREBASE_LLAVE, cfg.CARPETA_REGISTROS)
        os.makedirs(cfg.CARPETA_CAPTURAS, exist_ok=True)
        self.lectura = {"estado": None, "distancia": None, "movimiento": None,
                        "inclinacion": None, "lazo": None}
        self.info_foto = {"nivel": "?", "motivo": ""}
        self._ultima_lectura = 0.0
        self.cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id="bikesafe-servidor")
        self.cliente.on_connect = self.al_conectar
        self.cliente.on_message = self.al_recibir

    # ---------- MQTT ----------
    def al_conectar(self, cliente, userdata, flags, rc, properties=None):
        print("[mqtt] Conectado al broker (codigo {})".format(rc))
        cliente.subscribe(T_TODO)

    def al_recibir(self, cliente, userdata, msg):
        try:
            if msg.topic == T_FRAME:
                self.procesar_frame(msg.payload)
            elif msg.topic == T_INFO:
                self.info_foto = json.loads(msg.payload.decode())
            else:
                self.procesar_texto(msg.topic, msg.payload.decode(errors="replace"))
        except Exception as e:
            print("[error]", msg.topic, e)

    # ---------- sensores y estado ----------
    def procesar_texto(self, topico, texto):
        if topico.endswith("/cmd") or topico == T_IA:
            return                                  # son nuestros propios mensajes
        print("[{}] {}: {}".format(hora(), topico, texto))
        if topico == "bikesafe/estado":
            self.lectura["estado"] = texto
            self.nube.actualizar_estado({"estado": texto})
        elif topico.startswith("bikesafe/sensor/"):
            nombre = topico.rsplit("/", 1)[1]
            try:
                self.lectura[nombre] = float(texto)
            except ValueError:
                self.lectura[nombre] = texto        # lazo: ENTERO / CORTADO
        elif topico == "bikesafe/sensores":
            # El ESP32 manda los 3 sensores juntos: es la lectura completa
            datos = json.loads(texto)
            self.lectura.update(estado=datos.get("estado"),
                                distancia=datos.get("dist"),
                                movimiento=datos.get("cambio"),
                                inclinacion=datos.get("incl"))
            self._guardar_lectura_si_toca()
        elif topico == "bikesafe/alerta":
            self.nube.guardar_alerta(texto, self.lectura["estado"])
            self.nube.actualizar_estado({"ultima_alerta": texto})

    def _guardar_lectura_si_toca(self):
        ahora = time.time()
        if ahora - self._ultima_lectura < cfg.GUARDAR_LECTURA_CADA_S:
            return
        self._ultima_lectura = ahora
        self.nube.guardar_lectura(dict(self.lectura))
        self.nube.actualizar_estado(dict(self.lectura))

    # ---------- foto + IA ----------
    def procesar_frame(self, jpg):
        inicio = time.time()
        img, res = self.detector.analizar_jpeg(jpg)
        ms = (time.time() - inicio) * 1000
        nivel = self.info_foto.get("nivel", "?")
        motivo = self.info_foto.get("motivo", "")
        print("[{}] FOTO {} bytes ({}: {}) -> IA: {} {:.0f}% [{} giro {}] en {:.0f} ms"
              .format(hora(), len(jpg), nivel, motivo, res.clase,
                      res.confianza * 100, res.modelo, res.giro, ms))

        accion = "ninguna"
        if res.hay_persona and cfg.ACTIVAR_ACTUADOR_SI_PERSONA:
            accion = "alerta_ia"
            self.cliente.publish(T_CMD, accion)
            print("[{}]   -> publico '{}' en {}: el ESP32 pita y prende el LED rojo"
                  .format(hora(), accion, T_CMD))
        self.cliente.publish(T_IA, json.dumps(dict(res.como_dict(), accion=accion,
                                                   nivel=nivel, motivo=motivo)))

        marcada = self.detector.dibujar(img, res)
        nombre = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + res.clase + ".jpg"
        cv2.imwrite(os.path.join(cfg.CARPETA_CAPTURAS, nombre), marcada)
        ok, chico = cv2.imencode(".jpg", cv2.resize(marcada, (240, 180)),
                                 [cv2.IMWRITE_JPEG_QUALITY, 70])
        self.nube.guardar_evento_ia(res, accion, nivel, motivo,
                                    chico.tobytes() if ok else None)
        self.nube.actualizar_estado({"ultima_ia": res.clase,
                                     "ultima_confianza": round(res.confianza, 3)})

    # ---------- arranque ----------
    def correr(self):
        print("[mqtt] Conectando a {}:{} ...".format(cfg.BROKER, cfg.PUERTO))
        try:
            self.cliente.connect(cfg.BROKER, cfg.PUERTO, keepalive=60)
        except OSError as e:
            print("[mqtt] No hay broker en {}:{} ({}). ¿Ya abriste mosquitto?"
                  .format(cfg.BROKER, cfg.PUERTO, e))
            sys.exit(1)
        self.cliente.loop_forever()


if __name__ == "__main__":
    try:
        Servidor().correr()
    except KeyboardInterrupt:
        print("\nServidor detenido")
