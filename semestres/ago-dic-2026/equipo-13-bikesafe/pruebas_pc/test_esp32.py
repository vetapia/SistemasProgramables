# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   pruebas_pc/test_esp32.py
# Objetivo:  Pruebas del firmware de la ESP32 cerebro (50 casos)
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
import os, sys, shutil, json, tempfile
AQUI=os.path.dirname(os.path.abspath(__file__))
FW=os.path.join(AQUI,"..","firmware","esp32")
tmp=tempfile.mkdtemp(); os.chdir(tmp)
for f in ("main.py","red.py","firma.py"): shutil.copy(os.path.join(FW,f), tmp)
shutil.copytree(os.path.join(FW,"hal"), os.path.join(tmp,"hal"))
cfg=open(os.path.join(FW,"config.example.py")).read()
cfg=cfg.replace('MQTT_CLAVE = ""','MQTT_CLAVE = "clave-de-prueba-123"')
open("config.py","w").write(cfg)
sys.path[:0]=[AQUI+"/fakes",AQUI,tmp]
import reloj; reloj.instalar(); from reloj import Reloj
import machine, network
from umqtt import simple
import firma, config
import main as M

ok=0; fallas=0
def check(cond, texto):
    global ok, fallas
    if cond: ok+=1; print("  OK ", texto)
    else: fallas+=1; print("  XX FALLA:", texto)

def correr(ms):
    fin=Reloj.ms+ms
    while Reloj.ms<fin:
        app.vuelta(); Reloj.ms+=10

uart=lambda: machine.UARTS[2]
def salida(): s=list(uart().salida); uart().salida.clear(); return s
def cmd_tg(c): uart().entrada += ("CMD|"+c+"\n").encode()
cli=lambda: simple.CLIENTES[-1]
def pubs(topico): return [m for t,m,r in cli().pub if t==topico]
contador=[1795000000000]
def mqtt(topico, texto, firmar=True, cont=None):
    if firmar:
        contador[0]+=1
        texto=firma.firmar(config.MQTT_CLAVE, texto, cont or contador[0])
    cli().cola.append((topico, texto.encode()))

# reed: GPIO18, pull-up; 0 = cerrado (iman cerca)
machine.forzar(18, 1)        # cable FUERA
machine.forzar(14, 0)        # lazo entero (cable a GND)
print("== Arranque")
app=M.BikeSafe()
check(app.estado=="LIBRE","arranca LIBRE")
correr(50)
check(cli().will==(b"bikesafe/conexion", b"offline", True),"ultima voluntad offline")
check("online" in pubs(b"bikesafe/conexion"),"publica online")
check(cli().cid.startswith("bikesafe-esp32-"),"id de cliente unico: "+cli().cid)
correr(1000)
check(app.luz.color_actual in ("verde","apagado"),"LIBRE parpadea verde")

print("== Cerrar con el cable fuera (reed ABIERTO)")
salida(); cmd_tg("asegurar"); correr(100)
s=salida()
check(app.estado=="LIBRE","no asegura sin cable")
check(any("NO cerre" in x for x in s),"avisa por Telegram que no cerro")

print("== Cerrar con el cable metido")
machine.forzar(18, 0); cmd_tg("asegurar"); correr(200)
s=salida()
check(app.estado=="ASEGURADA","queda ASEGURADA")
check(any("ASEGURADA" in x for x in s),"Telegram: bici ASEGURADA")
check(open("estado.txt").read()=="ASEGURADA","guarda estado.txt")
check(app.luz.color_actual=="azul","LED azul fijo")
ev=[json.loads(m) for m in pubs(b"bikesafe/evento")]
check(any(e["tipo"]=="estado" and e["detalle"]=="LIBRE -> ASEGURADA" and e["origen"]=="telegram" for e in ev),"evento de estado con origen telegram")

print("== Un toque (nivel 1)")
salida(); machine.I2C.lectura=(0.3,0.0,1.0); correr(60); machine.I2C.lectura=(0.0,0.0,1.0); correr(500)
s=salida()
check(app.estado=="ASEGURADA","sigue ASEGURADA tras un toque")
check(any(x.startswith("FOTO|AVISO|Movimiento (1 de 4)") for x in s),"pide foto de AVISO")

print("== IA (firmada) ve persona: 1a vez = aviso morado")
salida(); mqtt(b"bikesafe/ia/resultado", json.dumps({"clase":"persona","conf":0.82}))
correr(50)
s=salida()
check(app.estado=="ASEGURADA","persona sola = aviso, no robo")
check(any("la IA confirmo una PERSONA" in x and "82%" in x for x in s),"Telegram: IA confirmo persona 82%")
check(app.luz.color_actual=="morado","LED morado")
print("== IA 2a persona + la bici se movio = ROBO")
mqtt(b"bikesafe/ia/resultado", json.dumps({"clase":"persona","conf":0.77})); correr(50)
s=salida()
check(app.estado=="ALARMA","pasa a ALARMA")
check(any("FOTO|ROBO|IA: persona manipulando" in x for x in s),"foto de ROBO por IA")
check(app.buzzer.sonando,"sirena prendida")
print("== Rafaga de fotos")
correr(13000); s=salida()
check(sum(1 for x in s if x.startswith("FOTO|ROBO|Foto extra"))==2,"2 fotos extra en la rafaga")
print("== Silenciar desde Telegram")
cmd_tg("silenciar"); correr(50); s=salida()
check(app.estado=="ASEGURADA" and not app.buzzer.sonando,"se calla y sigue ASEGURADA")
check(any("silenciada" in x for x in s),"contesta silenciada")

print("== Cerrojo abierto a la fuerza (reed ABIERTO > 0.5 s)")
machine.forzar(18, 1); correr(300)
check(app.estado=="ASEGURADA","300 ms todavia no")
correr(500)
check(app.estado=="ALARMA","ALARMA por cerrojo forzado")
check(any("Cerrojo abierto a la fuerza" in m for m in pubs(b"bikesafe/alerta")),"alerta MQTT del cerrojo")
machine.forzar(18, 0)

print("== Fin automatico de la alarma (60 s)")
salida(); correr(61000); s=salida()
check(app.estado=="ASEGURADA","se calla sola al minuto")
check(any("se apago sola" in x for x in s),"avisa por Telegram")

print("== Seguridad MQTT")
mqtt(b"bikesafe/cmd","liberar",firmar=False); correr(30)
check(app.estado=="ASEGURADA","rechaza 'liberar' SIN firma")
cli().cola.append((b"bikesafe/cmd", b"liberar|1795000009999|0000000000000000")); correr(30)
check(app.estado=="ASEGURADA","rechaza firma falsa")
viejo=firma.firmar("otra-clave","liberar",1795999999999)
cli().cola.append((b"bikesafe/cmd", viejo.encode())); correr(30)
check(app.estado=="ASEGURADA","rechaza firma con otra clave")
check(app.red.rechazados==3,"cuenta 3 rechazados")
print("== Liberar firmado desde el dashboard")
salida(); mqtt(b"bikesafe/cmd","liberar"); correr(50); s=salida()
check(app.estado=="LIBRE","abre con mensaje firmado")
check(any("LIBERADA (desde dashboard)" in x for x in s),"avisa al dueno por Telegram que se abrio desde el dashboard")
print("== Repeticion del mismo mensaje (replay)")
machine.forzar(18,0); cmd_tg("asegurar"); correr(50)
repetido=firma.firmar(config.MQTT_CLAVE,"liberar",contador[0])   # mismo contador que el anterior
cli().cola.append((b"bikesafe/cmd", repetido.encode())); correr(30)
check(app.estado=="ASEGURADA","rechaza mensaje repetido (replay)")
check(open("contador.txt").read()==str(contador[0]),"guarda el contador en flash")

print("== Estado por Telegram")
salida(); cmd_tg("estado"); correr(30); s=salida()
txt=[x for x in s if x.startswith("MSG|BikeSafe: ASEGURADA")]
check(bool(txt) and "Cerrojo (sensor magnetico): CERRADO" in txt[0] and "~" in txt[0],"estado con cerrojo y saltos ~")
print("   ", txt[0][:160] if txt else s)

print("== Acelerometro desconectado")
salida(); machine.I2C.falla=True; correr(400); s=salida()
check(any("FOTO|AVISO|El acelerometro no responde" in x for x in s),"aviso de acelerometro desconectado")
machine.I2C.falla=False; correr(200)
check(app.estado=="ASEGURADA","se recupera sin alarma")

print("== Lazo cortado (GPIO14)")
machine.forzar(14,1); correr(300)
check(app.estado=="ALARMA","cable cortado = ALARMA")
machine.forzar(14,0)
cmd_tg("silenciar"); correr(50)

print("== Inclinacion > 25 grados por 1.2 s")
machine.I2C.lectura=(0.0,0.6,0.8); correr(1500)
check(app.estado=="ALARMA","bici levantada = ALARMA")
machine.I2C.lectura=(0.0,0.0,1.0); cmd_tg("silenciar"); correr(50)

print("== Presencia con ultrasonico (3 s a < 50 cm)")
salida(); app._ultima_foto_ms-=30000; machine.DISTANCIA[0]=30.0; correr(3800); s=salida()
check(any(x.startswith("FOTO|PRESENCIA|Alguien a 30 cm") for x in s),"foto de PRESENCIA")
machine.DISTANCIA[0]=150.0

print("== Buscar y comandos de actuador")
cmd_tg("buscar"); correr(100)
check(app.buzzer.sonando and app.luz.color_actual in ("blanco","apagado"),"Buscar: suena y parpadea blanco")
correr(5200)
check(not app.buzzer.sonando and app.luz.color_actual=="azul","Buscar termina y regresa a azul")
mqtt(b"bikesafe/led/cmd","morado"); correr(30)
check(app.luz.color_actual=="morado","led/cmd morado (actuador por MQTT)")
mqtt(b"bikesafe/led/cmd","normal"); correr(30)
check(app.luz.color_actual=="azul","led/cmd normal")

print("== Publicacion de sensores")
cli().pub.clear(); correr(2100)
js=[json.loads(m) for m in pubs(b"bikesafe/sensores")]
check(js and js[-1]["cerrojo"]=="CERRADO" and js[-1]["lazo"]=="ENTERO" and "luz" in js[-1],"JSON de sensores con cerrojo, lazo y luz: "+str(js[-1] if js else None))
check(pubs(b"bikesafe/sensor/cerrojo")[-1]=="CERRADO","topico bikesafe/sensor/cerrojo")
check(cli().pings>=1,"manda ping MQTT")

print("== Reinicio con la bici asegurada (se va la luz)")
app2=M.BikeSafe()
check(app2.estado=="ASEGURADA","al volver la luz sigue ASEGURADA")

print("\nRESULTADO: {} OK, {} fallas".format(ok, fallas))
sys.exit(1 if fallas else 0)
