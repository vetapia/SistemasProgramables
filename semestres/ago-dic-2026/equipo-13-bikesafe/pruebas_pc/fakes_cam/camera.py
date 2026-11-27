# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/fakes_cam/camera.py
# Objetivo:  Falso de la camara de la Freenove
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
class FrameSize: QVGA=1; VGA=2; SVGA=3
class PixelFormat: JPEG=1; RGB565=2; GRAYSCALE=3
class GrabMode: WHEN_EMPTY=0
class Camera:
    def __init__(self, **k): self.k=k
    def capture(self): return b"\xff\xd8FAKEJPEG\xff\xd9"
