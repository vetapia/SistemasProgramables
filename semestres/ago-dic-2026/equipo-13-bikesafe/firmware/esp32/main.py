# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   main.py   (va en la ESP32 NORMAL, el "cerebro")
# Objetivo:  Programa principal: lee el llavero RFID, cierra/abre
#            el cerrojo, vigila la bici con el acelerometro, el
#            ultrasonico y el lazo, y dispara la alarma de 2 niveles
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# La ESP32 corre este archivo SOLA cada vez que recibe energia.
#
# COMO PIENSA EL CANDADO (maquina de estados):
#
#     LIBRE  --llavero-->  ASEGURADA  --robo-->  ALARMA
#       ^                      |                    |
#       +------llavero---------+<---llavero---------+
#
#   LIBRE      cerrojo abierto, LED verde parpadea lento
#   ASEGURADA  cerrojo cerrado, LED verde fijo, sensores vigilando
#   ALARMA     sirena + LED rojo rapido + foto + aviso al celular
#
# ALARMA DE 2 NIVELES (para que un roce no dispare la sirena):
#   Nivel 1 AVISO: un toque  -> 2 pitidos + foto. Sigue ASEGURADA.
#   Nivel 2 ROBO:  forcejeo, bici inclinada o cable cortado -> ALARMA.

import sys
import time
import json

import config as cfg
from hal.actuadores import Cerrojo, Zumbador, Led, EnlaceCamara

LIBRE = "LIBRE"
ASEGURADA = "ASEGURADA"
ALARMA = "ALARMA"

ARCHIVO_ESTADO = "estado.txt"


class BikeSafe:
    def __init__(self):
        print("\n=== BikeSafe arrancando ===")
        # ---- actuadores (siempre estan) ----
        self.verde = Led(cfg.PIN_LED_VERDE)
        self.rojo = Led(cfg.PIN_LED_ROJO)
        self.buzzer = Zumbador(cfg.PIN_BUZZER, cfg.BUZZER_ACTIVO)
        self.cerrojo = Cerrojo(cfg.PIN_SERVO, cfg.SERVO_ABIERTO,
                               cfg.SERVO_CERRADO)

        # ---- sensores (cada uno puede faltar) ----
        self.rfid = self._crear("RFID", cfg.USAR_RFID, self._crear_rfid)
        self.acel = self._crear("Acelerometro", cfg.USAR_ACELEROMETRO,
                                self._crear_acel)
        self.ultra = self._crear("Ultrasonico", cfg.USAR_ULTRASONICO,
                                 self._crear_ultra)
        self.lazo = self._crear("Lazo", cfg.USAR_LAZO, self._crear_lazo)
        self.camara = self._crear("Camara", cfg.USAR_CAMARA,
                                  self._crear_camara)
        self.red = self._crear("Red", cfg.USAR_WIFI_MQTT, self._crear_red)

        # ---- memoria del programa ----
        self.estado = LIBRE
        self._ultima = {}            # ultima vez que se hizo cada tarea
        self._toques = []            # momentos de los ultimos toques
        self._ultimo_toque_ms = 0
        self._inclinada_desde = None
        self._cerca_desde = None
        self._ultima_foto_ms = time.ticks_add(time.ticks_ms(),
                                              -cfg.ESPERA_ENTRE_FOTOS_MS)
        self._alarma_desde = 0
        self._rojo_hasta = None
        self._lazo_avisado = False
        self._dist = None
        self._cambio = 0.0
        self._incl = 0.0

        # ---- recordar como estaba antes de apagarse ----
        # Si se va la luz con la bici asegurada, al volver NO debe
        # abrirse sola. Por eso guardamos el estado en un archivo.
        if self._leer_estado_guardado() == ASEGURADA:
            print("Estaba ASEGURADA antes de apagarse: sigo cerrado")
            self._entrar_asegurada(avisar=False)
        else:
            self.cerrojo.abrir()
            self._poner_estado(LIBRE)
        self.buzzer.pitido(1)
        if cfg.ASEGURAR_AL_ARRANCAR and self.estado == LIBRE:
            print("Modo prueba sin RFID: me aseguro solo en 5 segundos...")
            time.sleep(5)
            self.asegurar()
        print("=== Listo. Estado:", self.estado, "===\n")

    # ===========================================================
    #  ARRANQUE DE CADA PIEZA
    # ===========================================================
    def _crear(self, nombre, usar, funcion):
        """Intenta crear una pieza. Si falla, avisa y sigue sin ella."""
        if not usar:
            print(" -", nombre, "desactivado en config.py")
            return None
        try:
            pieza = funcion()
            print(" +", nombre, "OK")
            return pieza
        except Exception as e:
            print(" !", nombre, "NO respondio (", e, "). Sigo sin el.")
            return None

    def _crear_rfid(self):
        from hal.sensores import LectorRFID
        lector = LectorRFID(cfg.PIN_RFID_SCK, cfg.PIN_RFID_MOSI,
                            cfg.PIN_RFID_MISO, cfg.PIN_RFID_SDA,
                            cfg.PIN_RFID_RST)
        if not lector.conectado():
            raise OSError("el RC522 no contesta, revisa cables y 3.3 V")
        return lector

    def _crear_acel(self):
        from hal.sensores import Acelerometro
        return Acelerometro(cfg.PIN_I2C_SDA, cfg.PIN_I2C_SCL)

    def _crear_ultra(self):
        from hal.sensores import Ultrasonico
        return Ultrasonico(cfg.PIN_TRIG, cfg.PIN_ECHO)

    def _crear_lazo(self):
        from hal.sensores import LazoAntiCorte
        return LazoAntiCorte(cfg.PIN_LAZO)

    def _crear_camara(self):
        return EnlaceCamara(cfg.PIN_CAM_TX, cfg.PIN_CAM_RX)

    def _crear_red(self):
        from red import Red
        red = Red(cfg)
        red.conectar_wifi()
        return red

    # ===========================================================
    #  UTILERIAS
    # ===========================================================
    def _toca(self, tarea, ahora, cada_ms):
        """True si ya pasaron 'cada_ms' desde la ultima vez de 'tarea'.
        Asi cada sensor se revisa a su ritmo sin usar sleep largos."""
        ultima = self._ultima.get(tarea)
        if ultima is None or time.ticks_diff(ahora, ultima) >= cada_ms:
            self._ultima[tarea] = ahora
            return True
        return False

    def _leer_estado_guardado(self):
        try:
            with open(ARCHIVO_ESTADO) as f:
                return f.read().strip()
        except OSError:
            return LIBRE

    def _poner_estado(self, nuevo):
        self.estado = nuevo
        # En el archivo solo guardamos si el cerrojo esta cerrado o no
        guardado = LIBRE if nuevo == LIBRE else ASEGURADA
        try:
            if self._leer_estado_guardado() != guardado:
                with open(ARCHIVO_ESTADO, "w") as f:
                    f.write(guardado)
        except OSError:
            pass
        # Luces segun el estado
        if nuevo == LIBRE:
            self.rojo.apagar()
            self.verde.parpadear(800)
        elif nuevo == ASEGURADA:
            self.rojo.apagar()
            self.verde.encender()
        else:
            self.verde.apagar()
            self.rojo.parpadear(120)
        print(">> ESTADO:", nuevo)
        if self.red:
            self.red.publicar(b"bikesafe/estado", nuevo, True)

    def _alerta(self, texto):
        print("!!", texto)
        if self.red:
            self.red.publicar(b"bikesafe/alerta", texto)

    def _foto(self, nivel, motivo, forzar=False):
        """Le pide una foto a la camara, respetando el tiempo minimo
        entre fotos (a menos que sea un robo: forzar=True)."""
        if not self.camara:
            return
        ahora = time.ticks_ms()
        if (not forzar and time.ticks_diff(ahora, self._ultima_foto_ms)
                < cfg.ESPERA_ENTRE_FOTOS_MS):
            return
        self._ultima_foto_ms = ahora
        self.camara.pedir_foto(nivel, motivo)

    # ===========================================================
    #  ACCIONES PRINCIPALES
    # ===========================================================
    def _entrar_asegurada(self, avisar=True):
        self.cerrojo.cerrar()
        time.sleep_ms(1200)          # esperar a que todo deje de vibrar
        if self.acel:
            self.acel.guardar_referencia()
        self._toques = []
        self._inclinada_desde = None
        self._cerca_desde = None
        self._lazo_avisado = False
        self._poner_estado(ASEGURADA)
        if avisar and self.camara:
            self.camara.mensaje("BikeSafe: bici ASEGURADA")

    def asegurar(self):
        if self.estado != LIBRE:
            return
        self.buzzer.pitido(1)
        self._entrar_asegurada()

    def liberar(self):
        if self.estado == LIBRE:
            return
        self.buzzer.sirena(False)
        self.cerrojo.abrir()
        self._poner_estado(LIBRE)
        self.buzzer.pitido(2)
        if self.camara:
            self.camara.mensaje("BikeSafe: bici LIBERADA")

    def aviso(self, motivo):
        """NIVEL 1: algo raro, pero todavia no es robo."""
        self._alerta("AVISO: " + motivo)
        self.buzzer.pitido(2, 60, 60)
        self.rojo.encender()
        self._rojo_hasta = time.ticks_add(time.ticks_ms(), 1500)
        self._foto("AVISO", motivo)

    def alarma(self, motivo):
        """NIVEL 2: robo. Sirena, luz, foto y aviso."""
        if self.estado == ALARMA:
            return
        self._alerta("ROBO: " + motivo)
        self._alarma_desde = time.ticks_ms()
        self._rojo_hasta = None
        self._poner_estado(ALARMA)
        self.buzzer.sirena(True)
        self._foto("ROBO", motivo, forzar=True)

    def silenciar(self):
        """Calla la sirena pero la bici SIGUE asegurada."""
        if self.estado != ALARMA:
            return
        self.buzzer.sirena(False)
        time.sleep_ms(300)
        if self.acel:
            self.acel.guardar_referencia()   # nueva posicion de la bici
        self._toques = []
        self._inclinada_desde = None
        self._poner_estado(ASEGURADA)

    # ===========================================================
    #  REVISIONES (se llaman en cada vuelta del ciclo)
    # ===========================================================
    def _revisar_rfid(self, ahora):
        if not self.rfid or not self._toca("rfid", ahora, 150):
            return
        uid = self.rfid.leer()
        if uid is None:
            return
        print("Tarjeta:", uid)
        if uid in cfg.TARJETAS_AUTORIZADAS:
            if self.estado == LIBRE:
                self.asegurar()
            else:
                self.liberar()
        else:
            self.buzzer.pitido(3, 40, 40)
            self._alerta("Tarjeta NO autorizada: " + uid)
            if self.estado == ASEGURADA:
                self._foto("AVISO", "Tarjeta desconocida " + uid)

    def _revisar_movimiento(self, ahora):
        if not self.acel or not self._toca("acel", ahora, 50):
            return
        lectura = self.acel.leer()
        self._cambio = self.acel.cambio(lectura)
        self._incl = self.acel.inclinacion(lectura)

        # --- inclinada o levantada por un rato = ROBO ---
        if self._incl > cfg.UMBRAL_INCLINA_GRADOS:
            if self._inclinada_desde is None:
                self._inclinada_desde = ahora
            elif (time.ticks_diff(ahora, self._inclinada_desde)
                  > cfg.TIEMPO_INCLINA_MS):
                self.alarma("Bici inclinada o levantada")
                return
        else:
            self._inclinada_desde = None

        # --- toques ---
        if self._cambio < cfg.UMBRAL_TOQUE_G:
            return
        # Un mismo jalon dura varias lecturas: lo contamos una vez
        if time.ticks_diff(ahora, self._ultimo_toque_ms) < 400:
            return
        self._ultimo_toque_ms = ahora
        # Olvidar toques viejos y agregar el nuevo
        self._toques = [t for t in self._toques
                        if time.ticks_diff(ahora, t) < cfg.VENTANA_TOQUES_MS]
        self._toques.append(ahora)
        if len(self._toques) >= cfg.TOQUES_PARA_ROBO:
            self.alarma("Forcejeo continuo")
        else:
            self.aviso("Movimiento ({} de {})".format(
                len(self._toques), cfg.TOQUES_PARA_ROBO))

    def _revisar_presencia(self, ahora):
        if not self.ultra or not self._toca("ultra", ahora, 300):
            return
        self._dist = self.ultra.distancia_cm()
        cerca = (self._dist is not None and
                 self._dist < cfg.DISTANCIA_CERCA_CM)
        if not cerca:
            self._cerca_desde = None
            return
        if self._cerca_desde is None:
            self._cerca_desde = ahora
        elif time.ticks_diff(ahora, self._cerca_desde) > cfg.TIEMPO_CERCA_MS:
            self._cerca_desde = None
            if (time.ticks_diff(ahora, self._ultima_foto_ms)
                    >= cfg.ESPERA_ENTRE_FOTOS_MS):
                self._alerta("Alguien cerca de la bici")
                self.buzzer.pitido(1, 40)
                self._foto("PRESENCIA", "Alguien a {:.0f} cm".format(
                    self._dist))

    def _revisar_lazo(self, ahora):
        if not self.lazo or not self._toca("lazo", ahora, 200):
            return
        if self.lazo.cortado():
            if not self._lazo_avisado:
                self._lazo_avisado = True
                self.alarma("Cable cortado")
        else:
            self._lazo_avisado = False

    def _revisar_fin_alarma(self, ahora):
        if (time.ticks_diff(ahora, self._alarma_desde)
                > cfg.DURACION_ALARMA_MS):
            print("La alarma ya sono suficiente: me callo y sigo vigilando")
            self.silenciar()

    def _revisar_camara(self):
        if not self.camara:
            return
        respuesta = self.camara.leer_respuesta()
        if respuesta:
            print("Camara dice:", respuesta)
            if self.red:
                self.red.publicar(b"bikesafe/camara", respuesta)

    def _revisar_red(self, ahora):
        if not self.red:
            return
        # No intentamos reconectar en plena alarma (puede tardar)
        self.red.atender(ahora, puede_reconectar=(self.estado != ALARMA))
        comando = self.red.siguiente_comando()
        if comando:
            print("Comando MQTT:", comando)
            if comando == "asegurar":
                self.asegurar()
            elif comando == "liberar" and cfg.PERMITIR_ABRIR_POR_MQTT:
                self.liberar()
            elif comando == "silenciar":
                self.silenciar()
            elif comando == "foto":
                self._foto("MANUAL", "Foto pedida desde el celular",
                           forzar=True)
            else:
                self._comando_actuador(comando)
        if self._toca("publicar", ahora, cfg.PERIODO_PUBLICAR_MS):
            dist = None if self._dist is None else round(self._dist, 1)
            self.red.publicar(b"bikesafe/sensores", json.dumps({
                "estado": self.estado,
                "dist": dist,
                "cambio": round(self._cambio, 2),
                "incl": round(self._incl, 1),
            }))
            # Un topico por sensor (Tabla HAL del curso)
            if dist is not None:
                self.red.publicar(b"bikesafe/sensor/distancia", str(dist))
            self.red.publicar(b"bikesafe/sensor/movimiento",
                              str(round(self._cambio, 2)))
            self.red.publicar(b"bikesafe/sensor/inclinacion",
                              str(round(self._incl, 1)))
            if self.lazo:
                self.red.publicar(b"bikesafe/sensor/lazo",
                                  "CORTADO" if self.lazo.cortado()
                                  else "ENTERO")

    def _comando_actuador(self, comando):
        """Ordenes que llegan del servidor Python (la IA) o del celular
        a un actuador en particular."""
        if comando == "alerta_ia":
            # La IA confirmo que hay una PERSONA en la foto
            self._alerta("IA: persona detectada junto a la bici")
            self.buzzer.pitido(3, 80, 80)
            self.rojo.encender()
            self._rojo_hasta = time.ticks_add(time.ticks_ms(), 3000)
        elif comando == "servo:cerrar":
            self.asegurar()
        elif comando == "servo:abrir" and cfg.PERMITIR_ABRIR_POR_MQTT:
            self.liberar()
        elif comando == "buzzer:pitido":
            self.buzzer.pitido(1)
        elif comando == "buzzer:sirena_off":
            self.silenciar()
        elif comando == "led:alerta":
            self.rojo.encender()
            self._rojo_hasta = time.ticks_add(time.ticks_ms(), 3000)
        elif comando == "led:normal":
            self._rojo_hasta = time.ticks_ms()
        else:
            print("Comando desconocido:", comando)

    # ===========================================================
    #  CICLO PRINCIPAL
    # ===========================================================
    def vuelta(self):
        ahora = time.ticks_ms()

        self._revisar_rfid(ahora)

        if self.estado == ASEGURADA:
            self._revisar_movimiento(ahora)
        if self.estado == ASEGURADA:        # pudo cambiar a ALARMA arriba
            self._revisar_presencia(ahora)
        if self.estado == ASEGURADA:
            self._revisar_lazo(ahora)
        if self.estado == ALARMA:
            self._revisar_fin_alarma(ahora)

        self._revisar_camara()
        self._revisar_red(ahora)

        # Apagar el destello rojo del aviso
        if (self._rojo_hasta is not None and
                time.ticks_diff(ahora, self._rojo_hasta) >= 0):
            self._rojo_hasta = None
            if self.estado == ASEGURADA:
                self.rojo.apagar()

        # Cosas que parpadean o suenan solas
        self.buzzer.actualizar(ahora)
        self.verde.actualizar(ahora)
        self.rojo.actualizar(ahora)

    def correr(self):
        while True:
            try:
                self.vuelta()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Un error NO debe tumbar el candado: lo mostramos y seguimos
                sys.print_exception(e)
                time.sleep_ms(200)
            time.sleep_ms(10)


def main():
    app = None
    try:
        app = BikeSafe()
        app.correr()
    except KeyboardInterrupt:
        print("Detenido desde Thonny")
    finally:
        if app:
            app.buzzer.sirena(False)


if __name__ == "__main__":
    main()
