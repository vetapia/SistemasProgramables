# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/test_e2e.py
# Objetivo:  Prueba de punta a punta con broker MQTT real, servidor con YOLO y placas simuladas
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
import os, sys, shutil, tempfile, json, threading, time as T, importlib
from datetime import datetime, timezone
AQUI=os.path.dirname(os.path.abspath(__file__))
REPO=os.path.abspath(os.path.join(AQUI,".."))
CLAVE="clave-e2e-XYZ"
real_sleep=T.sleep; real_time=T.time
# ---------- servidor (proceso real, en un hilo) ----------
sys.path.insert(0, REPO+"/servidor")
import config as scfg
scfg.BROKER="localhost"; scfg.MQTT_CLAVE=CLAVE
tmp_srv=tempfile.mkdtemp(); scfg.CARPETA_REGISTROS=tmp_srv+"/registros"; scfg.CARPETA_CAPTURAS=tmp_srv+"/capturas"
scfg.FIREBASE_LLAVE=tmp_srv+"/no-existe.json"
import mqtt_bridge
srv=mqtt_bridge.Servidor()
marcas=[]; srv.nube.marcar_comando=lambda i,e,n="": marcas.append((i,e))
srv.cliente.connect("localhost",1883); srv.cliente.loop_start()
real_sleep(0.5)
for m in ("config","ia","ia.detector","nube","mqtt_bridge"): sys.modules.pop(m,None)
sys.path.remove(REPO+"/servidor")
# ---------- placas simuladas ----------
tmp=tempfile.mkdtemp(); os.chdir(tmp)
os.makedirs("esp32"); os.makedirs("cam")
for f in ("main.py","red.py","firma.py"): shutil.copy(REPO+"/firmware/esp32/"+f, "esp32")
shutil.copytree(REPO+"/firmware/esp32/hal","esp32/hal")
c=open(REPO+"/firmware/esp32/config.example.py").read().replace('MQTT_CLAVE = ""','MQTT_CLAVE = "%s"'%CLAVE).replace('MQTT_BROKER = "broker.hivemq.com"','MQTT_BROKER = "localhost"')
open("esp32/config.py","w").write(c)
sys.path[:0]=[AQUI+"/fakes_real",AQUI+"/fakes_cam",AQUI+"/fakes",AQUI]
import reloj
# reloj virtual solo para las placas; el servidor usa el real (ya cargado)
import machine, telegram, camera
FOTO=open(REPO+"/media/ia-deteccion-persona.jpg","rb").read()
camera.Camera.capture=lambda self: FOTO
machine.forzar(18,0); machine.forzar(14,0)
os.chdir(tmp+"/esp32"); sys.path.insert(0,tmp+"/esp32")
reloj.instalar(); from reloj import Reloj
esp=importlib.import_module("main")
app=esp.BikeSafe()
sys.modules.pop("main"); sys.modules.pop("config"); sys.path.remove(tmp+"/esp32")
os.chdir(tmp+"/cam"); shutil.copy(REPO+"/firmware/camara/main.py",".")
cc=open(REPO+"/firmware/camara/config.example.py").read().replace("USAR_TELEGRAM = False","USAR_TELEGRAM = True").replace('MQTT_BROKER = "broker.hivemq.com"','MQTT_BROKER = "localhost"').replace("USAR_WEB = True","USAR_WEB = False")
open("config.py","w").write(cc); sys.path.insert(0,tmp+"/cam")
cam=importlib.import_module("main").Fotografo()
os.chdir(tmp+"/esp32")
u_esp=machine.UARTS[2]; u_cam=machine.UARTS[1]
ok=fallas=0
def check(c,t):
    global ok,fallas
    print(("  OK  " if c else "  XX FALLA: ")+t); 
    if c: ok+=1
    else: fallas+=1
def paso(ms_virtual, real=0.0):
    fin=Reloj.ms+ms_virtual
    while Reloj.ms<fin:
        app.vuelta()
        for s in u_esp.salida: u_cam.entrada+=s.encode()
        u_esp.salida.clear()
        o=cam._leer_orden()
        if o: cam.atender_orden(o)
        for s in u_cam.salida: u_esp.entrada+=s.encode()
        u_cam.salida.clear()
        Reloj.ms+=10
    if real: real_sleep(real)
def esperar(cond, seg=6):
    t0=real_time()
    while real_time()-t0<seg:
        paso(50, 0.05)
        if cond(): return True
    return False
paso(200,0.5)
print("== Dueno cierra por Telegram")
u_esp.entrada+=b"CMD|asegurar\n"; paso(300,0.3)
check(app.estado=="ASEGURADA","ESP32 asegurada")
check(any("ASEGURADA" in l[1] for l in telegram.LLAMADAS if l[0]=="msg"),"Telegram recibio 'bici ASEGURADA' (UART real entre placas)")
print("== Un toque -> foto AVISO -> servidor IA -> resultado firmado -> ESP32 decide")
machine.I2C.lectura=(0.3,0,1.0); paso(60); machine.I2C.lectura=(0,0,1.0)
ok_ia=esperar(lambda: app._ultima_ia is not None, 10)
check(ok_ia,"la ESP32 recibio y ACEPTO la firma del resultado de la IA: "+str(app._ultima_ia))
check(app.red.rechazados==0,"ningun mensaje rechazado")
check(any(l[0]=="foto" for l in telegram.LLAMADAS),"la foto llego a Telegram")
check(any("la IA confirmo una PERSONA" in l[1] for l in telegram.LLAMADAS if l[0]=="msg"),"Telegram: la IA confirmo persona")
check(app.estado=="ASEGURADA","1 persona = aviso (sigue ASEGURADA)")
print("== 2a foto con persona y la bici movida -> ROBO decidido en la ESP32")
app._ultima_ia=None; app._ultima_foto_ms-=30000
machine.I2C.lectura=(0.3,0,1.0); paso(60); machine.I2C.lectura=(0,0,1.0)
esperar(lambda: app.estado=="ALARMA", 10)
check(app.estado=="ALARMA","ALARMA: persona manipulando la bici")
print("== Dashboard pide 'silenciar' y luego 'liberar' (Firestore -> servidor -> MQTT firmado)")
srv.al_llegar_comando("doc1",{"cmd":"silenciar","estado":"pendiente","creado":datetime.now(timezone.utc),"nombre":"Oscar"})
esperar(lambda: app.estado=="ASEGURADA")
check(app.estado=="ASEGURADA","silenciada desde el dashboard")
srv.al_llegar_comando("doc2",{"cmd":"liberar","estado":"pendiente","creado":datetime.now(timezone.utc),"nombre":"Oscar"})
esperar(lambda: app.estado=="LIBRE")
check(app.estado=="LIBRE","LIBRE desde el dashboard")
check(("doc2","enviado") in marcas,"el servidor marca el comando como enviado")
srv.al_llegar_comando("doc2",{"cmd":"liberar","estado":"pendiente","nombre":"Oscar"})
check(marcas.count(("doc2","enviado"))==1,"no repite un comando ya atendido")
from datetime import timedelta
srv.al_llegar_comando("doc3",{"cmd":"liberar","estado":"pendiente","creado":datetime.now(timezone.utc)-timedelta(minutes=5)})
check(("doc3","caducado") in marcas,"comando de hace 5 min = caducado")
srv.al_llegar_comando("doc4",{"cmd":"formatear","estado":"pendiente"})
check(("doc4","rechazado") in marcas,"comando desconocido = rechazado")
real_sleep(1)
reg=scfg.CARPETA_REGISTROS
lst=sorted(os.listdir(reg)); print("   registros:", lst)
ev=[json.loads(l) for l in open(reg+"/eventos.jsonl")]
check(any(e["tipo"]=="estado" and e["origen"]=="telegram" for e in ev),"evento de estado guardado (origen telegram)")
check(any(e["tipo"]=="comando" and "dashboard" in e["origen"] for e in ev),"evento de comando del dashboard guardado")
ia=[json.loads(l) for l in open(reg+"/eventos_ia.jsonl")]
check(ia and ia[0]["deteccion"]=="persona" and ia[0]["modelo"]=="yolov5s-coco" and "imagen" in ia[0],"eventos_ia con persona, modelo YOLO y miniatura")
est=json.load(open(reg+"/estado_actual.json"))
check(est.get("estado")=="LIBRE" and est.get("cerrojo")=="CERRADO","estado_actual con estado y cerrojo: "+str({k:est.get(k) for k in ("estado","cerrojo","conexion","ultima_ia")}))
print("\nRESULTADO E2E: {} OK, {} fallas".format(ok,fallas))
os._exit(1 if fallas else 0)
