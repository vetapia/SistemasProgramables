# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/mqtt_bridge.py
# Objetivo:  Servidor central: recibe sensores, eventos y fotos por MQTT,
#            la IA detecta personas y le INFORMA a la ESP32, guarda todo
#            en Firebase y escucha en tiempo real los comandos del dashboard
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Flujo:
#
#   Freenove --bikesafe/cam/frame--> este servidor
#       YOLOv5 (OpenCV dnn): ¿cuantas personas hay y con que confianza?
#       publica el RESULTADO firmado en bikesafe/ia/resultado
#           -> la ESP32 decide si es aviso, robo o nada
#       guarda la foto analizada en Firebase (eventos_ia)
#
#   ESP32 --bikesafe/sensores, /alerta, /evento, /conexion--> Firebase
#
#   Dashboard --(Firestore: comandos)--> on_snapshot en este servidor
#       --bikesafe/cmd firmado--> ESP32
#
# El servidor YA NO le ordena nada a los actuadores por su cuenta: si la
# laptop se apaga, el candado sigue protegiendo la bici igual.
#
# Como correrlo (o doble clic en INICIAR_DEMO.bat):
#   pip install -r requirements.txt
#   python mqtt_bridge.py

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone

import cv2
import paho.mqtt.client as mqtt

import config as cfg
from ia.detector import DetectorPersonas
from nube import Nube

# firma.py es el MISMO archivo que usa la ESP32 (una sola copia)
sys.path.append(os.path.join(cfg.AQUI, "..", "firmware", "esp32"))
import firma  # noqa: E402

T_TODO = "bikesafe/#"
T_FRAME = "bikesafe/cam/frame"
T_INFO = "bikesafe/cam/info"
T_CMD = "bikesafe/cmd"
T_IA = "bikesafe/ia/resultado"
T_CONEXION = "bikesafe/conexion"

# Lo que el dashboard puede pedir -> (topico, mensaje) para la ESP32
COMANDOS = {
    "asegurar": (T_CMD, "asegurar"),
    "liberar": (T_CMD, "liberar"),
    "silenciar": (T_CMD, "silenciar"),
    "foto": (T_CMD, "foto"),
    "buscar": (T_CMD, "buscar"),
    "pitido": ("bikesafe/buzzer/cmd", "pitido"),
    "led_prueba": ("bikesafe/led/cmd", "morado"),
}


def hora():
    return datetime.now().strftime("%H:%M:%S")


class Servidor:
    def __init__(self):
        print("=== BikeSafe servidor ===")
        self.detector = DetectorPersonas(cfg.CONFIANZA_MINIMA, cfg.PROBAR_GIROS)
        print("[ia] Detector de personas listo ({}), reporta desde {:.0f}%"
              .format(self.detector.nombre, cfg.CONFIANZA_MINIMA * 100))
        if cfg.MQTT_CLAVE:
            print("[seguridad] Mensajes a la ESP32 FIRMADOS (HMAC-SHA256)")
        else:
            print("[seguridad] OJO: falta servidor/clave_mqtt.txt. Los mensajes "
                  "van sin firma y la ESP32 rechazara 'liberar'.")
        self.nube = Nube(cfg.FIREBASE_LLAVE, cfg.CARPETA_REGISTROS)
        os.makedirs(cfg.CARPETA_CAPTURAS, exist_ok=True)
        self.lectura = {"estado": None, "distancia": None, "movimiento": None,
                        "inclinacion": None, "cerrojo": None, "lazo": None,
                        "luz": None}
        self.info_foto = {"nivel": "?", "motivo": "", "n": 0}
        self._ultima_lectura = 0.0
        self._contador = 0
        self._candado = threading.Lock()
        self._vistos = set()                     # comandos ya atendidos
        self.cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id="bikesafe13-servidor-{}".format(
                                       os.getpid()))
        self.cliente.on_connect = self.al_conectar
        self.cliente.on_message = self.al_recibir

    # ---------- MQTT ----------
    def al_conectar(self, cliente, userdata, flags, rc, properties=None):
        print("[mqtt] Conectado al broker (codigo {})".format(rc))
        cliente.subscribe(T_TODO)

    def publicar_firmado(self, topico, texto):
        """Firma el mensaje (ver firmware/esp32/firma.py) y lo publica.
        El contador es la hora en ms y nunca se repite."""
        with self._candado:
            self._contador = max(self._contador + 1, int(time.time() * 1000))
            contador = self._contador
        if cfg.MQTT_CLAVE:
            texto = firma.firmar(cfg.MQTT_CLAVE, texto, contador)
        self.cliente.publish(topico, texto)

    def al_recibir(self, cliente, userdata, msg):
        try:
            if msg.topic == T_FRAME:
                self.procesar_frame(msg.payload)
            elif msg.topic == T_INFO:
                self.info_foto = json.loads(msg.payload.decode())
            else:
                self.procesar_texto(msg.topic,
                                    msg.payload.decode(errors="replace"))
        except Exception as e:
            print("[error]", msg.topic, e)

    # ---------- sensores, eventos y estado ----------
    def procesar_texto(self, topico, texto):
        if topico.endswith("/cmd") or topico == T_IA:
            return                                  # son nuestros propios mensajes
        if topico != "bikesafe/sensores" and not topico.startswith("bikesafe/sensor/"):
            print("[{}] {}: {}".format(hora(), topico, texto))
        if topico == "bikesafe/estado":
            self.lectura["estado"] = texto
            self.nube.actualizar_estado({"estado": texto})
        elif topico == T_CONEXION:
            self.nube.actualizar_estado({"conexion": texto})
            self.nube.guardar_evento("conexion", "ESP32 " + texto, "broker",
                                     self.lectura["estado"])
        elif topico.startswith("bikesafe/sensor/"):
            nombre = topico.rsplit("/", 1)[1]
            try:
                self.lectura[nombre] = float(texto)
            except ValueError:
                self.lectura[nombre] = texto        # cerrojo / lazo
        elif topico == "bikesafe/sensores":
            # La ESP32 manda todo junto: es la lectura completa
            datos = json.loads(texto)
            self.lectura.update(estado=datos.get("estado"),
                                distancia=datos.get("dist"),
                                movimiento=datos.get("cambio"),
                                inclinacion=datos.get("incl"),
                                cerrojo=datos.get("cerrojo"),
                                lazo=datos.get("lazo"),
                                luz=datos.get("luz"))
            self._guardar_lectura_si_toca()
        elif topico == "bikesafe/alerta":
            self.nube.guardar_alerta(texto, self.lectura["estado"])
            self.nube.actualizar_estado({"ultima_alerta": texto})
        elif topico == "bikesafe/evento":
            e = json.loads(texto)
            if e.get("tipo") != "alerta":           # esas ya van en alertas
                self.nube.guardar_evento(e.get("tipo"), e.get("detalle"),
                                         e.get("origen", ""), e.get("estado"))

    def _guardar_lectura_si_toca(self):
        ahora = time.time()
        if ahora - self._ultima_lectura < cfg.GUARDAR_LECTURA_CADA_S:
            return
        self._ultima_lectura = ahora
        self.nube.guardar_lectura(dict(self.lectura))
        self.nube.actualizar_estado(dict(self.lectura, conexion="online"))

    # ---------- foto + IA ----------
    def procesar_frame(self, jpg):
        inicio = time.time()
        img, res = self.detector.analizar_jpeg(jpg)
        ms = (time.time() - inicio) * 1000
        nivel = self.info_foto.get("nivel", "?")
        motivo = self.info_foto.get("motivo", "")
        print("[{}] FOTO {} bytes ({}: {}) -> IA: {} {:.0f}% ({} persona(s), "
              "giro {}) en {:.0f} ms".format(hora(), len(jpg), nivel, motivo,
                                              res.clase, res.confianza * 100,
                                              res.personas, res.giro, ms))
        # La IA solo INFORMA. La ESP32 decide con su propia regla.
        self.publicar_firmado(T_IA, json.dumps({
            "clase": res.clase, "conf": round(res.confianza, 3),
            "personas": res.personas, "nivel": nivel,
            "n": self.info_foto.get("n", 0)}))

        marcada = self.detector.dibujar(img, res)
        nombre = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + res.clase + ".jpg"
        cv2.imwrite(os.path.join(cfg.CARPETA_CAPTURAS, nombre), marcada)
        ok, chico = cv2.imencode(".jpg", cv2.resize(marcada, (240, 180)),
                                 [cv2.IMWRITE_JPEG_QUALITY, 70])
        self.nube.guardar_evento_ia(res, nivel, motivo,
                                    chico.tobytes() if ok else None)
        self.nube.actualizar_estado({"ultima_ia": res.clase,
                                     "ultima_confianza": round(res.confianza, 3)})

    # ---------- comandos del dashboard (Firestore en tiempo real) ----------
    def al_llegar_comando(self, doc_id, datos):
        if doc_id in self._vistos or datos.get("estado") != "pendiente":
            return
        self._vistos.add(doc_id)
        cmd = datos.get("cmd", "")
        quien = datos.get("nombre") or datos.get("uid", "?")
        creado = datos.get("creado")
        if cmd not in COMANDOS:
            self.nube.marcar_comando(doc_id, "rechazado", "comando desconocido")
            return
        if creado is not None:
            edad = (datetime.now(timezone.utc) - creado).total_seconds()
            if edad > cfg.COMANDO_CADUCA_S:
                print("[{}] Comando '{}' de {} caducado ({:.0f} s)".format(
                    hora(), cmd, quien, edad))
                self.nube.marcar_comando(doc_id, "caducado",
                                         "llego {:.0f} s tarde".format(edad))
                return
        topico, texto = COMANDOS[cmd]
        self.publicar_firmado(topico, texto)
        print("[{}] Dashboard ({}) pide '{}' -> {}".format(hora(), quien, cmd,
                                                         topico))
        self.nube.marcar_comando(doc_id, "enviado", "a la ESP32 por MQTT")
        self.nube.guardar_evento("comando", cmd, "dashboard: " + quien,
                                 self.lectura["estado"])

    # ---------- arranque ----------
    def correr(self):
        print("[mqtt] Conectando a {}:{} ...".format(cfg.BROKER, cfg.PUERTO))
        try:
            self.cliente.connect(cfg.BROKER, cfg.PUERTO, keepalive=60)
        except OSError as e:
            print("[mqtt] No hay broker en {}:{} ({}). ¿Hay internet / abriste "
                  "mosquitto?".format(cfg.BROKER, cfg.PUERTO, e))
            sys.exit(1)
        self.nube.actualizar_estado({"servidor": "online",
                                     "ia_modelo": self.detector.nombre})
        self.nube.escuchar_comandos(self.al_llegar_comando)
        try:
            self.cliente.loop_forever()
        finally:
            self.nube.detener()
            self.nube.actualizar_estado({"servidor": "offline"})


if __name__ == "__main__":
    try:
        Servidor().correr()
    except KeyboardInterrupt:
        print("\nServidor detenido")
