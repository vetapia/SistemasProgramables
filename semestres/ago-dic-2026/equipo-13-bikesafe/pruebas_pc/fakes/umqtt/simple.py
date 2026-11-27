# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/fakes/umqtt/simple.py
# Objetivo:  Falso de umqtt.simple que guarda lo publicado en listas
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
CLIENTES=[]
class MQTTClient:
    def __init__(self, cid, broker, port=1883, keepalive=0):
        self.cid=cid; self.pub=[]; self.subs=[]; self.cola=[]; self.cb=None; self.will=None; self.pings=0
        self.fallar_publish=0
        CLIENTES.append(self)
    def set_last_will(self, t, m, retain=False): self.will=(t,m,retain)
    def set_callback(self, f): self.cb=f
    def connect(self, timeout=None): pass
    def subscribe(self, t): self.subs.append(t)
    def publish(self, t, m, retain=False, qos=0):
        if self.fallar_publish: self.fallar_publish-=1; raise OSError(104)
        self.pub.append((t, m if isinstance(m,(bytes,bytearray)) else str(m), retain))
    def check_msg(self):
        while self.cola:
            t,m=self.cola.pop(0); self.cb(t,m)
    def ping(self): self.pings+=1
