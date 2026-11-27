# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   main.py   (va en la FREENOVE ESP32-WROVER con camara)
# Objetivo:  Esperar ordenes de la ESP32 normal por el cable serie;
#            cuando llega "FOTO" toma la foto, la guarda y la manda
#            al celular por Telegram
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Esta placa es "el fotografo". No decide nada: solo obedece.
#
#   Llega por el cable:            Lo que hace:
#   FOTO|ROBO|Forcejeo continuo -> foto + Telegram con ese texto
#   MSG|BikeSafe: bici ASEGURADA -> solo manda el texto
#
#   Ademas revisa el chat del bot cada pocos segundos. El dueno toca
#   los botones Cerrar, Abrir, Silenciar o Estado (o los escribe, con
#   o sin "/"), y se lo pasa a la ESP32 normal como "CMD|asegurar"
#   (ella es la que decide). "Foto" la resuelve la Freenove sola.
#
#   Y contesta:  OK|FOTO|telegram   /  OK|FOTO|guardada  /  ERR|...
#
# Ademas, cada foto se publica por MQTT para el servidor de IA:
#   bikesafe/cam/info   -> {"nivel": "ROBO", "motivo": "...", "n": 7}
#   bikesafe/cam/frame  -> la foto en JPEG (bytes)
# El servidor NO le contesta a esta placa: le manda el resultado de la
# IA a la ESP32 normal, que es la que decide si es para alarmarse.
#
# Seguridad del bot: solo obedece al TELEGRAM_CHAT_ID del dueno. Si un
# extrano le escribe, lo ignora y le avisa al dueno.
#
# NECESITA un firmware de MicroPython QUE INCLUYA CAMARA (el normal
# no la trae). La guia explica cual instalar. Este programa funciona
# con los dos firmwares mas comunes y detecta solo cual tienes.

import gc
import sys
import json
import time
import socket
import network
from machine import Pin, UART

import config as cfg
import telegram

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None

# Pines de la camara en la Freenove ESP32-WROVER (vienen soldados
# en la placa, no se pueden cambiar)
CAM_DATOS = [4, 5, 18, 19, 36, 39, 34, 35]    # D0..D7
CAM_VSYNC = 25
CAM_HREF = 23
CAM_PCLK = 22
CAM_XCLK = 21
CAM_SDA = 26
CAM_SCL = 27


# Emojis para que las alertas se distingan rapido en el celular
EMOJI = {"ROBO": "\U0001F6A8", "AVISO": "\u26A0\uFE0F",
         "PRESENCIA": "\U0001F440", "FOTO": "\U0001F4F7",
         "MANUAL": "\U0001F4F7", "PRUEBA": "\U0001F9EA"}


# ---------------------------------------------------------------
#  CAMARA
# ---------------------------------------------------------------
class Camara:
    """Envuelve los dos firmwares con camara para usarlos igual."""

    def __init__(self):
        self._nueva = None        # objeto Camera (firmware nuevo)
        self._codificador = None  # convierte a JPEG si la camara no puede
        self._vieja = None        # modulo camera (firmware lemariva)
        try:
            from camera import Camera     # firmware "micropython-camera-API"
            self._iniciar_nueva()
            print("Camara OK (firmware nuevo)")
        except ImportError:
            import camera                 # firmware de lemariva / Freenove
            self._iniciar_vieja(camera)
            print("Camara OK (firmware lemariva)")

    def _iniciar_nueva(self):
        from camera import Camera, FrameSize, PixelFormat, GrabMode
        pines = dict(
            data_pins=CAM_DATOS, vsync_pin=CAM_VSYNC, href_pin=CAM_HREF,
            sda_pin=CAM_SDA, scl_pin=CAM_SCL, pclk_pin=CAM_PCLK,
            xclk_pin=CAM_XCLK, xclk_freq=10000000,
            powerdown_pin=-1, reset_pin=-1, fb_count=1,
            grab_mode=GrabMode.WHEN_EMPTY)
        try:
            # Camaras que SI hacen JPEG solas (OV2640, OV3660...)
            tamano = getattr(FrameSize, cfg.TAMANO_FOTO, FrameSize.VGA)
            self._nueva = Camera(pixel_format=PixelFormat.JPEG,
                                 frame_size=tamano, jpeg_quality=85, **pines)
        except OSError:
            # Camaras que NO hacen JPEG (como la GC0308 de su Freenove):
            # tomamos la foto "cruda" y la convertimos con el modulo jpeg.
            import jpeg
            color = getattr(cfg, "FOTO_A_COLOR", True)
            self._nueva = Camera(
                pixel_format=PixelFormat.RGB565 if color else PixelFormat.GRAYSCALE,
                frame_size=FrameSize.QVGA, **pines)
            self._codificador = jpeg.Encoder(
                width=320, height=240, quality=80,
                pixel_format="RGB565_BE" if color else "GRAY")
            print("Camara sin JPEG propio: convierto con el modulo jpeg (320x240)")
        try:
            self._nueva.vflip = cfg.VOLTEAR_VERTICAL
            self._nueva.hmirror = cfg.ESPEJO
        except Exception:
            pass

    def _iniciar_vieja(self, camera):
        try:
            camera.deinit()               # por si quedo prendida
        except Exception:
            pass
        tamano = getattr(camera, "FRAME_" + cfg.TAMANO_FOTO, camera.FRAME_VGA)
        ajustes = dict(
            d0=4, d1=5, d2=18, d3=19, d4=36, d5=39, d6=34, d7=35,
            format=camera.JPEG, framesize=tamano,
            xclk_freq=camera.XCLK_10MHz,
            href=CAM_HREF, vsync=CAM_VSYNC, reset=-1, pwdn=-1,
            sioc=CAM_SCL, siod=CAM_SDA, xclk=CAM_XCLK, pclk=CAM_PCLK)
        try:
            listo = camera.init(0, fb_location=camera.PSRAM, **ajustes)
        except (TypeError, AttributeError):
            listo = camera.init(0, **ajustes)   # version sin fb_location
        if listo is False:
            raise OSError("camera.init fallo: revisa el cable plano")
        camera.quality(12)                # 10 = mejor, 63 = peor
        camera.flip(1 if cfg.VOLTEAR_VERTICAL else 0)
        camera.mirror(1 if cfg.ESPEJO else 0)
        self._vieja = camera

    def foto(self):
        """Regresa la foto como bytes JPEG, o None si fallo."""
        gc.collect()
        imagen = None
        # La primera foto suele salir oscura o vieja: tomamos 2 y
        # nos quedamos con la segunda.
        for _ in range(2):
            if self._nueva:
                imagen = self._nueva.capture()
            else:
                imagen = self._vieja.capture()
            time.sleep_ms(120)
        if not imagen:
            return None
        if self._codificador:
            return bytes(self._codificador.encode(imagen))
        return bytes(imagen)              # copia segura de la foto


# ---------------------------------------------------------------
#  PROGRAMA
# ---------------------------------------------------------------
class Fotografo:
    def __init__(self):
        print("\n=== BikeSafe camara arrancando ===")
        self.led = Pin(cfg.PIN_LED, Pin.OUT, value=0)
        self.uart = UART(1, baudrate=9600, rx=cfg.PIN_RX, tx=cfg.PIN_TX,
                         timeout=0)
        self._pendiente = b""
        self._numero = 0
        self._wifi_intento_ms = 0
        self.wlan = network.WLAN(network.STA_IF)
        self.camara = Camara()
        self.servidor = None
        self.conectar_wifi()
        if cfg.USAR_WEB:
            self._abrir_web()
        self._bot_desde = 0
        self._confirmar_hasta = None   # esperando "Si, abrir"
        self._intrusos = []            # chats ajenos que ya se reportaron
        self._pendientes = []          # alertas que no salieron por falta de internet
        self._reintento_ms = 0
        self._sin_internet = False
        self._wdt = None
        self._bot_ultima_ms = time.ticks_ms()
        self._bot_listo = False
        self.mqtt = None
        self._ping_ms = time.ticks_ms()
        self._mqtt_intento_ms = time.ticks_add(time.ticks_ms(), -60000)
        self.responder("OK|LISTA")
        print("=== Lista. Esperando ordenes ===\n")

    # ---------- WiFi ----------
    def _reiniciar_wifi(self):
        """Suelta conexiones a medias (evita 'Wifi Internal State Error')."""
        try:
            self.wlan.disconnect()
        except Exception:
            pass
        self.wlan.active(False)
        time.sleep_ms(200)
        self.wlan.active(True)
        time.sleep_ms(200)

    def _conectar(self):
        if cfg.WIFI_PASS:
            self.wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
        else:                                   # red abierta
            self.wlan.connect(cfg.WIFI_SSID)

    def conectar_wifi(self, espera_s=15, intentos=3):
        self.wlan.active(True)
        for n in range(1, intentos + 1):
            if self.wlan.isconnected():
                break
            self._reiniciar_wifi()
            if n == 1:
                try:
                    redes = {}
                    for r in self.wlan.scan():
                        redes[r[0].decode()] = r[3]
                    if cfg.WIFI_SSID in redes:
                        print("WiFi: si veo", cfg.WIFI_SSID, "con senal",
                              redes[cfg.WIFI_SSID], "dBm")
                    else:
                        print("WiFi: NO veo", repr(cfg.WIFI_SSID))
                        print("  Redes que si veo:", list(redes))
                except Exception:
                    pass
            print("WiFi: conectando a", cfg.WIFI_SSID,
                  "(intento", n, "de", intentos, ")")
            try:
                self._conectar()
            except OSError as e:
                print("WiFi: error al conectar:", e)
                continue
            limite = time.ticks_add(time.ticks_ms(), espera_s * 1000)
            while (not self.wlan.isconnected() and
                   time.ticks_diff(limite, time.ticks_ms()) > 0):
                time.sleep_ms(250)
        if self.wlan.isconnected():
            print("WiFi OK. Para ver la camara abre  http://{}".format(
                self.wlan.ifconfig()[0]))
            return True
        print("WiFi: sin conexion (las fotos se guardan en la placa)")
        return False

    def _revisar_wifi(self, ahora):
        if self.wlan.isconnected():
            if self._sin_internet:
                self._sin_internet = False
                print("WiFi: volvio la conexion")
            return
        if not self._sin_internet:
            self._sin_internet = True
            self.mqtt = None
            print("WiFi: se perdio la conexion, guardo las alertas")
        if time.ticks_diff(ahora, self._wifi_intento_ms) > 20000:
            self._wifi_intento_ms = ahora
            try:
                self._reiniciar_wifi()
                self._conectar()
            except Exception:
                pass

    # ---------- enlace serie ----------
    def responder(self, texto):
        self.uart.write(texto + "\n")

    def _leer_orden(self):
        dato = self.uart.read()
        if dato:
            self._pendiente += dato
            if len(self._pendiente) > 400:
                self._pendiente = b""
        if b"\n" in self._pendiente:
            renglon, self._pendiente = self._pendiente.split(b"\n", 1)
            try:
                return renglon.decode().strip()
            except Exception:
                return None
        return None

    # ---------- fotos ----------
    def _guardar(self, jpg):
        """Guarda la foto en la memoria de la placa. Solo conserva
        las ultimas FOTOS_GUARDADAS (va encimando las mas viejas)."""
        nombre = "foto_{}.jpg".format(self._numero % cfg.FOTOS_GUARDADAS)
        self._numero += 1
        try:
            with open(nombre, "wb") as f:
                f.write(jpg)
            return nombre
        except OSError as e:
            print("No pude guardar la foto:", e)
            return None

    # ---------- MQTT (para el servidor de IA) ----------
    def _id_cliente(self):
        """Nombre unico en el broker publico (numero de serie del chip)."""
        try:
            from machine import unique_id
            from binascii import hexlify
            return "{}-{}".format(cfg.MQTT_CLIENTE,
                                  hexlify(unique_id()).decode()[-6:])
        except Exception:
            return cfg.MQTT_CLIENTE

    def _conectar_mqtt(self, ya=False):
        """ya=True: intenta aunque haya fallado hace poco."""
        if not getattr(cfg, "USAR_MQTT", False) or MQTTClient is None:
            return False
        if self.mqtt:
            return True
        ahora = time.ticks_ms()
        if not self.wlan.isconnected():
            return False
        if not ya and time.ticks_diff(ahora, self._mqtt_intento_ms) < 15000:
            return False
        self._mqtt_intento_ms = ahora
        try:
            c = MQTTClient(self._id_cliente(), cfg.MQTT_BROKER,
                           port=cfg.MQTT_PUERTO, keepalive=60)
            c.connect()
            self.mqtt = c
            self._ping_ms = ahora
            print("MQTT OK en", cfg.MQTT_BROKER)
            return True
        except Exception as e:
            print("MQTT: no se pudo conectar:", e)
            self.mqtt = None
            return False

    def _mantener_mqtt(self, ahora):
        """Ping cada 30 s: sin esto el broker corta la conexion por
        inactividad y la siguiente foto se perderia."""
        if self.mqtt and time.ticks_diff(ahora, self._ping_ms) > 30000:
            self._ping_ms = ahora
            try:
                self.mqtt.ping()
                self.mqtt.check_msg()      # leer la respuesta del ping
            except Exception:
                print("MQTT: se cayo, reconecto en la siguiente foto")
                self.mqtt = None

    def publicar_frame(self, jpg, nivel, motivo):
        """Manda la foto al servidor Python (IA) por MQTT. Si la
        conexion estaba caida, reconecta y lo intenta una vez mas."""
        info = json.dumps({"nivel": nivel, "motivo": motivo,
                           "n": self._numero})
        for intento in (1, 2):
            if not self._conectar_mqtt(ya=(intento == 2)):
                return False
            try:
                self.mqtt.publish(b"bikesafe/cam/info", info)
                self.mqtt.publish(b"bikesafe/cam/frame", jpg)
                print("Foto publicada por MQTT:", len(jpg), "bytes")
                return True
            except Exception as e:
                print("MQTT: fallo al publicar ({}): {}".format(intento, e))
                self.mqtt = None
        return False

    def tomar_y_enviar(self, nivel, motivo):
        self.led.value(1)
        jpg = self.camara.foto()
        self.led.value(0)
        pie = "{} BikeSafe {}: {}".format(EMOJI.get(nivel, ""), nivel,
                                          motivo).strip()
        if jpg is None:
            # Sin foto, por lo menos que llegue el aviso en texto
            self.responder("ERR|FOTO|la camara no entrego imagen")
            self.enviar_texto(pie + " (sin foto)")
            return
        print("Foto tomada: {} bytes ({})".format(len(jpg), nivel))
        nombre = self._guardar(jpg)
        self.publicar_frame(jpg, nivel, motivo)
        if cfg.USAR_TELEGRAM and self.wlan.isconnected():
            try:
                if telegram.enviar_foto(cfg.TELEGRAM_TOKEN,
                                        cfg.TELEGRAM_CHAT_ID, jpg, pie):
                    self.responder("OK|FOTO|telegram")
                    return
                self.responder("ERR|FOTO|Telegram la rechazo (token/chat)")
                return
            except Exception as e:
                sys.print_exception(e)
                self.responder("ERR|FOTO|sin internet")
        if cfg.USAR_TELEGRAM and nombre:
            self._guardar_pendiente(nombre, pie)
        self.responder("OK|FOTO|guardada como {}".format(nombre))

    def enviar_texto(self, texto, botones=False):
        if not cfg.USAR_TELEGRAM:
            self.responder("OK|MSG|no enviado (Telegram apagado)")
            return
        if not self.wlan.isconnected():
            self._guardar_pendiente(None, texto)
            self.responder("OK|MSG|guardado hasta que vuelva el internet")
            return
        try:
            bien = telegram.enviar_mensaje(cfg.TELEGRAM_TOKEN,
                                           cfg.TELEGRAM_CHAT_ID, texto,
                                           botones)
            self.responder("OK|MSG|telegram" if bien
                           else "ERR|MSG|Telegram lo rechazo")
        except Exception as e:
            sys.print_exception(e)
            self._guardar_pendiente(None, texto)
            self.responder("ERR|MSG|sin internet")

    # ---------- alertas guardadas cuando no hay internet ----------
    def _guardar_pendiente(self, archivo, texto):
        self._pendientes.append((archivo, texto))
        # Las fotos se van encimando, asi que no guardamos mas que esas
        if len(self._pendientes) > cfg.FOTOS_GUARDADAS:
            self._pendientes = self._pendientes[-cfg.FOTOS_GUARDADAS:]

    def _reenviar_pendientes(self, ahora):
        if not self._pendientes or not self.wlan.isconnected():
            return
        if time.ticks_diff(ahora, self._reintento_ms) < 15000:
            return
        self._reintento_ms = ahora
        total = len(self._pendientes)
        try:
            telegram.enviar_mensaje(
                cfg.TELEGRAM_TOKEN, cfg.TELEGRAM_CHAT_ID,
                "Volvio el internet. Te mando {} alerta(s) guardada(s):".format(total))
            while self._pendientes:
                archivo, texto = self._pendientes[0]
                if archivo:
                    with open(archivo, "rb") as f:
                        jpg = f.read()
                    telegram.enviar_foto(cfg.TELEGRAM_TOKEN,
                                         cfg.TELEGRAM_CHAT_ID, jpg, texto)
                else:
                    telegram.enviar_mensaje(cfg.TELEGRAM_TOKEN,
                                            cfg.TELEGRAM_CHAT_ID, texto)
                self._pendientes.pop(0)
                gc.collect()
        except Exception as e:
            print("Pendientes: aun no se pudieron mandar:", e)

    def atender_orden(self, renglon):
        print("Orden:", renglon)
        partes = renglon.split("|")
        if partes[0] == "FOTO":
            nivel = partes[1] if len(partes) > 1 else "AVISO"
            motivo = partes[2] if len(partes) > 2 else ""
            self.tomar_y_enviar(nivel, motivo)
        elif partes[0] == "MSG":
            texto = partes[1] if len(partes) > 1 else ""
            self.enviar_texto(texto.replace("~", "\n"))
        else:
            self.responder("ERR|no entiendo")

    # ---------- comandos del bot de Telegram ----------
    AYUDA = ("BikeSafe - usa los botones de abajo:\n"
             "Cerrar - asegura la bici\n"
             "Abrir - libera la bici (pide confirmar)\n"
             "Foto - foto de la bici ahora\n"
             "Estado - como esta el candado\n"
             "Buscar - suena para encontrar tu bici\n"
             "Silenciar - calla la alarma (sigue asegurada)")

    # Palabras que entiende (con o sin "/", mayusculas o minusculas)
    PASAR_A_ESP32 = {"cerrar": "asegurar", "asegurar": "asegurar",
                     "silenciar": "silenciar", "callar": "silenciar",
                     "estado": "estado", "buscar": "buscar"}

    @staticmethod
    def _limpiar_comando(texto):
        """'/Cerrar@BikeSafe_bot' o 'cerrar ya' -> 'cerrar'."""
        palabra = texto.strip().split()[0] if texto.strip() else ""
        palabra = palabra.split("@")[0].lstrip("/").lower()
        for a, b in (("\u00e1", "a"), ("\u00e9", "e"), ("\u00ed", "i"),
                     ("\u00f3", "o"), ("\u00fa", "u")):
            palabra = palabra.replace(a, b)
        return "".join(c for c in palabra if c.isalpha())   # "si," -> "si"

    def _revisar_bot(self, ahora):
        if not (cfg.USAR_TELEGRAM and self.wlan.isconnected()):
            return
        cada = getattr(cfg, "REVISAR_BOT_CADA_S", 3) * 1000
        if time.ticks_diff(ahora, self._bot_ultima_ms) < cada:
            return
        self._bot_ultima_ms = ahora
        gc.collect()
        try:
            if not self._bot_listo:
                # Al arrancar ignoramos los mensajes viejos del chat
                _, self._bot_desde = telegram.obtener_comandos(
                    cfg.TELEGRAM_TOKEN, -1)
                self._bot_listo = True
                print("Bot listo: esperando comandos de Telegram")
                # Avisar que ya prendio y dejar los botones en el chat
                self.enviar_texto("BikeSafe encendido. Usa los botones de abajo.",
                                  botones=True)
                return
            comandos, self._bot_desde = telegram.obtener_comandos(
                cfg.TELEGRAM_TOKEN, self._bot_desde)
        except Exception as e:
            print("Bot: no pude revisar Telegram:", e)
            return
        for chat, texto in comandos:
            if chat != str(cfg.TELEGRAM_CHAT_ID):
                print("Bot: ignoro mensaje de otro chat", chat)
                if chat not in self._intrusos:
                    # Avisarle al dueno UNA vez por cada extrano
                    self._intrusos.append(chat)
                    self.enviar_texto("\u26A0\uFE0F Alguien mas (chat {}) intento "
                                      "usar tu bot. Lo ignore.".format(chat))
                continue
            comando = self._limpiar_comando(texto)
            print("Bot: comando", comando)
            esperando = (self._confirmar_hasta is not None and
                         time.ticks_diff(self._confirmar_hasta, ahora) > 0)
            self._confirmar_hasta = None
            if comando in ("abrir", "liberar"):
                # Pedir confirmacion para no abrirla por accidente
                self._confirmar_hasta = time.ticks_add(ahora, 30000)
                self.enviar_texto("Seguro que quieres ABRIR el candado?",
                                  botones="confirmar")
            elif comando == "si" and esperando:
                self.responder("CMD|liberar")
                self.enviar_texto("Abriendo...", botones=True)
            elif comando == "no" or comando == "si":
                self.enviar_texto("Ok, no se abre. Sigue como estaba.",
                                  botones=True)
            elif comando in self.PASAR_A_ESP32:
                self.responder("CMD|" + self.PASAR_A_ESP32[comando])
            elif comando == "foto":
                self.tomar_y_enviar("FOTO", "Foto pedida desde Telegram")
            else:
                self.enviar_texto(self.AYUDA, botones=True)

    # ---------- pagina web (foto en vivo) ----------
    def _abrir_web(self):
        try:
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", 80))
            s.listen(1)
            s.setblocking(False)
            self.servidor = s
        except OSError as e:
            print("Web: no se pudo abrir:", e)

    def _atender_web(self):
        if not self.servidor:
            return
        try:
            cliente, _ = self.servidor.accept()
        except OSError:
            return                        # nadie pidio la pagina
        try:
            cliente.settimeout(3)
            cliente.recv(512)
            jpg = self.camara.foto()
            if jpg is None:
                cliente.send(b"HTTP/1.0 500 Error\r\n\r\nSin imagen")
                return
            cliente.send(b"HTTP/1.0 200 OK\r\nContent-Type: image/jpeg\r\n"
                         b"Content-Length: " + str(len(jpg)).encode() +
                         b"\r\nConnection: close\r\n\r\n")
            vista = memoryview(jpg)
            for i in range(0, len(jpg), 1024):
                cliente.write(vista[i:i + 1024])
        except OSError:
            pass
        finally:
            cliente.close()

    # ---------- ciclo ----------
    def correr(self):
        if getattr(cfg, "USAR_WATCHDOG", False):
            # Reinicio automatico si algo se traba mas de 60 s.
            # OJO: con esto activo Thonny no puede detener el programa.
            from machine import WDT
            self._wdt = WDT(timeout=60000)
            print("Watchdog activo")
        while True:
            if self._wdt:
                self._wdt.feed()
            try:
                orden = self._leer_orden()
                if orden:
                    self.atender_orden(orden)
                self._atender_web()
                self._revisar_wifi(time.ticks_ms())
                self._revisar_bot(time.ticks_ms())
                self._reenviar_pendientes(time.ticks_ms())
                self._mantener_mqtt(time.ticks_ms())
            except KeyboardInterrupt:
                raise
            except Exception as e:
                sys.print_exception(e)
            time.sleep_ms(20)


if __name__ == "__main__":
    try:
        Fotografo().correr()
    except KeyboardInterrupt:
        print("Detenido desde Thonny")
    except ImportError as e:
        print("FALTA ALGO:", e)
        print("Si dice 'camera': este firmware NO trae camara.")
        print("Instala el firmware con camara (ver la guia, Etapa 0).")
