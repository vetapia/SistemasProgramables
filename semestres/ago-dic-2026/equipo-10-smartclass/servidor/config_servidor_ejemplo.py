# ============================================
# Proyecto:  SmartClass
# Archivo:   config_servidor_ejemplo.py
# Objetivo:  Ejemplo de configuración del servidor (se copia como config_servidor.py y se cambia la contraseña)
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
BROKER = "localhost"
PUERTO_MQTT = 1883
PUERTO_WEB = 5000
WEB_USUARIO = "docente"
WEB_PASSWORD = "CAMBIA_ESTA_CONTRASENA"
UMBRAL_SIMILITUD = 0.40
MUESTRAS_REGISTRO = 10
INTERVALO_LECTURAS_S = 60
INTERVALO_ESTADO_S = 15
ALERTA_TEMP_C = 30
ALERTA_TEMP_CRITICA_C = 35
VENTANA_NO_REGISTRADOS_MIN = 30
