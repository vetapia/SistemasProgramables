# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   telegram.py   (va en la FREENOVE)
# Objetivo:  Mandar mensajes y fotos al celular con un bot de
#            Telegram, usando solo lo que ya trae MicroPython
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Telegram tiene una "API": una direccion web a la que le mandas
# datos y el bot los publica en tu chat. Aqui armamos a mano esa
# peticion web (HTTPS) porque asi no hay que instalar nada.

import json
import socket

try:
    import ssl
except ImportError:            # firmwares viejos
    import ussl as ssl

SERVIDOR = "api.telegram.org"
LIMITE = "BikeSafe7d1f9c"      # separador de las partes del envio


def _conectar():
    direccion = socket.getaddrinfo(SERVIDOR, 443)[0][-1]
    s = socket.socket()
    s.settimeout(15)
    s.connect(direccion)
    try:
        return ssl.wrap_socket(s, server_hostname=SERVIDOR)
    except TypeError:          # firmwares muy viejos
        return ssl.wrap_socket(s)


def _salio_bien(s):
    """Lee el primer renglon de la respuesta: 'HTTP/1.1 200 OK'."""
    renglon = s.readline()
    return bool(renglon) and b" 200" in renglon


def _para_url(texto):
    """Cambia espacios y acentos por codigos %XX (asi lo pide la web)."""
    salida = ""
    for b in str(texto).encode():
        c = chr(b)
        if b < 128 and (c.isalpha() or c.isdigit() or c in "-_.~"):
            salida += c
        else:
            salida += "%{:02X}".format(b)
    return salida


# Botones que aparecen abajo del chat (el usuario solo los toca)
BOTONES = [["Cerrar", "Abrir"], ["Foto", "Estado"], ["Buscar", "Silenciar"]]
CONFIRMAR = [["Si, abrir", "No"]]


def enviar_mensaje(token, chat_id, texto, botones=False):
    """Manda un mensaje de texto. Regresa True si Telegram lo acepto.
    botones=True pone el teclado normal; botones="confirmar" pone
    el de "Si, abrir / No"."""
    cuerpo = "chat_id={}&text={}".format(chat_id, _para_url(texto))
    if botones:
        teclas = CONFIRMAR if botones == "confirmar" else BOTONES
        teclado = json.dumps({"keyboard": teclas, "resize_keyboard": True,
                              "is_persistent": True})
        cuerpo += "&reply_markup=" + _para_url(teclado)
    cuerpo = cuerpo.encode()
    cabecera = ("POST /bot{}/sendMessage HTTP/1.1\r\n"
                "Host: {}\r\n"
                "Content-Type: application/x-www-form-urlencoded\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n").format(token, SERVIDOR,
                                                    len(cuerpo)).encode()
    s = _conectar()
    try:
        s.write(cabecera)
        s.write(cuerpo)
        return _salio_bien(s)
    finally:
        s.close()


def enviar_foto(token, chat_id, jpg, pie=""):
    """Manda una foto JPEG con un texto abajo (pie de foto)."""
    inicio = ("--{0}\r\n"
              "Content-Disposition: form-data; name=\"chat_id\"\r\n\r\n"
              "{1}\r\n"
              "--{0}\r\n"
              "Content-Disposition: form-data; name=\"caption\"\r\n\r\n"
              "{2}\r\n"
              "--{0}\r\n"
              "Content-Disposition: form-data; name=\"photo\"; "
              "filename=\"bikesafe.jpg\"\r\n"
              "Content-Type: image/jpeg\r\n\r\n").format(LIMITE, chat_id,
                                                         pie).encode()
    fin = "\r\n--{}--\r\n".format(LIMITE).encode()
    total = len(inicio) + len(jpg) + len(fin)
    cabecera = ("POST /bot{}/sendPhoto HTTP/1.1\r\n"
                "Host: {}\r\n"
                "Content-Type: multipart/form-data; boundary={}\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n").format(token, SERVIDOR, LIMITE,
                                                    total).encode()
    s = _conectar()
    try:
        s.write(cabecera)
        s.write(inicio)
        vista = memoryview(jpg)
        # La foto se manda en pedazos de 1 KB para no llenar la memoria
        for i in range(0, len(jpg), 1024):
            s.write(vista[i:i + 1024])
        s.write(fin)
        return _salio_bien(s)
    finally:
        s.close()


def obtener_comandos(token, desde=0):
    """Pregunta a Telegram si hay mensajes nuevos para el bot.

    Regresa (lista, siguiente) donde lista son tuplas
    (chat_id, texto) y 'siguiente' es el numero que hay que mandar
    la proxima vez para no repetir mensajes viejos.
    """
    ruta = "/bot{}/getUpdates?timeout=0&limit=5&offset={}".format(token, desde)
    s = _conectar()
    try:
        # HTTP/1.0: Telegram contesta todo de una vez y cierra
        s.write("GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(
            ruta, SERVIDOR).encode())
        if not _salio_bien(s):
            return [], desde
        while True:                       # saltar las cabeceras
            renglon = s.readline()
            if not renglon or renglon == b"\r\n":
                break
        cuerpo = b""
        while True:
            pedazo = s.read(512)
            if not pedazo:
                break
            cuerpo += pedazo
    finally:
        s.close()
    datos = json.loads(cuerpo)
    lista = []
    siguiente = desde
    for u in datos.get("result", []):
        siguiente = u["update_id"] + 1
        m = u.get("message") or {}
        texto = m.get("text")
        if texto:
            lista.append((str(m["chat"]["id"]), texto.strip()))
    return lista, siguiente
