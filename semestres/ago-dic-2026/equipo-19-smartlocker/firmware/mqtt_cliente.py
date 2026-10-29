# ============================================================
# mqtt_cliente.py - Multi-Wi-Fi + cliente MQTT con reintentos
# Requiere WIFI_REDES y datos MQTT en configuracion.py
# ============================================================

import network
import machine
import ubinascii
from time import sleep, ticks_ms, ticks_diff
from umqtt.simple import MQTTClient
import configuracion


class MqttCliente:
    def __init__(self, callback_cmd=None):
        self.client = None
        self.callback_cmd = callback_cmd
        self.ultimo_intento = ticks_ms()

    def conectar_wifi(self):
        sta = network.WLAN(network.STA_IF)
        sta.active(True)

        if sta.isconnected():
            print("Wi-Fi ya conectado. IP:", sta.ifconfig()[0])
            return True

        for ssid, password in configuracion.WIFI_REDES:
            if not ssid or ssid.startswith("NOMBRE_WIFI_"):
                continue
            if password is None:
                password = ""
            if password.startswith("CONTRASENA_WIFI_") or password == "CONTRASENA_HOTSPOT":
                continue

            print("Intentando conectar a Wi-Fi:", ssid)
            try:
                sta.disconnect()
            except Exception:
                pass

            try:
                sta.connect(ssid, password)
            except Exception as e:
                print("No se pudo iniciar la conexión a", ssid, ":", e)
                continue

            inicio = ticks_ms()
            while not sta.isconnected():
                if ticks_diff(ticks_ms(), inicio) >= configuracion.TIEMPO_ESPERA_WIFI_S * 1000:
                    print("Tiempo agotado para la red:", ssid)
                    break
                sleep(0.25)

            if sta.isconnected():
                print("Wi-Fi conectado. IP:", sta.ifconfig()[0])
                return True

        raise OSError("No se pudo conectar a ninguna red Wi-Fi configurada.")

    def _on_message(self, topic, msg):
        t = topic.decode() if isinstance(topic, bytes) else str(topic)
        m = msg.decode() if isinstance(msg, bytes) else str(msg)
        print("MQTT:", t, m)

        if t.endswith("/cmd") and self.callback_cmd:
            self.callback_cmd(m.strip())

    def conectar(self):
        # Marca el intento para que los reintentos no se ejecuten continuamente.
        self.ultimo_intento = ticks_ms()
        try:
            self.conectar_wifi()

            cid = b"smartlocker-" + ubinascii.hexlify(machine.unique_id())
            cliente = MQTTClient(
                cid,
                configuracion.BROKER,
                port=configuracion.PUERTO,
                keepalive=60
            )
            cliente.set_callback(self._on_message)
            cliente.connect()
            cliente.subscribe(configuracion.TOPIC_CMD)

            self.client = cliente
            self.ultimo_intento = ticks_ms()
            print("MQTT conectado a", configuracion.BROKER, "puerto", configuracion.PUERTO)
            print("Suscrito a:", configuracion.TOPIC_CMD)
            return True
        except Exception:
            self.client = None
            self.ultimo_intento = ticks_ms()
            raise

    def publicar(self, topic, valor):
        if self.client is None:
            return

        try:
            if not isinstance(topic, bytes):
                topic = str(topic).encode()
            if not isinstance(valor, bytes):
                valor = str(valor).encode()
            self.client.publish(topic, valor)
        except Exception as e:
            print("Error al publicar; MQTT se reintentará:", e)
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = None
            self.ultimo_intento = ticks_ms()

    def check(self):
        if self.client is not None:
            try:
                self.client.check_msg()
                return
            except Exception as e:
                print("Conexión MQTT perdida:", e)
                try:
                    self.client.disconnect()
                except Exception:
                    pass
                self.client = None
                self.ultimo_intento = ticks_ms()
                return

        if ticks_diff(ticks_ms(), self.ultimo_intento) >= configuracion.INTERVALO_REINTENTO_MQTT_MS:
            try:
                self.conectar()
            except Exception as e:
                print("No se pudo reconectar a MQTT:", e)

