# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   red.py
# Objetivo:  Conectar la ESP32 al WiFi y al broker MQTT para publicar
#            sensores/eventos y recibir comandos FIRMADOS
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Topicos (los "canales" de MQTT) que usa BikeSafe:
#
#   ESP32 -> broker
#   bikesafe/estado              LIBRE / ASEGURADA / ALARMA (retenido)
#   bikesafe/conexion            online / offline (retenido; "offline"
#                                lo publica el broker solo si la ESP32
#                                se desconecta: "ultima voluntad")
#   bikesafe/sensores            todas las lecturas juntas en JSON
#   bikesafe/sensor/distancia    cm del HC-SR04
#   bikesafe/sensor/movimiento   cambio en g del MPU6050
#   bikesafe/sensor/inclinacion  grados del MPU6050
#   bikesafe/sensor/cerrojo      CERRADO / ABIERTO (reed switch)
#   bikesafe/sensor/lazo         ENTERO / CORTADO
#   bikesafe/alerta              texto de cada aviso o alarma
#   bikesafe/evento              JSON de cada cosa que pasa (historial)
#   bikesafe/camara              lo que contesta la placa de la camara
#
#   broker -> ESP32 (todos FIRMADOS, ver firma.py)
#   bikesafe/cmd                 asegurar / liberar / silenciar / foto / buscar
#   bikesafe/servo/cmd           cerrar / abrir
#   bikesafe/buzzer/cmd          pitido / sirena_off
#   bikesafe/led/cmd             alerta / normal / <color>
#   bikesafe/ia/resultado        lo que vio la IA: {"clase", "conf", ...}
#                                (la ESP32 DECIDE que hacer con eso)
#
# IMPORTANTE: si no hay WiFi o no hay broker, el candado sigue
# funcionando igual. La red es un extra, no una dependencia.

import time
import network

import firma

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None

T_ESTADO = b"bikesafe/estado"
T_CONEXION = b"bikesafe/conexion"
T_CMD = b"bikesafe/cmd"
T_CMD_ACTUADOR = b"bikesafe/+/cmd"   # servo, buzzer y led
T_IA = b"bikesafe/ia/resultado"

ARCHIVO_CONTADOR = "contador.txt"


class Red:
    def __init__(self, cfg):
        self._cfg = cfg
        self._wlan = network.WLAN(network.STA_IF)
        self._cliente = None
        self._entrada = []           # (tipo, texto) ya verificados
        self._clave = getattr(cfg, "MQTT_CLAVE", "")
        self._contador = self._leer_contador()
        self.rechazados = 0
        # Asi el primer intento de MQTT es en cuanto arranca
        self._intento_ms = time.ticks_add(time.ticks_ms(), -20000)

    # ---------- WiFi ----------
    def _reiniciar_wifi(self):
        """Evita el 'Wifi Internal State Error': apaga, prende y
        suelta cualquier conexion a medias antes de conectar."""
        try:
            self._wlan.disconnect()
        except Exception:
            pass
        self._wlan.active(False)
        time.sleep_ms(200)
        self._wlan.active(True)
        time.sleep_ms(200)

    def _ver_redes(self):
        """Imprime si la red configurada se ve (ayuda con el hotspot)."""
        try:
            redes = {}
            for r in self._wlan.scan():
                redes[r[0].decode()] = r[3]
            if self._cfg.WIFI_SSID in redes:
                print("WiFi: si veo", self._cfg.WIFI_SSID, "con senal",
                      redes[self._cfg.WIFI_SSID], "dBm")
            else:
                print("WiFi: NO veo", repr(self._cfg.WIFI_SSID))
                print("  Redes que si veo:", list(redes))
                print("  (iPhone: deja abierta la pantalla de Compartir"
                      " Internet y activa 'Maximizar compatibilidad')")
        except Exception:
            pass

    def _conectar(self):
        if self._cfg.WIFI_PASS:
            self._wlan.connect(self._cfg.WIFI_SSID, self._cfg.WIFI_PASS)
        else:                                   # red abierta
            self._wlan.connect(self._cfg.WIFI_SSID)

    def conectar_wifi(self, espera_s=15, intentos=3):
        self._wlan.active(True)
        if self._wlan.isconnected():
            print("WiFi OK, mi IP es", self._wlan.ifconfig()[0])
            return True
        for n in range(1, intentos + 1):
            self._reiniciar_wifi()
            if n == 1:
                self._ver_redes()
            print("WiFi: conectando a", self._cfg.WIFI_SSID,
                  "(intento", n, "de", intentos, ")")
            try:
                self._conectar()
            except OSError as e:
                print("WiFi: error al conectar:", e)
                continue
            limite = time.ticks_add(time.ticks_ms(), espera_s * 1000)
            while (not self._wlan.isconnected() and
                   time.ticks_diff(limite, time.ticks_ms()) > 0):
                time.sleep_ms(250)
            if self._wlan.isconnected():
                print("WiFi OK, mi IP es", self._wlan.ifconfig()[0])
                return True
        print("WiFi: no se pudo (sigo sin red). Revisa nombre y clave")
        return False

    # ---------- contador anti-repeticion ----------
    def _leer_contador(self):
        try:
            with open(ARCHIVO_CONTADOR) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def _guardar_contador(self, valor):
        self._contador = valor
        try:
            with open(ARCHIVO_CONTADOR, "w") as f:
                f.write(str(valor))
        except OSError:
            pass

    # ---------- MQTT ----------
    def _al_recibir(self, topico, mensaje):
        """Revisa la firma y guarda el mensaje como (tipo, texto).
        tipo = "cmd" (ordenes) o "ia" (resultado de la IA)."""
        try:
            texto = mensaje.decode().strip()
            if self._clave:
                valido, extra = firma.verificar(self._clave, texto,
                                                self._contador)
                if valido is None:
                    self.rechazados += 1
                    print("MQTT: rechazo mensaje en", topico, "->", extra)
                    return
                self._guardar_contador(extra)
                texto = valido
            if topico == T_IA:
                self._entrada.append(("ia", texto))
                return
            texto = texto.lower()
            if topico != T_CMD:
                partes = topico.decode().split("/")
                if len(partes) != 3 or partes[2] != "cmd":
                    return                 # no es un comando: lo ignoramos
                texto = partes[1] + ":" + texto      # "servo:cerrar"
            self._entrada.append(("cmd", texto))
        except Exception as e:
            print("MQTT: mensaje raro:", e)

    def _id_cliente(self):
        """En un broker publico dos aparatos con el mismo nombre se
        sacan uno al otro. Le agregamos el numero de serie del chip."""
        try:
            from machine import unique_id
            from binascii import hexlify
            return "{}-{}".format(self._cfg.MQTT_CLIENTE,
                                  hexlify(unique_id()).decode()[-6:])
        except Exception:
            return self._cfg.MQTT_CLIENTE

    def _conectar_mqtt(self):
        if MQTTClient is None:
            print("MQTT: este firmware no trae umqtt")
            return
        c = MQTTClient(self._id_cliente(), self._cfg.MQTT_BROKER,
                       port=self._cfg.MQTT_PUERTO, keepalive=30)
        # "Ultima voluntad": si la ESP32 se apaga o pierde el WiFi, el
        # broker publica "offline" por ella. Asi el dashboard sabe que
        # el candado se desconecto aunque ya no pueda avisar.
        c.set_last_will(T_CONEXION, b"offline", retain=True)
        c.set_callback(self._al_recibir)
        try:
            c.connect(timeout=5)       # versiones nuevas de umqtt
        except TypeError:
            c.connect()                # versiones viejas
        c.subscribe(T_CMD)
        c.subscribe(T_CMD_ACTUADOR)
        c.subscribe(T_IA)
        self._cliente = c
        self._ping_ms = time.ticks_ms()
        self.publicar(T_CONEXION, "online", True)
        print("MQTT OK en", self._cfg.MQTT_BROKER,
              "(mensajes firmados)" if self._clave else "(SIN firma)")

    def conectado(self):
        return self._cliente is not None

    def wifi_ok(self):
        return self._wlan.isconnected()

    def atender(self, ahora, puede_reconectar=True):
        """Llamar en cada vuelta: recibe mensajes y reconecta solo."""
        if self._cliente:
            try:
                self._cliente.check_msg()
                # Un "ping" cada 15 s para que el broker no nos corte
                if time.ticks_diff(ahora, self._ping_ms) > 15000:
                    self._ping_ms = ahora
                    self._cliente.ping()
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
                self._reiniciar_wifi()
                self._conectar()
        except Exception as e:
            print("Red: reintento fallido:", e)
            self._cliente = None

    def publicar(self, topico, texto, retener=False):
        if not self._cliente:
            return
        try:
            self._cliente.publish(topico, texto, retener)
        except OSError:
            self._cliente = None

    def siguiente(self):
        """Siguiente mensaje recibido: ("cmd", "liberar"),
        ("ia", '{"clase": "persona", ...}') o None."""
        return self._entrada.pop(0) if self._entrada else None
