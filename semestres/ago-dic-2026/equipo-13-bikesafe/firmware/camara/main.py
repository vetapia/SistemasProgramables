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
#   Y contesta:  OK|FOTO|telegram   /  OK|FOTO|guardada  /  ERR|...
#
# Ademas, cada foto se publica por MQTT para el servidor de IA:
#   bikesafe/cam/info   -> {"nivel": "ROBO", "motivo": "...", "n": 7}
#   bikesafe/cam/frame  -> la foto en JPEG (bytes)
#
# NECESITA un firmware de MicroPython QUE INCLUYA CAMARA (el normal
# no la trae). La guia explica cual instalar. Este programa funciona
# con los dos firmwares mas comunes y detecta solo cual tienes.

import gc
import os
import sys
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
        self.mqtt = None
        self._mqtt_intento_ms = time.ticks_add(time.ticks_ms(), -60000)
        self.conectar_wifi()
        if cfg.USAR_WEB:
            self._abrir_web()
        self.responder("OK|LISTA")
        print("=== Lista. Esperando ordenes ===\n")

    # ---------- WiFi ----------
    def conectar_wifi(self, espera_s=15):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print("WiFi: conectando a", cfg.WIFI_SSID)
            self.wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
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
            return
        if time.ticks_diff(ahora, self._wifi_intento_ms) > 20000:
            self._wifi_intento_ms = ahora
            try:
                self.wlan.connect(cfg.WIFI_SSID, cfg.WIFI_PASS)
            except Exception:
                pass

    # ---------- MQTT (para el servidor de IA) ----------
    def _conectar_mqtt(self):
        if not getattr(cfg, "USAR_MQTT", False) or MQTTClient is None:
            return False
        if self.mqtt:
            return True
        ahora = time.ticks_ms()
        if (not self.wlan.isconnected() or
                time.ticks_diff(ahora, self._mqtt_intento_ms) < 15000):
            return False
        self._mqtt_intento_ms = ahora
        try:
            c = MQTTClient(cfg.MQTT_CLIENTE, cfg.MQTT_BROKER,
                           port=cfg.MQTT_PUERTO, keepalive=60)
            c.connect()
            self.mqtt = c
            print("MQTT OK en", cfg.MQTT_BROKER)
            return True
        except Exception as e:
            print("MQTT: no se pudo conectar:", e)
            self.mqtt = None
            return False

    def publicar_frame(self, jpg, nivel, motivo):
        """Manda la foto al servidor Python (OpenCV) por MQTT."""
        if not self._conectar_mqtt():
            return False
        try:
            info = '{{"nivel": "{}", "motivo": "{}", "n": {}}}'.format(
                nivel, motivo.replace('"', "'"), self._numero)
            self.mqtt.publish(b"bikesafe/cam/info", info)
            self.mqtt.publish(b"bikesafe/cam/frame", jpg)
            print("Foto publicada por MQTT:", len(jpg), "bytes")
            return True
        except Exception as e:
            print("MQTT: fallo al publicar:", e)
            self.mqtt = None
            return False

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

    def tomar_y_enviar(self, nivel, motivo):
        self.led.value(1)
        jpg = self.camara.foto()
        self.led.value(0)
        if jpg is None:
            self.responder("ERR|FOTO|la camara no entrego imagen")
            return
        print("Foto tomada: {} bytes ({})".format(len(jpg), nivel))
        nombre = self._guardar(jpg)
        self.publicar_frame(jpg, nivel, motivo)
        if cfg.USAR_TELEGRAM and self.wlan.isconnected():
            pie = "BikeSafe {}: {}".format(nivel, motivo)
            try:
                if telegram.enviar_foto(cfg.TELEGRAM_TOKEN,
                                        cfg.TELEGRAM_CHAT_ID, jpg, pie):
                    self.responder("OK|FOTO|telegram")
                    return
                self.responder("ERR|FOTO|Telegram la rechazo (token/chat)")
            except Exception as e:
                sys.print_exception(e)
                self.responder("ERR|FOTO|sin internet")
            return
        self.responder("OK|FOTO|guardada como {}".format(nombre))

    def enviar_texto(self, texto):
        if not (cfg.USAR_TELEGRAM and self.wlan.isconnected()):
            self.responder("OK|MSG|no enviado (Telegram apagado)")
            return
        try:
            bien = telegram.enviar_mensaje(cfg.TELEGRAM_TOKEN,
                                           cfg.TELEGRAM_CHAT_ID, texto)
            self.responder("OK|MSG|telegram" if bien
                           else "ERR|MSG|Telegram lo rechazo")
        except Exception as e:
            sys.print_exception(e)
            self.responder("ERR|MSG|sin internet")

    def atender_orden(self, renglon):
        print("Orden:", renglon)
        partes = renglon.split("|")
        if partes[0] == "FOTO":
            nivel = partes[1] if len(partes) > 1 else "AVISO"
            motivo = partes[2] if len(partes) > 2 else ""
            self.tomar_y_enviar(nivel, motivo)
        elif partes[0] == "MSG":
            self.enviar_texto(partes[1] if len(partes) > 1 else "")
        else:
            self.responder("ERR|no entiendo")

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
        while True:
            try:
                orden = self._leer_orden()
                if orden:
                    self.atender_orden(orden)
                self._atender_web()
                self._revisar_wifi(time.ticks_ms())
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
