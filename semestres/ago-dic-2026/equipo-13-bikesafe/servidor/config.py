# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   servidor/config.py
# Objetivo:  Ajustes del servidor Python: broker MQTT, IA y Firebase
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

# ---------- Broker MQTT (Mosquitto corre en esta misma compu) ----------
BROKER = "localhost"
PUERTO = 1883

# ---------- Inteligencia artificial ----------
# Confianza minima para decir "hay una persona en la foto" (0 a 1)
CONFIANZA_MINIMA = 0.60
# La camara va montada de lado en el candado, asi que la IA prueba la
# foto en varios giros y se queda con el mejor resultado.
PROBAR_GIROS = True
# Si la IA ve una persona, ordena al ESP32 que avise (pitidos + LED rojo)
ACTIVAR_ACTUADOR_SI_PERSONA = True
# Fotos analizadas con sus recuadros (no se suben a GitHub)
CARPETA_CAPTURAS = "capturas"

# ---------- Firebase (Cloud Firestore) ----------
# Descarguen la llave desde la consola de Firebase:
#   Configuracion del proyecto > Cuentas de servicio > Generar nueva clave
# y guardenla junto a este archivo con este nombre. NUNCA la suban a GitHub.
FIREBASE_LLAVE = "serviceAccountKey.json"
# Cada cuanto se guarda una lectura de sensores en el historico
GUARDAR_LECTURA_CADA_S = 5
# Si no hay llave de Firebase, todo se guarda en archivos .jsonl aqui:
CARPETA_REGISTROS = "registros"
