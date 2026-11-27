# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   firma.py   (ESP32 normal; el servidor usa una copia igual)
# Objetivo:  Firmar y comprobar los mensajes MQTT con HMAC-SHA256 para
#            que nadie mas pueda abrir el candado desde el broker publico
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# PROBLEMA: broker.hivemq.com es publico. Cualquiera en internet que
# sepa el topico podria publicar "liberar" en bikesafe/cmd y abrir el
# candado.
#
# SOLUCION: el servidor y la ESP32 comparten una CLAVE secreta (que no
# viaja por la red). Cada mensaje va asi:
#
#     liberar|1795631062430|9f2c4b1a7e3d5c60
#     ------- ------------- ----------------
#     orden   contador      firma = HMAC-SHA256(clave, "liberar|1795...")
#
#   - Sin la clave no se puede calcular la firma -> mensaje rechazado.
#   - El contador siempre crece: si alguien graba un mensaje viejo y lo
#     vuelve a mandar (ataque de repeticion), se rechaza.
#
# Este archivo funciona igual en MicroPython y en Python normal.

import hashlib

try:
    from binascii import hexlify
except ImportError:                      # por si acaso
    from ubinascii import hexlify

_BLOQUE = 64                             # tamano de bloque de SHA-256


def _a_bytes(x):
    return x if isinstance(x, bytes) else str(x).encode()


def hmac_sha256(clave, mensaje):
    """HMAC-SHA256 (RFC 2104) escrito a mano, porque MicroPython no
    trae el modulo hmac. Regresa los 32 bytes de la firma."""
    clave = _a_bytes(clave)
    if len(clave) > _BLOQUE:
        clave = hashlib.sha256(clave).digest()
    clave = clave + b"\x00" * (_BLOQUE - len(clave))
    interna = bytes(b ^ 0x36 for b in clave)
    externa = bytes(b ^ 0x5C for b in clave)
    paso1 = hashlib.sha256(interna + _a_bytes(mensaje)).digest()
    return hashlib.sha256(externa + paso1).digest()


def firma_corta(clave, texto):
    """Primeros 8 bytes de la firma en hexadecimal (16 letras)."""
    return hexlify(hmac_sha256(clave, texto)[:8]).decode()


def firmar(clave, texto, contador):
    """'liberar' -> 'liberar|contador|firma'."""
    base = "{}|{}".format(texto, contador)
    return "{}|{}".format(base, firma_corta(clave, base))


def _iguales(a, b):
    """Compara sin cortar al primer caracter distinto (asi no se puede
    adivinar la firma midiendo cuanto tarda la comparacion)."""
    if len(a) != len(b):
        return False
    dif = 0
    for x, y in zip(a, b):
        dif |= ord(x) ^ ord(y)
    return dif == 0


def verificar(clave, mensaje, ultimo_contador):
    """Revisa un mensaje firmado.

    Regresa (texto, contador) si es valido, o (None, motivo) si no.
    """
    partes = mensaje.rsplit("|", 2)
    if len(partes) != 3:
        return None, "sin firma"
    texto, contador, firma = partes
    try:
        contador = int(contador)
    except ValueError:
        return None, "contador invalido"
    if not _iguales(firma, firma_corta(clave, texto + "|" + str(contador))):
        return None, "firma incorrecta"
    if contador <= ultimo_contador:
        return None, "mensaje repetido (contador viejo)"
    return texto, contador
