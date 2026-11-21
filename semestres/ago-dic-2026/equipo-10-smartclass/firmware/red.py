# ============================================
# Proyecto:  SmartClass
# Archivo:   red.py
# Objetivo:  Conexión WiFi y MQTT con red de configuración, común a los dos nodos
# Equipo:   Aldo Emmanuel Carrillo Gomez (23240343), Juan Daniel Torres Uribe (23240326)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# =====================================================================
"""Wi-Fi, conexion al servidor MQTT y red de configuracion (comun a los dos nodos).

- Los datos de red salen de config.py y, si existe, de wifi.json (que gana).
- Si no logra conectarse, la placa crea su propia red "SmartClass-Setup" con una
  pagina (http://192.168.4.1) para escribir la red Wi-Fi y la IP del servidor.
"""
import json
import socket
import time

import machine
import network

ARCHIVO = "wifi.json"
AP_NOMBRE = "SmartClass-Setup"
AP_CLAVE = "smartclass123"


def _pausa(ms, tick=None):
    fin = time.ticks_add(time.ticks_ms(), ms)
    while time.ticks_diff(fin, time.ticks_ms()) > 0:
        if tick:
            tick()
        time.sleep_ms(50)


# ------------------------------------------------------------ ajustes guardados
def cargar():
    datos = {"ssid": "", "password": "", "broker": "", "puerto": 1883}
    try:
        import config
        datos["ssid"] = getattr(config, "WIFI_SSID", "")
        datos["password"] = getattr(config, "WIFI_PASS", "")
        datos["broker"] = getattr(config, "MQTT_BROKER", "")
        datos["puerto"] = getattr(config, "MQTT_PORT", 1883)
    except ImportError:
        pass
    try:
        with open(ARCHIVO) as f:
            extra = json.load(f)
        if extra.get("ssid"):
            datos["ssid"] = extra["ssid"]
            datos["password"] = extra.get("password", "")
        if extra.get("broker"):
            datos["broker"] = extra["broker"]
    except (OSError, ValueError):
        pass
    return datos


def guardar(ssid, password, broker=None):
    datos = cargar()
    datos["ssid"] = ssid
    datos["password"] = password
    if broker:
        datos["broker"] = broker
    with open(ARCHIVO, "w") as f:
        json.dump({"ssid": datos["ssid"], "password": datos["password"],
                   "broker": datos["broker"]}, f)


# ------------------------------------------------------------ Wi-Fi
def conectar(ssid, password, timeout_s=20, tick=None):
    wlan = network.WLAN(network.STA_IF)
    try:
        wlan.disconnect()
    except Exception:
        pass
    wlan.active(False)
    time.sleep_ms(200)
    wlan.active(True)
    try:
        wlan.config(pm=network.WLAN.PM_NONE)   # sin ahorro de energia: menos retardos
    except Exception:
        pass
    wlan.connect(ssid, password)
    t0 = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
            return False
        if tick:
            tick()
        time.sleep_ms(300)
    return True


def asegurar_wifi(tick=None, mostrar=None, fallos_para_portal=3):
    """Conecta al Wi-Fi guardado. Tras varios fallos abre la red de configuracion."""
    fallos = 0
    while True:
        datos = cargar()
        if datos["ssid"]:
            if mostrar:
                mostrar(["Conectando", "Wi-Fi...", datos["ssid"][:16]])
            if conectar(datos["ssid"], datos["password"], 20, tick):
                print("WiFi OK. IP:", network.WLAN(network.STA_IF).ifconfig()[0])
                return datos
            fallos += 1
            print("No se pudo conectar a", datos["ssid"], "- intento", fallos)
        else:
            fallos = fallos_para_portal      # no hay red guardada: directo al portal
        if fallos >= fallos_para_portal:
            portal(datos, tick, mostrar)
            fallos = 0


# ------------------------------------------------------------ servidor MQTT
def conectar_mqtt(datos, client_id, callback, topicos):
    from umqtt.simple import MQTTClient
    cliente = MQTTClient(client_id, datos["broker"], port=datos["puerto"], keepalive=30)
    cliente.set_callback(callback)
    try:
        cliente.connect(timeout=10)
    except TypeError:                # umqtt viejo sin parametro timeout
        cliente.connect()
    for topico in topicos:
        cliente.subscribe(topico)
    print("MQTT conectado y suscrito")
    return cliente


def conectar_servidor(datos, client_id, callback, topicos, tick=None, mostrar=None,
                      fallos_para_portal=6):
    """Reintenta hasta conectar. Si el servidor no aparece, abre la red de configuracion."""
    fallos = 0
    while True:
        try:
            if not network.WLAN(network.STA_IF).isconnected():
                datos = asegurar_wifi(tick, mostrar)
            if mostrar:
                mostrar(["Conectando al", "servidor..."])
            return conectar_mqtt(datos, client_id, callback, topicos)
        except OSError as e:
            fallos += 1
            print("Servidor MQTT no responde:", e, "- intento", fallos)
            if fallos >= fallos_para_portal:
                portal(datos, tick, mostrar)
                datos = cargar()
                fallos = 0
            _pausa(2000, tick)


def publicar(cliente, topico, contenido, timeout_s=8):
    """Publica con limite de tiempo: si la red se atora, falla en lugar de congelarse."""
    cliente.sock.settimeout(timeout_s)
    cliente.publish(topico, contenido)


# ------------------------------------------------------------ red de configuracion
def _urldecode(texto):
    texto = texto.replace("+", " ")
    salida = bytearray()
    i = 0
    n = len(texto)
    while i < n:
        if texto[i] == "%" and i + 2 < n:
            try:
                salida.append(int(texto[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        salida.extend(texto[i].encode())
        i += 1
    try:
        return salida.decode()
    except Exception:
        return "".join(chr(b) for b in salida)


def _esc(texto):
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


PAGINA = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SmartClass</title>
<style>body{font-family:sans-serif;max-width:420px;margin:20px auto;padding:0 14px}
input{width:100%%;padding:10px;margin:6px 0 14px;box-sizing:border-box}
button{padding:12px 18px;width:100%%}</style></head><body>
<h2>SmartClass</h2><p>Escribe la red Wi-Fi y la direccion IP de la laptop (servidor).</p>
<form method="POST" action="/guardar">
<label>Red Wi-Fi</label><input name="ssid" value="%s">
<label>Contrasena</label><input name="password" type="password">
<label>IP del servidor</label><input name="broker" value="%s">
<button>Guardar y reiniciar</button></form></body></html>"""

PAGINA_OK = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
             "<meta name='viewport' content='width=device-width,initial-scale=1'></head>"
             "<body style='font-family:sans-serif;padding:20px'>"
             "<h2>Guardado</h2><p>La placa se reinicia y se conecta a la nueva red.</p></body></html>")


def _responder(conn, cuerpo):
    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
              b"Connection: close\r\n\r\n")
    conn.send(cuerpo.encode())


def _leer(conn):
    datos = b""
    while b"\r\n\r\n" not in datos:
        trozo = conn.recv(512)
        if not trozo:
            break
        datos += trozo
        if len(datos) > 4096:
            break
    cabecera, _, cuerpo = datos.partition(b"\r\n\r\n")
    lineas = cabecera.split(b"\r\n")
    primera = lineas[0].decode().split(" ")
    metodo = primera[0]
    ruta = primera[1] if len(primera) > 1 else "/"
    largo = 0
    for linea in lineas[1:]:
        if linea.lower().startswith(b"content-length:"):
            largo = int(linea.split(b":")[1].strip())
    while len(cuerpo) < largo and len(cuerpo) < 2048:
        trozo = conn.recv(512)
        if not trozo:
            break
        cuerpo += trozo
    return metodo, ruta, cuerpo.decode()


def _parsear_formulario(cuerpo):
    campos = {}
    for par in cuerpo.split("&"):
        if "=" in par:
            clave, valor = par.split("=", 1)
            campos[clave] = _urldecode(valor)
    return campos


def portal(datos, tick=None, mostrar=None, duracion_s=120):
    """Abre la red SmartClass-Setup y una pagina para cambiar la red Wi-Fi y el servidor."""
    try:
        network.WLAN(network.STA_IF).active(False)
    except Exception:
        pass
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_NOMBRE, password=AP_CLAVE,
              authmode=getattr(network, "AUTH_WPA_WPA2_PSK", 3))
    ip = ap.ifconfig()[0]
    print("Red de configuracion:", AP_NOMBRE, "clave", AP_CLAVE, "- abre http://" + ip)
    if mostrar:
        mostrar(["Red de ajuste:", AP_NOMBRE, "Clave:", AP_CLAVE, ip])

    servidor = socket.socket()
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", 80))
    servidor.listen(2)
    servidor.settimeout(1)
    t0 = time.ticks_ms()
    try:
        while time.ticks_diff(time.ticks_ms(), t0) < duracion_s * 1000:
            if tick:
                tick()
            try:
                conn, _ = servidor.accept()
            except OSError:
                continue
            guardado = False
            try:
                conn.settimeout(3)
                metodo, ruta, cuerpo = _leer(conn)
                if metodo == "POST" and ruta == "/guardar":
                    campos = _parsear_formulario(cuerpo)
                    ssid = campos.get("ssid", "").strip()
                    clave = campos.get("password", "")
                    if ssid:
                        if not clave and ssid == datos.get("ssid"):
                            clave = datos.get("password", "")
                        guardar(ssid, clave, campos.get("broker", "").strip())
                        _responder(conn, PAGINA_OK)
                        guardado = True
                    else:
                        _responder(conn, PAGINA % (_esc(datos.get("ssid", "")),
                                                   _esc(datos.get("broker", ""))))
                else:
                    _responder(conn, PAGINA % (_esc(datos.get("ssid", "")),
                                               _esc(datos.get("broker", ""))))
            except Exception as e:
                print("Portal: error", e)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            if guardado:
                time.sleep(1)
                machine.reset()
    finally:
        servidor.close()
        ap.active(False)
