# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/fakes_cam/telegram.py
# Objetivo:  Falso de telegram.py que registra mensajes y fotos
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
LLAMADAS=[]; ENTRADA=[]; FALLA=[False]
def enviar_mensaje(t, c, texto, botones=False):
    if FALLA[0]: raise OSError("sin internet")
    LLAMADAS.append(("msg", texto, botones)); return True
def enviar_foto(t, c, jpg, pie=""):
    if FALLA[0]: raise OSError("sin internet")
    LLAMADAS.append(("foto", pie)); return True
def obtener_comandos(t, desde=0):
    if desde == -1: return [], 100
    l=list(ENTRADA); ENTRADA.clear(); return l, desde+len(l)
