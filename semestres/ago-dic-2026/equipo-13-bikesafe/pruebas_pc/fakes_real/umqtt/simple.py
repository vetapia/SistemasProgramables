# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/fakes_real/umqtt/simple.py
# Objetivo:  umqtt.simple de prueba conectado a un broker MQTT real con paho
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
# umqtt.simple de mentiras, pero conectado a un broker REAL con paho
import paho.mqtt.client as _m, threading
class MQTTClient:
    def __init__(self, cid, broker, port=1883, keepalive=0):
        self.c=_m.Client(_m.CallbackAPIVersion.VERSION2, client_id=cid); self.broker=broker; self.port=port
        self.cola=[]; self.lock=threading.Lock(); self.cb=None
        self.c.on_message=self._msg
    def _msg(self,c,u,m):
        with self.lock: self.cola.append((m.topic.encode(), bytes(m.payload)))
    def set_last_will(self,t,m,retain=False): self.c.will_set(t.decode(),m,retain=retain)
    def set_callback(self,f): self.cb=f
    def connect(self,timeout=None):
        self.c.connect(self.broker,self.port); self.c.loop_start()
        import time; time.sleep(0.2)
    def subscribe(self,t): self.c.subscribe(t.decode())
    def publish(self,t,m,retain=False,qos=0):
        self.c.publish(t.decode() if isinstance(t,bytes) else t, m, retain=retain)
    def check_msg(self):
        with self.lock: q=list(self.cola); self.cola.clear()
        for t,m in q: self.cb(t,m)
    def ping(self): pass
