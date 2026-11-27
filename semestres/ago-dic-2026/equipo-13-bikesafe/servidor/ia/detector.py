# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/ia/detector.py
# Objetivo:  Detectar PERSONAS (cuerpo completo o en parte) en la foto
#            del candado con una red neuronal YOLOv5 entrenada en COCO
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Antes usabamos YuNet, que solo encuentra CARAS. Si el ladron esta de
# espaldas, agachado o con gorra no habia deteccion. Ahora usamos
# YOLOv5s, un detector de OBJETOS: la clase 0 de COCO es "person" y la
# reconoce aunque solo se vea el cuerpo, un brazo o la cabeza de lado.
#
# - Modelo: ia/modelos/yolov5s.onnx (14 MB, 80 clases de COCO).
# - Corre con cv2.dnn (viene en OpenCV, no hay que instalar PyTorch).
#   Funciona en OpenCV 4.8+ y en OpenCV 5 (que ya no lee modelos Caffe
#   como MobileNet-SSD; por eso elegimos YOLO en formato ONNX).
# - La camara va dentro del candado viendo hacia arriba por la ventana
#   de la tapa, asi que la foto llega girada: la probamos a 0, 90, 180
#   y 270 grados y nos quedamos con el mejor resultado.
#
# Pasos de la deteccion:
#   1. "Letterbox": la foto se mete en un cuadro de 640x640 sin
#      deformarla (relleno gris).
#   2. La red regresa 25200 cajas candidatas, cada una con
#      [x, y, ancho, alto, objeto, 80 probabilidades de clase].
#   3. confianza = objeto * probabilidad de "person".
#   4. NMS (non-maximum suppression) junta las cajas encimadas.

import os

import cv2
import numpy as np

CARPETA_MODELOS = os.path.join(os.path.dirname(__file__), "modelos")
MODELO = os.path.join(CARPETA_MODELOS, "yolov5s.onnx")
CLASE_PERSONA = 0                    # en COCO, "person" es la clase 0
ENTRADA = 640                        # el modelo espera 640x640

GIROS = {
    0: None,
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


class Resultado:
    """Lo que la IA vio en una foto (sin decidir nada: eso lo hace
    la ESP32)."""

    def __init__(self, clase, confianza, modelo, giro, cajas):
        self.clase = clase            # "persona" o "sin_persona"
        self.confianza = confianza    # 0 a 1 (la mejor persona)
        self.modelo = modelo          # "yolov5s-coco"
        self.giro = giro              # grados que hubo que girar la foto
        self.cajas = cajas            # [(x, y, w, h, confianza), ...]

    @property
    def hay_persona(self):
        return self.clase == "persona"

    @property
    def personas(self):
        return len(self.cajas) if self.hay_persona else 0

    def como_dict(self):
        return {"deteccion": self.clase, "confianza": round(self.confianza, 3),
                "modelo": self.modelo, "giro": self.giro,
                "personas": self.personas}


class DetectorPersonas:
    def __init__(self, confianza_minima=0.45, probar_giros=True,
                 modelo=MODELO):
        if not os.path.exists(modelo):
            raise FileNotFoundError(
                "Falta el modelo {}. Esta en el repositorio en "
                "servidor/ia/modelos/".format(modelo))
        self.confianza_minima = confianza_minima
        self.giros = GIROS if probar_giros else {0: None}
        self.red = cv2.dnn.readNet(modelo)
        self.nombre = "yolov5s-coco"

    # ---------- un giro ----------
    def _personas(self, img):
        """Regresa la lista de personas [(x, y, w, h, conf)] en 'img'."""
        alto, ancho = img.shape[:2]
        escala = min(ENTRADA / ancho, ENTRADA / alto)
        nw, nh = int(round(ancho * escala)), int(round(alto * escala))
        lienzo = np.full((ENTRADA, ENTRADA, 3), 114, np.uint8)
        lienzo[:nh, :nw] = cv2.resize(img, (nw, nh))
        blob = cv2.dnn.blobFromImage(lienzo, 1 / 255.0, (ENTRADA, ENTRADA),
                                     swapRB=True)
        self.red.setInput(blob)
        salida = self.red.forward()
        salida = salida[0] if salida.ndim == 3 else salida

        conf = salida[:, 4] * salida[:, 5 + CLASE_PERSONA]
        # Ademas de "persona", la clase de persona debe ser la mas probable
        es_persona = np.argmax(salida[:, 5:], axis=1) == CLASE_PERSONA
        elegidas = np.where((conf >= 0.10) & es_persona)[0]
        if len(elegidas) == 0:
            return []
        cajas, confs = [], []
        for i in elegidas:
            cx, cy, w, h = salida[i, :4] / escala      # regreso a la foto
            cajas.append([int(cx - w / 2), int(cy - h / 2), int(w), int(h)])
            confs.append(float(conf[i]))
        quedan = cv2.dnn.NMSBoxes(cajas, confs, 0.10, 0.45)
        quedan = np.array(quedan).flatten() if len(quedan) else []
        lista = sorted(((*cajas[i], confs[i]) for i in quedan),
                       key=lambda c: -c[4])
        return self._quitar_contenidas(lista)

    @staticmethod
    def _quitar_contenidas(lista):
        """Si una caja queda casi toda DENTRO de otra mas segura, es la
        misma persona (p. ej. la cara dentro del cuerpo): se descarta."""
        final = []
        for x, y, w, h, c in lista:
            repetida = False
            for fx, fy, fw, fh, _ in final:
                ix = max(0, min(x + w, fx + fw) - max(x, fx))
                iy = max(0, min(y + h, fy + fh) - max(y, fy))
                if ix * iy > 0.6 * min(w * h, fw * fh):
                    repetida = True
                    break
            if not repetida:
                final.append((x, y, w, h, c))
        return final

    # ---------- decision ----------
    def analizar(self, img):
        """Recibe una imagen BGR de OpenCV y regresa un Resultado."""
        mejor = Resultado("sin_persona", 0.0, self.nombre, 0, [])
        for grados, codigo in self.giros.items():
            girada = img if codigo is None else cv2.rotate(img, codigo)
            personas = self._personas(girada)
            if personas and personas[0][4] > mejor.confianza:
                mejor = Resultado("sin_persona", personas[0][4], self.nombre,
                                  grados, personas)
        if mejor.confianza >= self.confianza_minima:
            mejor.clase = "persona"
            mejor.cajas = [c for c in mejor.cajas
                           if c[4] >= self.confianza_minima]
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
        if resultado.hay_persona:
            for (x, y, w, h, c) in resultado.cajas:
                cv2.rectangle(salida, (x, y), (x + w, y + h), color, 2)
                cv2.putText(salida, "persona {:.0f}%".format(c * 100),
                            (x + 2, max(12, y + 14)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.4, color, 1, cv2.LINE_AA)
        texto = "{} {:.0f}%".format(resultado.clase, resultado.confianza * 100)
        cv2.rectangle(salida, (0, 0), (salida.shape[1], 22), (0, 0, 0), -1)
        cv2.putText(salida, texto, (5, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    color, 1, cv2.LINE_AA)
        return salida
