# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   red.py
# Objetivo:  Conectar la ESP32 al WiFi y al broker MQTT (Mosquitto)
#            para ver el estado y mandar comandos desde el celular
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Topicos (los "canales" de MQTT) que usa BikeSafe:
#
#   bikesafe/estado    -> LIBRE / ASEGURADA / ALARMA
#   bikesafe/sensores  -> {"dist": 83.2, "cambio": 0.02, "incl": 1.4}
#   bikesafe/alerta    -> texto de cada aviso o alarma
#   bikesafe/camara    -> lo que contesta la placa de la camara
#   bikesafe/cmd       <- asegurar / liberar / silenciar / foto / alerta_ia
#
#   Topicos de la Tabla HAL (uno por sensor y uno por actuador):
#   bikesafe/sensor/distancia    -> cm del HC-SR04
#   bikesafe/sensor/movimiento   -> cambio en g del MPU6050
#   bikesafe/sensor/inclinacion  -> grados del MPU6050
#   bikesafe/sensor/lazo         -> ENTERO / CORTADO
#   bikesafe/servo/cmd           <- cerrar / abrir
#   bikesafe/buzzer/cmd          <- pitido / sirena_off
#   bikesafe/led/cmd             <- alerta / normal
#
# IMPORTANTE: si no hay WiFi o no hay broker, el candado sigue
# funcionando igual. La red es un extra, no una dependencia.

import time
import network

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None

T_ESTADO = b"bikesafe/estado"
T_SENSORES = b"bikesafe/sensores"
T_ALERTA = b"bikesafe/alerta"
T_CAMARA = b"bikesafe/camara"
T_CMD = b"bikesafe/cmd"
T_CMD_ACTUADOR = b"bikesafe/+/cmd"   # servo, buzzer y led


class Red:
    def __init__(self, cfg):
        self._cfg = cfg
        self._wlan = network.WLAN(network.STA_IF)
        self._cliente = None
        self._comandos = []
        # Asi el primer intento de MQTT es en cuanto arranca
        self._intento_ms = time.ticks_add(time.ticks_ms(), -20000)

    # ---------- WiFi ----------
    def conectar_wifi(self, espera_s=12):
        self._wlan.active(True)
        if not self._wlan.isconnected():
            print("WiFi: conectando a", self._cfg.WIFI_SSID)
            self._wlan.connect(self._cfg.WIFI_SSID, self._cfg.WIFI_PASS)
            limite = time.ticks_add(time.ticks_ms(), espera_s * 1000)
            while (not self._wlan.isconnected() and
                   time.ticks_diff(limite, time.ticks_ms()) > 0):
                time.sleep_ms(250)
        if self._wlan.isconnected():
            print("WiFi OK, mi IP es", self._wlan.ifconfig()[0])
            return True
        print("WiFi: no se pudo (sigo sin red)")
        return False

    # ---------- MQTT ----------
    def _al_recibir(self, topico, mensaje):
        """Guarda el comando. Si llega por el topico de un actuador
        (bikesafe/servo/cmd) se guarda como "servo:cerrar"."""
        try:
            texto = mensaje.decode().strip().lower()
            if topico != T_CMD:
                partes = topico.decode().split("/")
                if len(partes) != 3 or partes[2] != "cmd":
                    return                 # no es un comando: lo ignoramos
                texto = partes[1] + ":" + texto
            self._comandos.append(texto)
        except Exception:
            pass

    def _conectar_mqtt(self):
        if MQTTClient is None:
            print("MQTT: este firmware no trae umqtt")
            return
        c = MQTTClient(self._cfg.MQTT_CLIENTE, self._cfg.MQTT_BROKER,
                       port=self._cfg.MQTT_PUERTO, keepalive=60)
        c.set_callback(self._al_recibir)
        try:
            c.connect(timeout=5)       # versiones nuevas de umqtt
        except TypeError:
            c.connect()                # versiones viejas
        c.subscribe(T_CMD)
        c.subscribe(T_CMD_ACTUADOR)
        self._cliente = c
        print("MQTT OK en", self._cfg.MQTT_BROKER)

    def conectado(self):
        return self._cliente is not None

    def atender(self, ahora, puede_reconectar=True):
        """Llamar en cada vuelta: recibe comandos y reconecta solo."""
        if self._cliente:
            try:
                self._cliente.check_msg()
            except OSError:
                print("MQTT: se cayo la conexion")
                self._cliente = None
            return
        if not puede_reconectar:
            return
        if time.ticks_diff(ahora, self._intento_ms) < 15000:
            return
        self._intento_ms = ahora
        try:
            if self._wlan.isconnected():
                self._conectar_mqtt()
            else:
                self._wlan.active(True)
                self._wlan.connect(self._cfg.WIFI_SSID, self._cfg.WIFI_PASS)
        except Exception as e:
            print("Red: reintento fallido:", e)

    def publicar(self, topico, texto, retener=False):
        if not self._cliente:
            return
        try:
            self._cliente.publish(topico, texto, retener)
        except OSError:
            self._cliente = None

    def siguiente_comando(self):
        return self._comandos.pop(0) if self._comandos else None
