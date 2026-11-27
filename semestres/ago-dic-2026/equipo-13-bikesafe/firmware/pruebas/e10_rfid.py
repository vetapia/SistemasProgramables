# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas/e10_rfid.py
# Objetivo:  Probar el lector RFID RC522 y leer el codigo (UID) de tus llaveros
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# ANTES: sube lib/mfrc522.py a la ESP32 (carpeta /lib).
#
# QUE DEBES VER:
#   "Version del chip: 0x92" (o 0x91, 0x88, 0xb2) -> el lector responde.
#   "0x0" o "0xff" -> NO responde: revisa los 7 cables y que este
#                     alimentado con 3.3 V (NUNCA 5 V).
#   Al acercar un llavero:  "UID: A1B2C3D4"
#
# COPIA ese codigo en config.py, dentro de TARJETAS_AUTORIZADAS.

import time
from mfrc522 import MFRC522

lector = MFRC522(sck=18, mosi=23, miso=19, rst=4, cs=5)
print("Version del chip:", hex(lector.version()))
print("Acerca una tarjeta o llavero...")

ultimo = None
visto_ms = 0
while True:
    uid = lector.leer_uid()
    ahora = time.ticks_ms()
    if uid:
        # Solo lo imprime una vez por pasada (no 10 veces seguidas)
        if uid != ultimo or time.ticks_diff(ahora, visto_ms) > 1500:
            print("UID:", uid)
        ultimo = uid
        visto_ms = ahora
    time.sleep(0.1)
