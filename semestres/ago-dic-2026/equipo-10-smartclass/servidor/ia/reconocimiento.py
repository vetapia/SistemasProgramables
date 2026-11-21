# ============================================
# Proyecto:  SmartClass
# Archivo:   reconocimiento.py
# Objetivo:  Detecta rostros (YuNet), los reconoce (SFace) y administra el registro de alumnos por vectores
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
"""Reconocimiento facial para SmartClass.

- MotorFacial: detector YuNet + reconocedor SFace (ambos vienen en OpenCV).
- RegistroAlumnos: guarda por alumno unos cuantos vectores numericos (no fotos)
  y busca a quien pertenece un rostro comparando similitud coseno.
"""
import json
import os
import threading
import uuid

import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
MODELO_YUNET = os.path.join(DIR, "face_detection_yunet_2023mar.onnx")
MODELO_SFACE = os.path.join(DIR, "face_recognition_sface_2021dec.onnx")


class MotorFacial:
    def __init__(self, umbral_deteccion=0.7):
        import cv2
        for ruta in (MODELO_YUNET, MODELO_SFACE):
            if not os.path.exists(ruta):
                raise FileNotFoundError(
                    f"Falta el modelo '{os.path.basename(ruta)}' en {DIR}. "
                    "Descargalo como indica la guia.")
        self._lock = threading.Lock()
        self.detector = cv2.FaceDetectorYN.create(
            MODELO_YUNET, "", (320, 320), umbral_deteccion, 0.3, 5000)
        self.sface = cv2.FaceRecognizerSF.create(MODELO_SFACE, "")

    def detectar(self, img):
        """Devuelve (fila_del_rostro_mas_grande, cuantos_rostros) o (None, 0)."""
        alto, ancho = img.shape[:2]
        with self._lock:
            self.detector.setInputSize((ancho, alto))
            _, caras = self.detector.detect(img)
        if caras is None or len(caras) == 0:
            return None, 0
        mayor = max(caras, key=lambda c: c[2] * c[3])
        return mayor, len(caras)

    def embedding(self, img, fila):
        """Vector de 128 numeros (normalizado) que describe el rostro."""
        fila = np.asarray(fila, dtype=np.float32)
        with self._lock:
            alineado = self.sface.alignCrop(img, fila)
            vec = self.sface.feature(alineado)
        vec = np.asarray(vec, dtype=np.float32).flatten()
        norma = np.linalg.norm(vec)
        return vec / norma if norma > 0 else vec


class RegistroAlumnos:
    def __init__(self, ruta, umbral=0.40):
        self.ruta = ruta
        self.umbral = umbral
        self._lock = threading.RLock()
        self._alumnos = {}      # id -> {"nombre": str, "embeddings": [[...], ...]}
        self._matrices = {}     # id -> matriz numpy (para comparar rapido)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        self._cargar()

    # ---------- persistencia ----------
    def _cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as f:
                self._alumnos = json.load(f)
        except FileNotFoundError:
            self._alumnos = {}
        except (ValueError, OSError) as e:
            print("Aviso: no se pudo leer alumnos.json (", e, "). Se guarda copia y se inicia vacio.")
            try:
                os.replace(self.ruta, self.ruta + ".corrupto")
            except OSError:
                pass
            self._alumnos = {}
        self._reconstruir()

    def _reconstruir(self):
        self._matrices = {
            i: np.array(a["embeddings"], dtype=np.float32)
            for i, a in self._alumnos.items() if a.get("embeddings")
        }

    def _guardar(self):
        tmp = self.ruta + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._alumnos, f, ensure_ascii=False)
        os.replace(tmp, self.ruta)

    # ---------- altas, bajas y cambios ----------
    def listar(self):
        with self._lock:
            lista = [{"id": i, "nombre": a["nombre"], "muestras": len(a.get("embeddings", []))}
                     for i, a in self._alumnos.items()]
        return sorted(lista, key=lambda x: x["nombre"].lower())

    def agregar(self, nombre, embeddings):
        with self._lock:
            alumno_id = uuid.uuid4().hex[:8]
            self._alumnos[alumno_id] = {
                "nombre": nombre,
                "embeddings": [np.round(np.asarray(e, dtype=np.float32), 5).tolist()
                               for e in embeddings],
            }
            self._reconstruir()
            self._guardar()
            return alumno_id

    def renombrar(self, alumno_id, nombre):
        with self._lock:
            if alumno_id not in self._alumnos:
                return False
            self._alumnos[alumno_id]["nombre"] = nombre
            self._guardar()
            return True

    def eliminar(self, alumno_id):
        with self._lock:
            if alumno_id not in self._alumnos:
                return False
            del self._alumnos[alumno_id]
            self._reconstruir()
            self._guardar()
            return True

    # ---------- reconocimiento ----------
    def identificar(self, vec):
        """Devuelve (id, nombre, similitud). id/nombre son None si no hay coincidencia."""
        mejor_id, mejor = None, -1.0
        with self._lock:
            for alumno_id, matriz in self._matrices.items():
                similitud = float(np.max(matriz @ vec))
                if similitud > mejor:
                    mejor, mejor_id = similitud, alumno_id
            if mejor_id is None:
                return None, None, 0.0
            if mejor >= self.umbral:
                return mejor_id, self._alumnos[mejor_id]["nombre"], mejor
            return None, None, mejor
