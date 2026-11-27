# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/test_telegram.py
# Objetivo:  Pruebas de las peticiones HTTP de telegram.py
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
import sys, io, json, importlib.util
import os
AQUI=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location("telegram",os.path.join(AQUI,"..","firmware","camara","telegram.py"))
T=importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
class S:
    def __init__(self, resp): self.w=b""; self.r=io.BytesIO(resp)
    def write(self,b): self.w+=bytes(b); return len(b)
    def readline(self): return self.r.readline()
    def read(self,n=-1): return self.r.read(n)
    def close(self): pass
ultima=[]
def fake(resp):
    def c():
        s=S(resp); ultima.append(s); return s
    T._conectar=c
cuerpo=json.dumps({"ok":True,"result":[{"update_id":7,"message":{"chat":{"id":555},"text":"Cerrar"}},{"update_id":8,"message":{"chat":{"id":555},"text":"Sí, abrir"}}]}).encode()
fake(b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n"+cuerpo)
l,sig=T.obtener_comandos("TOKEN",5); print(l,sig); assert l==[("555","Cerrar"),("555","Sí, abrir")] and sig==9
assert b"offset=5" in ultima[-1].w
fake(b"HTTP/1.1 200 OK\r\n\r\n{}")
assert T.enviar_mensaje("TOKEN","555","Hola ñ\nadiós",botones=True)
w=ultima[-1].w.decode(); assert "reply_markup=" in w and "%C3%B1" in w and "Content-Length" in w
cab,body=w.split("\r\n\r\n",1); assert int(cab.split("Content-Length: ")[1].split("\r\n")[0])==len(body.encode()), "content-length"
fake(b"HTTP/1.1 200 OK\r\n\r\n{}")
assert T.enviar_foto("TOKEN","555",b"\xff\xd8abc\xff\xd9","pie")
w=ultima[-1].w; cab,body=w.split(b"\r\n\r\n",1); assert int(cab.split(b"Content-Length: ")[1].split(b"\r\n")[0])==len(body)
fake(b"HTTP/1.1 401 Unauthorized\r\n\r\n{}")
assert T.obtener_comandos("MAL",3)==([],3)
print("telegram.py OK")
