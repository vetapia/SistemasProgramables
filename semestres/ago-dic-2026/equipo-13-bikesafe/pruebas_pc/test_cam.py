# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/test_cam.py
# Objetivo:  Pruebas del firmware de la Freenove y su bot (17 casos)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
import os, sys, shutil, tempfile, json
AQUI=os.path.dirname(os.path.abspath(__file__))
FW=os.path.join(AQUI,"..","firmware","camara")
tmp=tempfile.mkdtemp(); os.chdir(tmp)
shutil.copy(os.path.join(FW,"main.py"), tmp)
cfg=open(os.path.join(FW,"config.example.py")).read().replace("USAR_TELEGRAM = False","USAR_TELEGRAM = True").replace('TELEGRAM_CHAT_ID = "000000000"','TELEGRAM_CHAT_ID = "555"').replace("USAR_WEB = True","USAR_WEB = False")
open("config.py","w").write(cfg)
sys.path[:0]=[AQUI+"/fakes_cam",AQUI+"/fakes",AQUI,tmp]
import reloj; reloj.instalar(); from reloj import Reloj
import machine, network, telegram
from umqtt import simple
import main as M
ok=fallas=0
def check(c,t):
    global ok,fallas
    if c: ok+=1; print("  OK ",t)
    else: fallas+=1; print("  XX FALLA:",t)
f=M.Fotografo()
uart=machine.UARTS[1]
def correr(ms):
    fin=Reloj.ms+ms
    while Reloj.ms<fin:
        o=f._leer_orden()
        if o: f.atender_orden(o)
        f._revisar_wifi(Reloj.ms); f._revisar_bot(Reloj.ms); f._reenviar_pendientes(Reloj.ms); f._mantener_mqtt(Reloj.ms)
        Reloj.ms+=20
def resp(): s=list(uart.salida); uart.salida.clear(); return s
correr(4000)
check(any(l[0]=="msg" and "encendido" in l[1] for l in telegram.LLAMADAS),"manda 'BikeSafe encendido' con botones")
print("== Botones")
telegram.LLAMADAS.clear(); resp()
telegram.ENTRADA += [("555","Cerrar")]; correr(3100)
check("CMD|asegurar\n" in resp(),"Cerrar -> CMD|asegurar")
telegram.ENTRADA += [("555","/Abrir@BikeSafe_bot")]; correr(3100)
check(any(l[0]=="msg" and l[2]=="confirmar" for l in telegram.LLAMADAS),"Abrir pide confirmacion")
telegram.ENTRADA += [("555","Sí, abrir")]; correr(3100)
check("CMD|liberar\n" in resp(),"'Si, abrir' -> CMD|liberar")
telegram.ENTRADA += [("555","si")]; correr(3100)
check("CMD|liberar\n" not in resp(),"'si' sin pedir Abrir antes NO abre")
print("== Extranos")
telegram.LLAMADAS.clear()
telegram.ENTRADA += [("999","Abrir"),("999","Cerrar")]; correr(3100)
r=resp()
check(not any("CMD|" in x for x in r),"ignora al extrano")
check(sum(1 for l in telegram.LLAMADAS if "Alguien mas (chat 999)" in l[1])==1,"avisa al dueno UNA vez")
print("== Foto pedida por la ESP32")
telegram.LLAMADAS.clear(); simple.CLIENTES.clear()
uart.entrada += "FOTO|ROBO|Cable cortado\n".encode(); correr(100)
check(any(l[0]=="foto" and "ROBO: Cable cortado" in l[1] for l in telegram.LLAMADAS),"manda la foto a Telegram con pie")
check("OK|FOTO|telegram\n" in resp(),"contesta OK|FOTO|telegram")
c=simple.CLIENTES[-1]
check([t for t,m,r in c.pub]==[b"bikesafe/cam/info",b"bikesafe/cam/frame"],"publica info + frame por MQTT")
check(json.loads(c.pub[0][1])["nivel"]=="ROBO","info en JSON valido")
check(c.cid.startswith("bikesafe-cam-"),"id MQTT unico "+c.cid)
print("== MQTT se cae: reintenta")
c.fallar_publish=1; c.pub.clear()
uart.entrada += "FOTO|AVISO|Movimiento (1 de 4)\n".encode(); correr(100)
c2=simple.CLIENTES[-1]
check(c2 is not c and len(c2.pub)==2,"reconecta y la foto SI llega al servidor")
correr(31000)
check(c2.pings>=1,"ping MQTT cada 30 s")
print("== Mensaje con saltos ~")
telegram.LLAMADAS.clear()
uart.entrada += "MSG|BikeSafe: ASEGURADA~Cerrojo: CERRADO\n".encode(); correr(60)
check(any(l[1]=="BikeSafe: ASEGURADA\nCerrojo: CERRADO" for l in telegram.LLAMADAS),"convierte ~ en salto de linea")
print("== Sin internet: guarda y reenvia")
telegram.FALLA[0]=True; network.WLAN.conectado=False; telegram.LLAMADAS.clear()
uart.entrada += "FOTO|ROBO|Forcejeo continuo\n".encode(); correr(100)
check(len(f._pendientes)==1,"guarda la alerta pendiente")
telegram.FALLA[0]=False; network.WLAN.conectado=True; correr(16000)
check(any(l[0]=="foto" and "Forcejeo" in l[1] for l in telegram.LLAMADAS) and not f._pendientes,"al volver el internet la manda")
print("\nRESULTADO: {} OK, {} fallas".format(ok,fallas))
sys.exit(1 if fallas else 0)
