# ============================================
# Proyecto:  SmartClass
# Archivo:   mqtt_bridge.py
# Objetivo:  Servidor principal: recibe frames y sensores por MQTT, reconoce rostros, registra asistencia y sirve el dashboard web
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
"""SmartClass - Servidor principal (reconocimiento, asistencia y pagina web).

Corre en la laptop. Recibe por MQTT los frames de la camara y los datos de los
sensores; reconoce rostros, guarda la asistencia en Excel y ofrece una pagina web
(para el telefono) con sensores en tiempo real, registro de alumnos y descarga.

Topicos MQTT
  Entrada : smartclass/cam/frame            JPEG de la camara de la puerta
            smartclass/s/clima              {"temp": 25, "hum": 50}
            smartclass/s/distancia          cm (texto)
            smartclass/s/ir                 "1" si el sensor de la puerta detecta
            smartclass/s/ir_disp            "1" si el sensor del dispensador detecta
            smartclass/nodo/<nombre>        latido: puerta, dispensador
            smartclass/e/bomba, e/vent      "ON" / "OFF": estado de los actuadores del dispensador
  Salida  : smartclass/puerta/resultado     {"estado": reconocido|desconocido|sin_rostro, ...}
            smartclass/puerta/cmd           {"accion": registro_inicio|registro_listo|
                                                        registro_ok|registro_cancelado}
            smartclass/config/wifi          {"ssid": "...", "password": "..."}
"""
import hmac
import json
import os
import re
import socket
import threading
import time
from collections import deque
import unicodedata
from datetime import datetime, timedelta

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template, request, send_file

import firebase_opcional
from asistencia import Asistencia
from ia.reconocimiento import MotorFacial, RegistroAlumnos

DIR = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(DIR, "datos")

T_FRAME = "smartclass/cam/frame"
T_SENSORES = "smartclass/s/#"
T_NODOS = "smartclass/nodo/#"
T_ESTADOS = "smartclass/e/#"
T_RESULTADO = "smartclass/puerta/resultado"
T_CMD_PUERTA = "smartclass/puerta/cmd"
T_CFG_WIFI = "smartclass/config/wifi"

SEGUNDOS_ENTRE_MUESTRAS = 0.4
ESTADOS_REGISTRO_ACTIVOS = ("esperando", "capturando")


def sin_acentos(texto):
    """La pantalla OLED solo muestra ASCII: quita acentos y la enie."""
    base = unicodedata.normalize("NFKD", texto)
    return base.encode("ascii", "ignore").decode("ascii")


def limpiar_nombre(texto):
    texto = re.sub(r"\s+", " ", (texto or "")).strip()
    texto = "".join(c for c in texto if c.isprintable())
    return texto[:40]


class Servidor:
    def __init__(self, motor, alumnos, asistencia, publicar,
                 muestras_registro=10, timeout_registro=90, reloj=datetime.now,
                 nube=None, intervalo_lecturas_s=60, intervalo_estado_s=15,
                 alerta_temp=30, alerta_temp_critica=35, ventana_desconocidos_min=30):
        self.motor = motor
        self.alumnos = alumnos
        self.asistencia = asistencia
        self.publicar = publicar            # publicar(topico, dict_o_texto)
        self.muestras_registro = muestras_registro
        self.timeout_registro = timeout_registro
        self.reloj = reloj
        self.lock = threading.RLock()
        self.sensores = {}                  # clave -> (valor, instante)
        self.nodos = {}                     # nombre -> instante
        self.registro = {"estado": "inactivo", "muestras": [], "inicio": 0.0, "ultima": 0.0}
        self.ultimo_jpg = None
        self.actuadores = {}                # "bomba"/"vent" -> "ON"/"OFF"
        self.nube = nube if nube is not None else firebase_opcional
        self.intervalo_lecturas_s = intervalo_lecturas_s
        self.intervalo_estado_s = intervalo_estado_s
        self._t_lectura = 0.0
        self._t_estado = 0.0
        self._t_desconocido = 0.0
        self.historial = deque(maxlen=1500)   # lecturas (las carga Firebase y luego crecen en vivo)
        self.eventos = deque(maxlen=300)      # decisiones de la IA
        self._t_recarga = 0.0
        self.alerta_temp = alerta_temp
        self.alerta_temp_critica = alerta_temp_critica
        self.ventana_desconocidos_min = ventana_desconocidos_min

    # ------------------------------------------------------------ MQTT
    def al_recibir_mensaje(self, topico, payload):
        if topico == T_FRAME:
            self.procesar_frame(payload)
        elif topico.startswith("smartclass/s/"):
            self._guardar_sensor(topico.rsplit("/", 1)[1], payload)
        elif topico.startswith("smartclass/nodo/"):
            with self.lock:
                self.nodos[topico.rsplit("/", 1)[1]] = time.time()
        elif topico.startswith("smartclass/e/"):
            valor = payload.decode("utf-8", "ignore").strip().upper()
            if valor in ("ON", "OFF"):
                nombre = topico.rsplit("/", 1)[1]
                with self.lock:
                    cambio = self.actuadores.get(nombre) != valor
                    self.actuadores[nombre] = valor
                if cambio:
                    self._enviar_a_nube(forzar_estado=True)

    def _guardar_sensor(self, nombre, payload):
        try:
            texto = payload.decode("utf-8", "ignore").strip()
            with self.lock:
                if nombre == "clima":
                    datos = json.loads(texto)
                    ahora = time.time()
                    if datos.get("temp") is not None:
                        self.sensores["temp"] = (float(datos["temp"]), ahora)
                    if datos.get("hum") is not None:
                        self.sensores["hum"] = (float(datos["hum"]), ahora)
                elif nombre in ("distancia", "ir", "ir_disp"):
                    self.sensores[nombre] = (float(texto), time.time())
        except (ValueError, TypeError):
            return
        self._enviar_a_nube()

    def _valores_actuales(self, max_edad_s=60):
        nombres = {"temp": "temperatura", "hum": "humedad", "distancia": "distancia_cm",
                   "ir": "ir_puerta", "ir_disp": "ir_dispensador"}
        ahora = time.time()
        valores = {}
        with self.lock:
            for clave, nombre in nombres.items():
                if clave in self.sensores and ahora - self.sensores[clave][1] <= max_edad_s:
                    v = self.sensores[clave][0]
                    valores[nombre] = int(v) if clave in ("ir", "ir_disp") else v
        return valores

    def _enviar_a_nube(self, forzar_estado=False):
        """Guarda lecturas e estado en Firebase sin saturarlo (cada X segundos)."""
        ahora = time.time()
        if ahora - self._t_lectura >= self.intervalo_lecturas_s:
            valores = self._valores_actuales()
            if valores:
                self._t_lectura = ahora
                self.nube.lectura(valores)
                with self.lock:
                    self.historial.append(
                        dict(t=self.reloj().isoformat(timespec="seconds"), **valores))
        if forzar_estado or ahora - self._t_estado >= self.intervalo_estado_s:
            doc = self._valores_actuales()
            with self.lock:
                if "bomba" in self.actuadores:
                    doc["bomba"] = self.actuadores["bomba"]
                if "vent" in self.actuadores:
                    doc["ventilador"] = self.actuadores["vent"]
                doc["nodo_puerta_en_linea"] = (ahora - self.nodos.get("puerta", 0)) < 30
                doc["nodo_dispensador_en_linea"] = (ahora - self.nodos.get("dispensador", 0)) < 30
            if len(doc) > 2:
                self._t_estado = ahora
                self.nube.estado_actual(doc)

    # ------------------------------------------------------------ frames
    def procesar_frame(self, datos):
        img = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print("Frame invalido, se ignora")
            return
        if self._registro_activo():
            self._frame_registro(img)
        else:
            self._frame_asistencia(img)

    def _guardar_anotado(self, img, fila, texto, color):
        if fila is not None:
            x, y, w, h = (int(v) for v in fila[:4])
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img, sin_acentos(texto), (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        ok, buf = cv2.imencode(".jpg", img)
        if ok:
            self.ultimo_jpg = buf.tobytes()

    def _evento_ia(self, deteccion, accion, confianza, extra, ahora):
        """Guarda la decision de la IA en Firebase y en la lista del dashboard."""
        with self.lock:
            self.eventos.append({"t": ahora.isoformat(timespec="seconds"), "deteccion": deteccion,
                                 "accion": accion, "confianza": round(float(confianza), 3)})
        self.nube.evento_ia(deteccion, accion, confianza, extra, ahora)

    def _frame_asistencia(self, img):
        ahora = self.reloj()
        fila, _ = self.motor.detectar(img)
        if fila is None:
            self.publicar(T_RESULTADO, {"estado": "sin_rostro"})
            self._guardar_anotado(img, None, "sin rostro", (0, 165, 255))
            print(f"[{ahora:%H:%M:%S}] Frame recibido -> IA: sin rostro -> puerta: reintenta con otra foto")
            return

        vec = self.motor.embedding(img, fila)
        alumno_id, nombre, score = self.alumnos.identificar(vec)
        if alumno_id is None:
            self.publicar(T_RESULTADO, {"estado": "desconocido", "score": round(score, 2)})
            self._guardar_anotado(img, fila, f"desconocido ({score:.2f})", (0, 0, 255))
            print(f"[{ahora:%H:%M:%S}] Frame recibido -> IA: desconocido (similitud {score:.2f}) "
                  "-> actuador: anillo rojo + buzzer largo (si se repite en las 4 fotos)")
            if time.time() - self._t_desconocido >= 5:       # no llenar Firebase con cada foto
                self._t_desconocido = time.time()
                self._evento_ia("desconocido", "anillo_rojo+buzzer_largo", score,
                                {"fecha": ahora.strftime("%Y-%m-%d"),
                                 "hora": ahora.strftime("%H:%M:%S")}, ahora)
            return

        nueva, hora = self.asistencia.registrar(alumno_id, nombre, ahora)
        self.publicar(T_RESULTADO, {
            "estado": "reconocido",
            "nombre": nombre,
            "nombre_oled": sin_acentos(nombre),
            "hora": ahora.strftime("%H:%M"),
            "nueva": nueva,
            "score": round(score, 2),
        })
        self._guardar_anotado(img, fila, f"{nombre} ({score:.2f})", (0, 200, 0))
        print(f"[{ahora:%H:%M:%S}] Frame recibido -> IA: {nombre} (similitud {score:.2f}) "
              "-> actuador: anillo verde + buzzer corto + pantalla BIENVENIDO"
              f"{' | asistencia registrada' if nueva else ' | ya estaba registrado hoy'}")
        self._evento_ia(alumno_id, "anillo_verde+buzzer_corto+pantalla_bienvenida", score,
                        {"alumno_id": alumno_id, "asistencia_nueva": bool(nueva),
                         "fecha": ahora.strftime("%Y-%m-%d"), "hora": hora}, ahora)
        if nueva:
            self.nube.asistencia(alumno_id, ahora.strftime("%Y-%m-%d"), hora, ahora)

    # ------------------------------------------------------------ registro de alumnos
    def _registro_activo(self):
        with self.lock:
            self._revisar_timeout()
            return self.registro["estado"] in ESTADOS_REGISTRO_ACTIVOS

    def _revisar_timeout(self):
        r = self.registro
        if (r["estado"] in ESTADOS_REGISTRO_ACTIVOS
                and time.time() - r["inicio"] > self.timeout_registro):
            r["estado"] = "tiempo_agotado"
            self.publicar(T_CMD_PUERTA, {"accion": "registro_cancelado"})

    def _frame_registro(self, img):
        fila, _ = self.motor.detectar(img)
        if fila is None:
            self._guardar_anotado(img, None, "registro: no veo rostro", (0, 165, 255))
            return
        with self.lock:
            r = self.registro
            if r["estado"] not in ESTADOS_REGISTRO_ACTIVOS:
                return
            if time.time() - r["ultima"] < SEGUNDOS_ENTRE_MUESTRAS:
                return
            r["muestras"].append(self.motor.embedding(img, fila))
            r["ultima"] = time.time()
            r["estado"] = "capturando"
            n = len(r["muestras"])
            self._guardar_anotado(img, fila, f"registro {n}/{self.muestras_registro}", (255, 120, 0))
            print(f"Registro: muestra {n}/{self.muestras_registro}")
            if n >= self.muestras_registro:
                r["estado"] = "listo"
                self.publicar(T_CMD_PUERTA, {"accion": "registro_listo"})

    def iniciar_registro(self):
        with self.lock:
            self._revisar_timeout()
            if self.registro["estado"] in ESTADOS_REGISTRO_ACTIVOS + ("listo",):
                return False
            self.registro = {"estado": "esperando", "muestras": [],
                             "inicio": time.time(), "ultima": 0.0}
        self.publicar(T_CMD_PUERTA, {"accion": "registro_inicio"})
        return True

    def cancelar_registro(self):
        with self.lock:
            activo = self.registro["estado"] != "inactivo"
            self.registro = {"estado": "inactivo", "muestras": [], "inicio": 0.0, "ultima": 0.0}
        if activo:
            self.publicar(T_CMD_PUERTA, {"accion": "registro_cancelado"})

    def confirmar_registro(self, nombre):
        nombre = limpiar_nombre(nombre)
        if not nombre:
            return None, "Escribe el nombre del alumno"
        with self.lock:
            if self.registro["estado"] != "listo":
                return None, "El registro todavia no esta listo"
            muestras = list(self.registro["muestras"])
            self.registro = {"estado": "inactivo", "muestras": [], "inicio": 0.0, "ultima": 0.0}
        alumno_id = self.alumnos.agregar(nombre, muestras)
        self.publicar(T_CMD_PUERTA, {"accion": "registro_ok", "nombre_oled": sin_acentos(nombre)})
        return alumno_id, None

    def estado_registro(self):
        with self.lock:
            self._revisar_timeout()
            r = self.registro
            return {"estado": r["estado"], "muestras": len(r["muestras"]),
                    "objetivo": self.muestras_registro}

    # ------------------------------------------------------------ estado para la pagina
    def estado_general(self):
        ahora = time.time()
        with self.lock:
            sensores = {k: {"valor": v, "hace_s": round(ahora - t)}
                        for k, (v, t) in self.sensores.items()}
            nodos = {n: (ahora - t) < 30 for n, t in self.nodos.items()}
        for n in ("puerta", "dispensador"):
            nodos.setdefault(n, False)
        alumnos = self.alumnos.listar()
        hoy = self.asistencia.hoy()
        with self.lock:
            actuadores = dict(self.actuadores)
        return {"sensores": sensores, "nodos": nodos, "registro": self.estado_registro(),
                "alumnos": alumnos, "hoy": hoy, "actuadores": actuadores}

    # ------------------------------------------------------------ dashboard
    def cargar_historial(self):
        """Lee de Firebase las lecturas y eventos guardados (al arrancar o al pedirlo)."""
        try:
            lecturas = self.nube.leer_historial(horas=24, limite=1500)
            eventos = self.nube.leer_eventos(limite=300)
        except Exception as e:
            print("Firebase: no se pudo leer el historial:", e)
            return False
        with self.lock:
            self.historial.clear()
            self.historial.extend(lecturas)
            self.eventos.clear()
            self.eventos.extend(eventos)
        return True

    def recargar_historial(self):
        if not self.nube.activo():
            return None, "Firebase no está activo", 503
        if time.time() - self._t_recarga < 30:
            return None, "Espera unos segundos antes de recargar otra vez", 429
        self._t_recarga = time.time()
        if not self.cargar_historial():
            return None, "No se pudo leer Firebase (mira la consola del servidor)", 502
        return {"lecturas": len(self.historial), "eventos": len(self.eventos)}, None, 200

    @staticmethod
    def _reducir(lista, maximo):
        if len(lista) <= maximo:
            return lista
        paso = -(-len(lista) // maximo)
        reducida = lista[::paso]
        if reducida[-1] is not lista[-1]:
            reducida.append(lista[-1])
        return reducida

    def _alertas(self):
        ahora = time.time()
        with self.lock:
            sensores = dict(self.sensores)
            nodos = dict(self.nodos)
            actuadores = dict(self.actuadores)
            eventos = list(self.eventos)
        lista = []
        for nombre in ("puerta", "dispensador"):
            if ahora - nodos.get(nombre, 0) > 30:
                lista.append({"nivel": "peligro", "texto": f"El nodo {nombre} está sin conexión"})
        temp = sensores.get("temp")
        if temp and ahora - temp[1] <= 60:
            valor = temp[0]
            if valor >= self.alerta_temp_critica:
                lista.append({"nivel": "peligro", "texto": f"Temperatura crítica: {valor:.0f} °C"})
            elif valor > self.alerta_temp:
                lista.append({"nivel": "aviso", "texto": f"Temperatura alta: {valor:.0f} °C"})
        elif ahora - nodos.get("dispensador", 0) <= 30:
            lista.append({"nivel": "aviso", "texto": "Sin lecturas de temperatura recientes (revisa el DHT11)"})
        corte = (self.reloj() - timedelta(minutes=self.ventana_desconocidos_min)).isoformat(timespec="seconds")
        desconocidos = [e for e in eventos if e.get("deteccion") == "desconocido" and e.get("t", "") >= corte]
        if desconocidos:
            lista.append({"nivel": "aviso", "texto":
                          f"{len(desconocidos)} intento(s) de personas no registradas en los últimos "
                          f"{self.ventana_desconocidos_min} min"})
        if actuadores.get("vent") == "ON":
            lista.append({"nivel": "info", "texto": "El ventilador está encendido"})
        if not self.nube.activo():
            lista.append({"nivel": "aviso", "texto": "Firebase desactivado: no se guarda el histórico"})
        return lista or [{"nivel": "ok", "texto": "Todo en orden"}]

    def dashboard(self):
        ahora = self.reloj()
        hoy = ahora.strftime("%Y-%m-%d")
        with self.lock:
            historial = list(self.historial)
            eventos = list(self.eventos)
            actuadores = dict(self.actuadores)
        temps = [h["temperatura"] for h in historial if h.get("temperatura") is not None]
        eventos_hoy = [e for e in eventos if str(e.get("t", "")).startswith(hoy)]
        nombres = {a["id"]: a["nombre"] for a in self.alumnos.listar()}
        resumen = {
            "temp_min": min(temps) if temps else None,
            "temp_max": max(temps) if temps else None,
            "temp_prom": round(sum(temps) / len(temps), 1) if temps else None,
            "presentes_hoy": len(self.asistencia.hoy()),
            "alumnos": len(self.alumnos.listar()),
            "reconocimientos_hoy": len([e for e in eventos_hoy if e.get("deteccion") != "desconocido"]),
            "no_registrados_hoy": len([e for e in eventos_hoy if e.get("deteccion") == "desconocido"]),
        }
        return {
            "ahora": ahora.isoformat(timespec="seconds"),
            "firebase": bool(self.nube.activo()),
            "historial": self._reducir(historial, 300),
            "eventos": [dict(e, deteccion=nombres.get(e.get("deteccion"), e.get("deteccion")))
                        for e in list(reversed(eventos))[:15]],
            "resumen": resumen,
            "alertas": self._alertas(),
            "actuadores": actuadores,
        }

    def enviar_wifi(self, ssid, password):
        ssid = (ssid or "").strip()
        password = password or ""
        if not ssid or len(ssid) > 32:
            return "El nombre de la red debe tener entre 1 y 32 caracteres"
        if len(password) > 63:
            return "La contrasena puede tener hasta 63 caracteres"
        self.publicar(T_CFG_WIFI, {"ssid": ssid, "password": password})
        return None


# ---------------------------------------------------------------- pagina web
def crear_app(srv, usuario, password):
    app = Flask(__name__)
    usuario_b = usuario.encode("utf-8")
    password_b = password.encode("utf-8")

    @app.before_request
    def proteger():
        auth = request.authorization
        ok = (auth is not None
              and hmac.compare_digest((auth.username or "").encode("utf-8"), usuario_b)
              and hmac.compare_digest((auth.password or "").encode("utf-8"), password_b))
        if not ok:
            return Response("Acceso restringido", 401,
                            {"WWW-Authenticate": 'Basic realm="SmartClass"'})

    @app.get("/")
    def inicio():
        return render_template("index.html")

    @app.get("/api/estado")
    def api_estado():
        return jsonify(srv.estado_general())

    @app.get("/api/dashboard")
    def api_dashboard():
        return jsonify(srv.dashboard())

    @app.post("/api/dashboard/recargar")
    def api_recargar():
        resultado, error, codigo = srv.recargar_historial()
        if error:
            return jsonify(error=error), codigo
        return jsonify(ok=True, **resultado)

    @app.put("/api/alumnos/<alumno_id>")
    def api_renombrar(alumno_id):
        nombre = limpiar_nombre((request.get_json(silent=True) or {}).get("nombre"))
        if not nombre:
            return jsonify(error="Escribe un nombre"), 400
        if not srv.alumnos.renombrar(alumno_id, nombre):
            return jsonify(error="Alumno no encontrado"), 404
        return jsonify(ok=True)

    @app.delete("/api/alumnos/<alumno_id>")
    def api_eliminar(alumno_id):
        if not srv.alumnos.eliminar(alumno_id):
            return jsonify(error="Alumno no encontrado"), 404
        return jsonify(ok=True)

    @app.post("/api/registro/iniciar")
    def api_reg_iniciar():
        if not srv.iniciar_registro():
            return jsonify(error="Ya hay un registro en curso"), 409
        return jsonify(ok=True)

    @app.post("/api/registro/cancelar")
    def api_reg_cancelar():
        srv.cancelar_registro()
        return jsonify(ok=True)

    @app.post("/api/registro/confirmar")
    def api_reg_confirmar():
        alumno_id, error = srv.confirmar_registro((request.get_json(silent=True) or {}).get("nombre"))
        if error:
            return jsonify(error=error), 400
        return jsonify(ok=True, id=alumno_id)

    @app.delete("/api/asistencia/hoy")
    def api_borrar_hoy():
        borrados = srv.asistencia.borrar_dia()
        return jsonify(ok=True, borrados=borrados)

    @app.get("/api/asistencia/exportar")
    def api_exportar():
        fecha = datetime.now().strftime("%Y-%m-%d")
        archivo = srv.asistencia.exportar_lista(srv.alumnos.listar(), fecha)
        return send_file(
            archivo, as_attachment=True, download_name=f"lista_asistencia_{fecha}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.post("/api/wifi")
    def api_wifi():
        datos = request.get_json(silent=True) or {}
        error = srv.enviar_wifi(datos.get("ssid"), datos.get("password"))
        if error:
            return jsonify(error=error), 400
        return jsonify(ok=True)

    @app.get("/api/ultimo_frame.jpg")
    def api_frame():
        if srv.ultimo_jpg is None:
            return Response(status=404)
        return Response(srv.ultimo_jpg, mimetype="image/jpeg",
                        headers={"Cache-Control": "no-store"})

    return app


# ---------------------------------------------------------------- arranque
def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def cargar_config():
    try:
        import config_servidor as cfg
    except ImportError:
        raise SystemExit("Falta config_servidor.py: copia config_servidor_ejemplo.py con ese "
                         "nombre y cambia la contrasena.")
    if cfg.WEB_PASSWORD == "CAMBIA_ESTA_CONTRASENA":
        raise SystemExit("Cambia WEB_PASSWORD en config_servidor.py antes de arrancar.")
    return cfg


def main():
    import paho.mqtt.client as mqtt

    cfg = cargar_config()
    os.makedirs(DATOS, exist_ok=True)
    firebase_opcional.iniciar()

    motor = MotorFacial()
    alumnos = RegistroAlumnos(os.path.join(DATOS, "alumnos.json"),
                              umbral=getattr(cfg, "UMBRAL_SIMILITUD", 0.40))
    asistencia = Asistencia(os.path.join(DATOS, "asistencia.xlsx"))

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="SmartClass_Servidor")

    def publicar(topico, contenido):
        if isinstance(contenido, dict):
            contenido = json.dumps(contenido)
        cliente.publish(topico, contenido)

    srv = Servidor(motor, alumnos, asistencia, publicar,
                   muestras_registro=getattr(cfg, "MUESTRAS_REGISTRO", 10),
                   intervalo_lecturas_s=getattr(cfg, "INTERVALO_LECTURAS_S", 60),
                   intervalo_estado_s=getattr(cfg, "INTERVALO_ESTADO_S", 15),
                   alerta_temp=getattr(cfg, "ALERTA_TEMP_C", 30),
                   alerta_temp_critica=getattr(cfg, "ALERTA_TEMP_CRITICA_C", 35),
                   ventana_desconocidos_min=getattr(cfg, "VENTANA_NO_REGISTRADOS_MIN", 30))
    if firebase_opcional.activo():
        if srv.cargar_historial():
            print(f"Firebase: historial cargado ({len(srv.historial)} lecturas, "
                  f"{len(srv.eventos)} eventos)")

    def on_connect(c, userdata, flags, reason_code, properties):
        print("MQTT conectado:", reason_code)
        c.subscribe([(T_FRAME, 0), (T_SENSORES, 0), (T_NODOS, 0), (T_ESTADOS, 0)])

    def on_message(c, userdata, msg):
        try:
            srv.al_recibir_mensaje(msg.topic, msg.payload)
        except Exception as e:
            print("Error procesando", msg.topic, "->", repr(e))

    cliente.on_connect = on_connect
    cliente.on_message = on_message
    cliente.connect(getattr(cfg, "BROKER", "localhost"), getattr(cfg, "PUERTO_MQTT", 1883), 60)
    cliente.loop_start()

    puerto = getattr(cfg, "PUERTO_WEB", 5000)
    app = crear_app(srv, cfg.WEB_USUARIO, cfg.WEB_PASSWORD)
    print(f"\nPagina web: abre http://{ip_local()}:{puerto} en el telefono (misma red Wi-Fi)\n")
    app.run(host="0.0.0.0", port=puerto, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
