# ============================================
# Proyecto:  SmartClass
# Archivo:   firebase_opcional.py
# Objetivo:  Guarda lecturas, eventos de IA, estado y asistencias en Firestore y lee el histórico para el dashboard
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
"""Registro en Firebase (Firestore) para SmartClass.

Si junto a este archivo existe serviceAccountKey.json, el servidor guarda en Firestore:
  - lecturas/{timestamp}       sensores (cada cierto tiempo, no cada segundo)
  - eventos_ia/{timestamp}     cada decision de la IA: deteccion, accion, confianza
  - estado_actual/actual       ultimo valor de sensores y estado de actuadores
  - asistencias/{timestamp}    cada llegada nueva de un alumno
Si no existe la clave, no pasa nada y el sistema funciona igual.
Los envios se hacen en un hilo aparte para no frenar el reconocimiento.
"""
import os
import queue
import threading
from datetime import datetime, timedelta

DIR = os.path.dirname(os.path.abspath(__file__))
CLAVE = os.path.join(DIR, "serviceAccountKey.json")

_db = None
_firestore = None
_cola = queue.Queue(maxsize=500)


def activo():
    return _db is not None


def iniciar():
    global _db, _firestore
    if not os.path.exists(CLAVE):
        print("Firebase: desactivado (falta serviceAccountKey.json)")
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        firebase_admin.initialize_app(credentials.Certificate(CLAVE))
        _db = firestore.client()
        _firestore = firestore
        threading.Thread(target=_trabajador, daemon=True).start()
        print("Firebase: conectado")
    except Exception as e:
        print("Firebase: desactivado por error:", e)


def _trabajador():
    while True:
        tarea = _cola.get()
        try:
            tarea()
        except Exception as e:
            print("Firebase: error al registrar:", e)


def _encolar(tarea):
    if _db is None:
        return
    try:
        _cola.put_nowait(tarea)
    except queue.Full:
        print("Firebase: cola llena, se descarta un registro")


def _id_tiempo(ahora):
    return ahora.strftime("%Y-%m-%dT%H:%M:%S.") + "%03d" % (ahora.microsecond // 1000)


def _guardar(coleccion, documento, ahora=None):
    ahora = ahora or datetime.now()
    doc = dict(documento)
    doc["timestamp"] = ahora.isoformat(timespec="seconds")
    id_doc = _id_tiempo(ahora)

    def tarea():
        d = dict(doc)
        d["creado"] = _firestore.SERVER_TIMESTAMP
        _db.collection(coleccion).document(id_doc).set(d)

    _encolar(tarea)


def lectura(valores, ahora=None):
    _guardar("lecturas", valores, ahora)


def evento_ia(deteccion, accion, confianza, extra=None, ahora=None):
    doc = {"deteccion": deteccion, "accion": accion, "confianza": round(float(confianza), 3)}
    if extra:
        doc.update(extra)
    _guardar("eventos_ia", doc, ahora)


def asistencia(alumno_id, fecha, hora, ahora=None):
    _guardar("asistencias", {"alumno_id": alumno_id, "fecha": fecha, "hora": hora}, ahora)


def estado_actual(valores):
    doc = dict(valores)

    def tarea():
        d = dict(doc)
        d["creado"] = _firestore.SERVER_TIMESTAMP
        _db.collection("estado_actual").document("actual").set(d, merge=True)

    _encolar(tarea)


# ------------------------------------------------------------ lectura (dashboard)
def _donde(consulta, campo, operador, valor):
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        return consulta.where(filter=FieldFilter(campo, operador, valor))
    except ImportError:
        return consulta.where(campo, operador, valor)


def leer_historial(horas=24, limite=1500):
    """Lecturas de las ultimas 'horas', de la mas vieja a la mas nueva."""
    if _db is None:
        return []
    corte = (datetime.now() - timedelta(hours=horas)).isoformat(timespec="seconds")
    consulta = _donde(_db.collection("lecturas"), "timestamp", ">=", corte)
    consulta = consulta.order_by("timestamp", direction=_firestore.Query.DESCENDING).limit(limite)
    filas = []
    for doc in consulta.stream():
        d = doc.to_dict()
        fila = {"t": d.get("timestamp")}
        for campo in ("temperatura", "humedad", "distancia_cm", "ir_puerta", "ir_dispensador"):
            if d.get(campo) is not None:
                fila[campo] = d[campo]
        if fila["t"]:
            filas.append(fila)
    filas.reverse()
    return filas


def leer_eventos(limite=300):
    """Ultimos eventos de la IA, de el mas viejo al mas nuevo."""
    if _db is None:
        return []
    consulta = _db.collection("eventos_ia").order_by(
        "timestamp", direction=_firestore.Query.DESCENDING).limit(limite)
    filas = []
    for doc in consulta.stream():
        d = doc.to_dict()
        if d.get("timestamp"):
            filas.append({"t": d["timestamp"], "deteccion": d.get("deteccion", ""),
                          "accion": d.get("accion", ""), "confianza": d.get("confianza", 0)})
    filas.reverse()
    return filas
