# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/nube.py
# Objetivo:  Guardar lecturas, eventos de IA y estado actual en Firestore
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Estructura en Cloud Firestore (igual a la del curso):
#
#   proyectos/bikesafe                      <- documento del proyecto
#       /lecturas/{timestamp}               <- historico de sensores
#           distancia, movimiento, inclinacion, lazo, estado, ts
#       /eventos_ia/{timestamp}             <- cada decision de la IA
#           deteccion, accion, confianza, modelo, nivel, motivo,
#           imagen (JPEG chico en base64), ts
#       /alertas/{timestamp}                <- avisos del candado
#   proyectos/bikesafe/estado/actual        <- ultimo valor de todo
#
# Si no esta la llave de Firebase (serviceAccountKey.json), NO truena:
# guarda lo mismo en archivos .jsonl dentro de la carpeta registros/.

import base64
import json
import os
from datetime import datetime, timezone


def _ahora():
    return datetime.now(timezone.utc)


def _id(ts):
    # Un id que se ordena solo por fecha: 20261110T193055123
    return ts.strftime("%Y%m%dT%H%M%S%f")[:-3]


class Nube:
    def __init__(self, llave, carpeta_local):
        self.db = None
        self.carpeta_local = carpeta_local
        if os.path.exists(llave):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                firebase_admin.initialize_app(credentials.Certificate(llave))
                self.db = firestore.client()
                self.raiz = self.db.collection("proyectos").document("bikesafe")
                self.raiz.set({"nombre": "BikeSafe", "equipo": 13}, merge=True)
                print("[nube] Conectado a Firebase (Firestore)")
            except Exception as e:
                print("[nube] No pude conectar a Firebase:", e)
                self.db = None
        else:
            print("[nube] Sin", llave, "-> guardo en la carpeta", carpeta_local)
        if self.db is None:
            os.makedirs(carpeta_local, exist_ok=True)

    @property
    def en_firebase(self):
        return self.db is not None

    # ---------- escritura ----------
    def _agregar(self, coleccion, datos):
        ts = _ahora()
        datos = dict(datos, ts=ts)
        if self.db:
            self.raiz.collection(coleccion).document(_id(ts)).set(datos)
        else:
            datos["ts"] = ts.isoformat()
            ruta = os.path.join(self.carpeta_local, coleccion + ".jsonl")
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(json.dumps(datos, ensure_ascii=False) + "\n")

    def guardar_lectura(self, lectura):
        self._agregar("lecturas", lectura)

    def guardar_alerta(self, texto, estado):
        self._agregar("alertas", {"texto": texto, "estado": estado})

    def guardar_evento_ia(self, resultado, accion, nivel, motivo, jpeg_chico):
        datos = resultado.como_dict()
        datos.update(accion=accion, nivel=nivel, motivo=motivo)
        if jpeg_chico is not None:
            datos["imagen"] = base64.b64encode(jpeg_chico).decode()
        self._agregar("eventos_ia", datos)

    def actualizar_estado(self, cambios):
        cambios = dict(cambios, actualizado=_ahora())
        if self.db:
            self.raiz.collection("estado").document("actual").set(
                cambios, merge=True)
        else:
            ruta = os.path.join(self.carpeta_local, "estado_actual.json")
            previo = {}
            if os.path.exists(ruta):
                with open(ruta, encoding="utf-8") as f:
                    previo = json.load(f)
            cambios["actualizado"] = cambios["actualizado"].isoformat()
            previo.update(cambios)
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(previo, f, ensure_ascii=False, indent=2)
