# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/fakes/network.py
# Objetivo:  Falso del modulo network (WiFi) para probar en la PC
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
STA_IF=0
class WLAN:
    conectado=True
    def __init__(self, i): pass
    def active(self, *a): return True
    def isconnected(self): return WLAN.conectado
    def connect(self, *a): pass
    def disconnect(self): pass
    def scan(self): return [(b"Prueba", b"", 1, -55, 3, 0)]
    def ifconfig(self): return ("192.168.0.50","255.255.255.0","","")
