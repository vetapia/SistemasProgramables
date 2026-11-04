# ============================================
# Proyecto:  EcoClasifica
# Archivo:   red.py
# Objetivo:  Conexión WiFi y cliente MQTT (umqtt.simple) con reconexión automática y ping.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import network
import time
import ubinascii
import machine
from umqtt.simple import MQTTClient

from config import (
    WIFI_SSID, WIFI_PASS, MQTT_BROKER, MQTT_PUERTO, KEEPALIVE_S,
    TIMEOUT_WIFI_MS, INTERVALO_REINTENTO_RED_MS, INTERVALO_PING_MS,
)


class Red:
    def __init__(self, callback, topicos_suscripcion):
        self._callback = callback
        self._topicos = topicos_suscripcion
        self._wlan = network.WLAN(network.STA_IF)
        self._cliente = None
        self._mqtt_ok = False
        self._ultimo_intento = 0
        self._ultimo_ping = 0

    # ---------------- WiFi ----------------

    def conectar_wifi(self):
        """Solo se usa al arrancar (bloquea hasta TIMEOUT_WIFI_MS). Después la
        reconexión la hace actualizar() sin bloquear el loop principal."""
        self._wlan.active(True)
        if self._wlan.isconnected():
            return True
        self._wlan.connect(WIFI_SSID, WIFI_PASS)
        inicio = time.ticks_ms()
        while not self._wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), inicio) > TIMEOUT_WIFI_MS:
                return False
            time.sleep_ms(100)
        return True

    def ip(self):
        return self._wlan.ifconfig()[0]

    def wifi_conectado(self):
        return self._wlan.isconnected()

    def mqtt_conectado(self):
        return self._mqtt_ok

    # ---------------- MQTT ----------------

    def _cerrar(self):
        self._mqtt_ok = False
        try:
            self._cliente.sock.close()
        except Exception:
            pass
        self._cliente = None

    def _conectar_mqtt(self):
        try:
            cliente = MQTTClient(
                b'eco_' + ubinascii.hexlify(machine.unique_id()),
                MQTT_BROKER, port=MQTT_PUERTO, keepalive=KEEPALIVE_S)
            cliente.set_callback(self._callback)
            cliente.connect()
            for topico in self._topicos:
                cliente.subscribe(topico)
        except Exception as e:  # OSError (sin red/broker) o MQTTException
            print("MQTT: no se pudo conectar:", e)
            return
        self._cliente = cliente
        self._mqtt_ok = True
        self._ultimo_ping = time.ticks_ms()
        print("MQTT: conectado a", MQTT_BROKER)

    def actualizar(self):
        """Llamar UNA vez por vuelta del loop. Escucha comandos (check_msg no
        bloquea) y reconecta cada INTERVALO_REINTENTO_RED_MS si se cae algo."""
        ahora = time.ticks_ms()

        if not self._mqtt_ok:
            if time.ticks_diff(ahora, self._ultimo_intento) >= INTERVALO_REINTENTO_RED_MS:
                self._ultimo_intento = ahora
                if self._wlan.isconnected():
                    self._conectar_mqtt()
                else:
                    try:
                        self._wlan.connect(WIFI_SSID, WIFI_PASS)
                    except OSError:
                        pass
            return

        try:
            self._cliente.check_msg()
            if time.ticks_diff(ahora, self._ultimo_ping) >= INTERVALO_PING_MS:
                self._ultimo_ping = ahora
                self._cliente.ping()
        except Exception:
            print("MQTT: conexión perdida, se reintentará")
            self._cerrar()

    def publicar(self, topico, valor):
        """Publica 'valor' (se convierte a texto). Regresa True si se envió."""
        if not self._mqtt_ok:
            return False
        try:
            self._cliente.publish(topico, str(valor))
            return True
        except Exception:
            print("MQTT: falló la publicación, se reintentará la conexión")
            self._cerrar()
            return False
