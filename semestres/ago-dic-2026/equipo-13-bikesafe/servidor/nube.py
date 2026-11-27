# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/nube.py
# Objetivo:  Guardar en Firestore todo lo que pasa (lecturas, alertas,
#            eventos, decisiones de la IA) y ESCUCHAR en tiempo real los
#            comandos que manda el dashboard
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Estructura en Cloud Firestore:
#
#   proyectos/bikesafe                      <- documento del proyecto
#       /lecturas/{id}      historico de sensores (cada 5 s)
#           distancia, movimiento, inclinacion, cerrojo, lazo, estado, ts
#       /alertas/{id}       avisos y robos: texto, estado, ts
#       /eventos/{id}       historial: cambios de estado, comandos,
#                           conexion, cerrojo... tipo, detalle, origen, ts
#       /eventos_ia/{id}    cada foto analizada: deteccion, confianza,
#                           personas, modelo, nivel, motivo, imagen, ts
#       /comandos/{id}      lo que pide el dashboard (lo ESCUCHAMOS):
#                           cmd, uid, nombre, estado, creado, enviado
#       /estado/actual      ultimo valor de todo (el dashboard lo escucha)
#
# Los ids se ordenan solos por fecha: 20261125T183055123
# Si no esta la llave de Firebase (serviceAccountKey.json) se guarda lo
# mismo en archivos .jsonl dentro de la carpeta registros/.

import base64
import json
import os
import threading
from datetime import datetime, timezone


def _ahora():
    return datetime.now(timezone.utc)


def _id(ts):
    return ts.strftime("%Y%m%dT%H%M%S%f")[:-3]


class Nube:
    def __init__(self, llave, carpeta_local):
        self.db = None
        self.carpeta_local = carpeta_local
        self._candado = threading.Lock()   # escrituras locales en orden
        self._escucha = None
        if os.path.exists(llave):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(credentials.Certificate(llave))
                self.db = firestore.client()
                self._firestore = firestore
                self.raiz = self.db.collection("proyectos").document("bikesafe")
                self.raiz.set({"nombre": "BikeSafe", "equipo": 13}, merge=True)
                print("[nube] Conectado a Firebase (Firestore)")
            except Exception as e:
                print("[nube] No pude conectar a Firebase:", e)
                self.db = None
        else:
            print("[nube] Sin", os.path.basename(llave),
                  "-> guardo en la carpeta", carpeta_local)
        if self.db is None:
            os.makedirs(carpeta_local, exist_ok=True)

    @property
    def en_firebase(self):
        return self.db is not None

    # ---------- escritura ----------
    def _agregar(self, coleccion, datos):
        ts = _ahora()
        datos = dict(datos, ts=ts)
        try:
            if self.db:
                self.raiz.collection(coleccion).document(_id(ts)).set(datos)
                return
        except Exception as e:
            print("[nube] Firestore fallo ({}), guardo local: {}".format(
                coleccion, e))
        datos["ts"] = ts.isoformat()
        ruta = os.path.join(self.carpeta_local, coleccion + ".jsonl")
        os.makedirs(self.carpeta_local, exist_ok=True)
        with self._candado, open(ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(datos, ensure_ascii=False) + "\n")

    def guardar_lectura(self, lectura):
        self._agregar("lecturas", lectura)

    def guardar_alerta(self, texto, estado):
        self._agregar("alertas", {"texto": texto, "estado": estado})

    def guardar_evento(self, tipo, detalle, origen="", estado=None):
        self._agregar("eventos", {"tipo": tipo, "detalle": detalle,
                                  "origen": origen, "estado": estado})

    def guardar_evento_ia(self, resultado, nivel, motivo, jpeg_chico):
        datos = resultado.como_dict()
        datos.update(nivel=nivel, motivo=motivo)
        if jpeg_chico is not None:
            datos["imagen"] = base64.b64encode(jpeg_chico).decode()
        self._agregar("eventos_ia", datos)

    def actualizar_estado(self, cambios):
        cambios = dict(cambios, actualizado=_ahora())
        try:
            if self.db:
                self.raiz.collection("estado").document("actual").set(
                    cambios, merge=True)
                return
        except Exception as e:
            print("[nube] No pude actualizar el estado:", e)
        ruta = os.path.join(self.carpeta_local, "estado_actual.json")
        with self._candado:
            previo = {}
            if os.path.exists(ruta):
                with open(ruta, encoding="utf-8") as f:
                    previo = json.load(f)
            cambios["actualizado"] = cambios["actualizado"].isoformat()
            previo.update(cambios)
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(previo, f, ensure_ascii=False, indent=2)

    # ---------- escucha en tiempo real ----------
    def escuchar_comandos(self, al_llegar):
        """Se queda escuchando la coleccion 'comandos' (on_snapshot).
        Cada comando NUEVO con estado 'pendiente' llama a
        al_llegar(id, datos). Firestore avisa en menos de 1 s."""
        if not self.db:
            print("[nube] Sin Firebase: el dashboard no puede mandar comandos")
            return False
        coleccion = self.raiz.collection("comandos")
        try:                                   # firebase-admin nuevo
            from google.cloud.firestore_v1.base_query import FieldFilter
            consulta = coleccion.where(
                filter=FieldFilter("estado", "==", "pendiente"))
        except ImportError:                    # firebase-admin viejo
            consulta = coleccion.where("estado", "==", "pendiente")

        def al_cambiar(fotos, cambios, hora_lectura):
            for c in cambios:
                if c.type.name in ("ADDED", "MODIFIED"):
                    try:
                        al_llegar(c.document.id, c.document.to_dict())
                    except Exception as e:
                        print("[nube] Error con el comando", c.document.id, e)

        self._escucha = consulta.on_snapshot(al_cambiar)
        print("[nube] Escuchando comandos del dashboard en tiempo real")
        return True

    def marcar_comando(self, doc_id, estado, nota=""):
        """pendiente -> enviado / rechazado / caducado (el dashboard lo
        ve cambiar en vivo)."""
        if not self.db:
            return
        self.raiz.collection("comandos").document(doc_id).set(
            {"estado": estado, "nota": nota, "procesado": _ahora()},
            merge=True)

    def detener(self):
        if self._escucha:
            self._escucha.unsubscribe()
