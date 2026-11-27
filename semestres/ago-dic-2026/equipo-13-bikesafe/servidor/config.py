# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/config.py
# Objetivo:  Ajustes del servidor Python: broker MQTT, IA y Firebase
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Este archivo SI esta en GitHub, asi que aqui NO van secretos. Los dos
# secretos del servidor viven en archivos que estan en .gitignore:
#   - serviceAccountKey.json  (llave de Firebase)
#   - clave_mqtt.txt          (clave para firmar los mensajes MQTT)

import os

AQUI = os.path.dirname(os.path.abspath(__file__))

# ---------- Broker MQTT ----------
# broker.hivemq.com es publico y gratis: sirve con cualquier WiFi que
# tenga internet (escuela u hotspot). Para usar Mosquitto en la laptop
# pongan "localhost" (y la IP de la laptop en las placas).
BROKER = "broker.hivemq.com"
PUERTO = 1883


def _leer_clave():
    """La clave para FIRMAR los mensajes que van a la ESP32 (ver
    firmware/esp32/firma.py). Debe ser igual a MQTT_CLAVE del config.py
    de la ESP32. Se lee de la variable BIKESAFE_CLAVE o de clave_mqtt.txt."""
    clave = os.environ.get("BIKESAFE_CLAVE", "").strip()
    ruta = os.path.join(AQUI, "clave_mqtt.txt")
    if not clave and os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            clave = f.read().strip()
    return clave


MQTT_CLAVE = _leer_clave()

# ---------- Inteligencia artificial ----------
# El servidor solo INFORMA lo que ve; la ESP32 decide la alarma con su
# propio umbral (IA_CONFIANZA_MINIMA en su config.py).
# Desde que confianza se reporta "persona" (0 a 1):
CONFIANZA_MINIMA = 0.45
# La camara va dentro del candado viendo hacia arriba, asi que la IA
# prueba la foto en varios giros y se queda con el mejor resultado.
PROBAR_GIROS = True
# Fotos analizadas con sus recuadros (no se suben a GitHub)
CARPETA_CAPTURAS = os.path.join(AQUI, "capturas")

# ---------- Firebase (Cloud Firestore) ----------
# Descarguen la llave desde la consola de Firebase:
#   Configuracion del proyecto > Cuentas de servicio > Generar nueva clave
# y guardenla junto a este archivo con este nombre. NUNCA la suban a GitHub.
FIREBASE_LLAVE = os.path.join(AQUI, "serviceAccountKey.json")
# Cada cuanto se guarda una lectura de sensores en el historico
GUARDAR_LECTURA_CADA_S = 5
# Si no hay llave de Firebase, todo se guarda en archivos .jsonl aqui:
CARPETA_REGISTROS = os.path.join(AQUI, "registros")

# ---------- Comandos desde el dashboard ----------
# Los botones del dashboard escriben en Firestore (coleccion comandos).
# Este servidor los ESCUCHA en tiempo real y se los pasa a la ESP32.
# Un comando mas viejo que esto se descarta (por si el servidor estuvo
# apagado y alguien pico "Abrir" hace una hora).
COMANDO_CADUCA_S = 60
