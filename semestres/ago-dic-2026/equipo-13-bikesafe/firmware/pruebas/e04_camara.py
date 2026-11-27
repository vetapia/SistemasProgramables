# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e04_camara.py
# Objetivo:  Probar la camara de la Freenove sola: tomar una foto y guardarla (se corre en la FREENOVE)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# ANTES: la Freenove debe tener el firmware CON CAMARA.
#
# QUE DEBES VER: "Foto guardada: prueba.jpg (xxxxx bytes)".
# Luego en Thonny: Ver > Archivos, clic derecho en prueba.jpg >
# "Descargar a..." y abrela en la compu.
#
#   ImportError 'camera'  -> el firmware no trae camara.
#   Su Freenove trae la camara GC0308, que no hace JPEG sola: esta
#   prueba toma la foto "cruda" y la convierte con el modulo jpeg.
#   Guarda DOS fotos: prueba_color.jpg y prueba_gris.jpg.
#   Si sale un error de la camara: DESCONECTEN el USB 5 segundos
#   (el STOP de Thonny no reinicia la camara).
#   "la camara no inicio" -> revisa el cable plano naranja de la
#                            camara (que este bien metido y con seguro).

import time
from camera import Camera, FrameSize, PixelFormat, GrabMode
import jpeg

PINES = dict(data_pins=[4, 5, 18, 19, 36, 39, 34, 35], vsync_pin=25,
             href_pin=23, sda_pin=26, scl_pin=27, pclk_pin=22, xclk_pin=21,
             xclk_freq=10000000, powerdown_pin=-1, reset_pin=-1,
             fb_count=1, grab_mode=GrabMode.WHEN_EMPTY)

for nombre, formato, tipo in (("prueba_color.jpg", PixelFormat.RGB565, "RGB565_BE"),
                              ("prueba_gris.jpg", PixelFormat.GRAYSCALE, "GRAY")):
    cam = Camera(pixel_format=formato, frame_size=FrameSize.QVGA, **PINES)
    try:
        print("sensor:", cam.get_sensor_name())
    except Exception:
        pass
    cam.capture()                 # la primera sale oscura: se descarta
    time.sleep(0.3)
    crudo = cam.capture()
    foto = jpeg.Encoder(width=320, height=240, quality=80,
                        pixel_format=tipo).encode(crudo)
    with open(nombre, "wb") as f:
        f.write(foto)
    print("Foto guardada:", nombre, "(", len(foto), "bytes )")
    cam.deinit()
    time.sleep(0.5)

print("Listo. Descarguen las dos fotos y vean cual se ve mejor.")
print("Si la de color sale con colores raros: FOTO_A_COLOR = False en config.py")
