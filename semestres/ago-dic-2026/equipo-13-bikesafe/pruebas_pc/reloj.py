# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/reloj.py
# Objetivo:  Reloj virtual (ticks_ms, sleep_ms) para correr el firmware rapido
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
import time, sys
class Reloj:
    ms=1000
def instalar():
    time.ticks_ms=lambda: Reloj.ms
    time.ticks_add=lambda a,b: a+b
    time.ticks_diff=lambda a,b: a-b
    def sleep_ms(x): Reloj.ms+=int(x)
    time.sleep_ms=sleep_ms
    time.sleep_us=lambda x: None
    time.sleep=lambda s: sleep_ms(s*1000)
    sys.print_exception=lambda e: __import__('traceback').print_exception(e)
