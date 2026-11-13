# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/ia/detector.py
# Objetivo:  Detectar con OpenCV si hay una persona en la foto del candado
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Usa dos modelos que ya trae OpenCV (no hay que entrenar nada):
#
#   1. YuNet (red neuronal, archivo .onnx de 230 KB en ia/modelos/):
#      encuentra CARAS y da una confianza de 0 a 1. Es el principal,
#      porque el candado toma la foto de cerca (8 a 50 cm).
#   2. HOG + SVM de personas: encuentra CUERPOS completos, para cuando
#      la persona esta mas lejos y no se le ve bien la cara.
#
# La camara va de lado dentro del candado, asi que la foto se prueba
# girada 0, 90, 180 y 270 grados y se toma el mejor resultado.

import os

import cv2
import numpy as np

MODELO_CARAS = os.path.join(os.path.dirname(__file__), "modelos",
                            "face_detection_yunet_2023mar.onnx")

GIROS = {
    0: None,
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


class Resultado:
    """Lo que la IA decidio sobre una foto."""

    def __init__(self, clase, confianza, modelo, giro, cajas):
        self.clase = clase            # "persona" o "sin_persona"
        self.confianza = confianza    # 0 a 1
        self.modelo = modelo          # "caras-yunet" / "cuerpo-hog" / "-"
        self.giro = giro              # grados que hubo que girar la foto
        self.cajas = cajas            # recuadros [(x, y, w, h), ...]

    @property
    def hay_persona(self):
        return self.clase == "persona"

    def como_dict(self):
        return {"deteccion": self.clase, "confianza": round(self.confianza, 3),
                "modelo": self.modelo, "giro": self.giro}


class DetectorPersonas:
    def __init__(self, confianza_minima=0.6, probar_giros=True):
        self.confianza_minima = confianza_minima
        self.giros = GIROS if probar_giros else {0: None}
        self._caras = cv2.FaceDetectorYN.create(
            MODELO_CARAS, "", (320, 240), 0.5, 0.3, 50)
        # HOG viene en OpenCV 4; en OpenCV 5 solo con opencv-contrib-python.
        # Si no esta, la IA sigue funcionando solo con YuNet (caras).
        self._hog = None
        if hasattr(cv2, "HOGDescriptor"):
            self._hog = cv2.HOGDescriptor()
            self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # ---------- modelos ----------
    def _buscar_caras(self, img):
        alto, ancho = img.shape[:2]
        self._caras.setInputSize((ancho, alto))
        _, caras = self._caras.detect(img)
        if caras is None:
            return 0.0, []
        cajas = [tuple(int(v) for v in c[:4]) for c in caras]
        return float(max(c[-1] for c in caras)), cajas

    def _buscar_cuerpos(self, img):
        if self._hog is None:
            return 0.0, []
        # HOG necesita que la persona mida al menos 128 px de alto
        escala = 480 / max(img.shape[:2])
        chica = cv2.resize(img, None, fx=escala, fy=escala)
        cajas, pesos = self._hog.detectMultiScale(chica, winStride=(8, 8),
                                                  padding=(8, 8), scale=1.05)
        if len(cajas) == 0:
            return 0.0, []
        # El peso del SVM no es una probabilidad: lo pasamos a 0..1
        mejor = float(np.max(pesos))
        confianza = 1.0 / (1.0 + np.exp(-2.0 * (mejor - 0.5)))
        cajas = [tuple(int(v / escala) for v in c) for c in cajas]
        return float(confianza), cajas

    # ---------- decision ----------
    def analizar(self, img):
        """Recibe una imagen BGR de OpenCV y regresa un Resultado."""
        mejor = Resultado("sin_persona", 0.0, "-", 0, [])
        for grados, codigo in self.giros.items():
            girada = img if codigo is None else cv2.rotate(img, codigo)
            for modelo, funcion in (("caras-yunet", self._buscar_caras),
                                    ("cuerpo-hog", self._buscar_cuerpos)):
                confianza, cajas = funcion(girada)
                if confianza > mejor.confianza:
                    mejor = Resultado("sin_persona", confianza, modelo,
                                      grados, cajas)
        if mejor.confianza >= self.confianza_minima:
            mejor.clase = "persona"
        return mejor

    def analizar_jpeg(self, datos):
        """Igual que analizar(), pero recibe los bytes JPEG del MQTT."""
        img = cv2.imdecode(np.frombuffer(datos, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("el frame no es un JPEG valido")
        return img, self.analizar(img)

    @staticmethod
    def dibujar(img, resultado):
        """Regresa la foto (ya girada) con los recuadros y la decision."""
        codigo = GIROS.get(resultado.giro)
        salida = img.copy() if codigo is None else cv2.rotate(img, codigo)
        color = (0, 0, 255) if resultado.hay_persona else (0, 200, 0)
        for (x, y, w, h) in resultado.cajas:
            cv2.rectangle(salida, (x, y), (x + w, y + h), color, 2)
        texto = "{} {:.0f}%".format(resultado.clase, resultado.confianza * 100)
        cv2.rectangle(salida, (0, 0), (salida.shape[1], 22), (0, 0, 0), -1)
        cv2.putText(salida, texto, (5, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    color, 1, cv2.LINE_AA)
        return salida
