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


def enviar_mensaje(token, chat_id, texto):
    """Manda un mensaje de texto. Regresa True si Telegram lo acepto."""
    cuerpo = "chat_id={}&text={}".format(chat_id, _para_url(texto)).encode()
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
