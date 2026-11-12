"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   mqtt_client.py
 Objetivo:  Abrir el socket TCP hacia Mosquitto, autenticar el cliente, publicar JSON, suscribirse a tópicos
             y ejecutar el callback al recibir PUBLISH QoS 0.
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 | 
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import socket

def _utf8(value):
    if isinstance(value, str):
        value = value.encode()
    return bytes((len(value) >> 8, len(value) & 0xFF)) + value


def _remaining_length(length):
    out = bytearray()
    while True:
        digit = length % 128
        length //= 128
        if length:
            digit |= 0x80
        out.append(digit)
        if not length:
            return bytes(out)


class MQTTClient:
    def __init__(self, client_id, server, port=1883, user=None, password=None,
                 keepalive=30, callback=None):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.callback = callback
        self.sock = None
        self.packet_id = 0

    def _sendall(self, data):
        view = memoryview(data)
        while len(view):
            sent = self.sock.send(view)
            if sent is None or sent <= 0:
                raise OSError("No se pudo enviar paquete MQTT")
            view = view[sent:]

    def _recv_exact(self, count):
        result = bytearray()
        while len(result) < count:
            part = self.sock.recv(count - len(result))
            if not part:
                raise OSError("Broker MQTT cerró la conexión")
            result.extend(part)
        return bytes(result)

    def _recv_remaining_length(self):
        multiplier = 1
        value = 0
        while True:
            digit = self._recv_exact(1)[0]
            value += (digit & 127) * multiplier
            if not (digit & 128):
                return value
            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise OSError("Longitud MQTT inválida")

    def connect(self):
        self.sock = socket.socket()
        self.sock.settimeout(5)
        self.sock.connect((self.server, self.port))
        flags = 0x02  # clean session
        if self.user:
            flags |= 0x80
        if self.password:
            flags |= 0x40
        variable = _utf8(b"MQTT") + bytes((4, flags)) + bytes((self.keepalive >> 8, self.keepalive & 255))
        payload = _utf8(self.client_id)
        if self.user:
            payload += _utf8(self.user)
        if self.password:
            payload += _utf8(self.password)
        packet = b"\x10" + _remaining_length(len(variable) + len(payload)) + variable + payload
        self._sendall(packet)
        first = self._recv_exact(1)
        length = self._recv_remaining_length()
        response = self._recv_exact(length)
        if (first[0] >> 4) != 2 or len(response) < 2 or response[1] != 0:
            raise OSError("Mosquitto rechazó la conexión MQTT: %s" % (response,))
        self.sock.settimeout(0)
        return True

    def publish(self, topic, message, retain=False):
        if self.sock is None:
            raise OSError("MQTT desconectado")
        if not isinstance(message, bytes):
            message = str(message).encode()
        body = _utf8(topic) + message
        header = 0x31 if retain else 0x30
        self.sock.settimeout(2)
        try:
            self._sendall(bytes((header,)) + _remaining_length(len(body)) + body)
        finally:
            self.sock.settimeout(0)

    def subscribe(self, topic):
        self.packet_id = (self.packet_id % 65535) + 1
        body = bytes((self.packet_id >> 8, self.packet_id & 255)) + _utf8(topic) + b"\x00"
        self.sock.settimeout(2)
        try:
            self._sendall(b"\x82" + _remaining_length(len(body)) + body)
        finally:
            self.sock.settimeout(0)

    def ping(self):
        if self.sock:
            self.sock.settimeout(2)
            try:
                self._sendall(b"\xC0\x00")
            finally:
                self.sock.settimeout(0)

    def check_msg(self):
        if self.sock is None:
            return
        try:
            self.sock.settimeout(0)
            first = self.sock.recv(1)
            if not first:
                raise OSError("Conexión MQTT cerrada")
        except OSError as exc:
            #EAGAIN/timeout significa que no hay mensaje pendiente.
            msg = str(exc).lower()
            if ("timed out" in msg or "timeout" in msg or "eagain" in msg or "would block" in msg
                    or getattr(exc, "errno", None) in (11, 35, 10035)):
                return
            raise
        try:
            self.sock.settimeout(2)
            remaining = self._recv_remaining_length()
            body = self._recv_exact(remaining) if remaining else b""
        finally:
            self.sock.settimeout(0)
        packet_type = first[0] >> 4
        if packet_type == 3 and len(body) >= 2:
            topic_len = (body[0] << 8) | body[1]
            topic = body[2:2 + topic_len].decode()
            payload = body[2 + topic_len:]
            if self.callback:
                self.callback(topic, payload)
        #PINGRESP, SUBACK y paquetes de control QoS 0 se ignoran.

    def disconnect(self):
        if self.sock:
            try:
                self.sock.settimeout(1)
                self._sendall(b"\xE0\x00")
                self.sock.close()
            except Exception:
                pass
            self.sock = None
