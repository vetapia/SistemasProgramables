# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   main.py   (va en la ESP32 NORMAL, el "cerebro")
# Objetivo:  Programa principal: obedece al dueno (Telegram o dashboard),
#            mueve el cerrojo, vigila la bici con sus sensores y DECIDE
#            la alarma de 2 niveles, sin depender de la laptop
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
#     LIBRE  --Cerrar-->  ASEGURADA  --robo-->  ALARMA
#       ^                     |  ^                 |
#       +------Abrir----------+  +---Silenciar-----+
#       +---------------------Abrir----------------+
#
#   LIBRE      cerrojo abierto, LED verde parpadeando lento
#   ASEGURADA  cerrojo cerrado, LED azul fijo, sensores vigilando
#   ALARMA     sirena + LED rojo rapido + rafaga de fotos + Telegram
#
# ALARMA DE 2 NIVELES (para que un roce no dispare la sirena):
#   Nivel 1 AVISO: un toque, alguien parado junto a la bici o la IA ve
#                  a una persona -> pitidos + color + foto. Sigue ASEGURADA.
#   Nivel 2 ROBO:  forcejeo (4 toques en 6 s), bici inclinada, cable
#                  cortado, cerrojo abierto a la fuerza, o la IA ve a una
#                  persona MIENTRAS mueven la bici -> ALARMA.
#
# TODAS las decisiones se toman aqui. La laptop (servidor con IA) solo
# INFORMA lo que vio en la foto; si la laptop esta apagada, el candado
# protege la bici igual.

import sys
import time
import json

import config as cfg
from hal.actuadores import (Cerrojo, Zumbador, Luz, LedRGB, DosLeds,
                            EnlaceCamara)

LIBRE = "LIBRE"
ASEGURADA = "ASEGURADA"
ALARMA = "ALARMA"

ARCHIVO_ESTADO = "estado.txt"


def _cfg(nombre, defecto):
    """Lee un ajuste de config.py; si no existe usa el valor por
    defecto (asi un config.py viejo sigue funcionando)."""
    return getattr(cfg, nombre, defecto)


class BikeSafe:
    def __init__(self):
        print("\n=== BikeSafe arrancando ===")
        # ---- actuadores (siempre estan) ----
        self.luz = Luz(self._crear_led())
        self.buzzer = Zumbador(cfg.PIN_BUZZER, cfg.BUZZER_ACTIVO)
        self.cerrojo = Cerrojo(cfg.PIN_SERVO, cfg.SERVO_ABIERTO,
                               cfg.SERVO_CERRADO)
        self.luz.destello("cian", 800)        # "estoy prendiendo"

        # ---- sensores (cada uno puede faltar) ----
        self.acel = self._crear("Acelerometro MPU6050", cfg.USAR_ACELEROMETRO,
                                self._crear_acel)
        self.ultra = self._crear("Ultrasonico HC-SR04", cfg.USAR_ULTRASONICO,
                                 self._crear_ultra)
        self.reed = self._crear("Sensor magnetico del cerrojo",
                                _cfg("USAR_SENSOR_CERROJO", False),
                                self._crear_reed)
        self.lazo = self._crear("Lazo anti-corte", cfg.USAR_LAZO,
                                self._crear_lazo)
        self.pir = self._crear("PIR", _cfg("USAR_PIR", False),
                               self._crear_pir)
        self.camara = self._crear("Camara (UART)", cfg.USAR_CAMARA,
                                  self._crear_camara)
        self.red = self._crear("Red WiFi + MQTT", cfg.USAR_WIFI_MQTT,
                               self._crear_red)

        # ---- memoria del programa ----
        self.estado = LIBRE
        self._ultima = {}            # ultima vez que se hizo cada tarea
        self._toques = []            # momentos de los ultimos toques
        self._ultimo_toque_ms = None
        self._inclinada_desde = None
        self._cerca_desde = None
        self._reed_abierto_desde = None
        self._ultima_foto_ms = time.ticks_add(time.ticks_ms(),
                                              -cfg.ESPERA_ENTRE_FOTOS_MS)
        self._alarma_desde = 0
        self._lazo_avisado = False
        self._acel_avisado = False
        self._dist = None
        self._cambio = 0.0
        self._incl = 0.0
        self._rafaga = 0             # fotos extra pendientes en un robo
        self._rafaga_ms = 0
        self._buscar_hasta = None    # boton "Buscar": sirena 5 s
        self._pir_ms = None          # ultima vez que el PIR vio a alguien
        self._personas_ia = []       # momentos en que la IA vio persona
        self._ultima_ia = None       # (clase, confianza)
        self._n_avisos = 0           # contadores para "Estado"
        self._n_robos = 0
        self._inicio_ms = time.ticks_ms()
        self._wdt = None

        # ---- recordar como estaba antes de apagarse ----
        # Si se va la luz con la bici asegurada, al volver NO debe
        # abrirse sola. Por eso guardamos el estado en un archivo.
        if self._leer_estado_guardado() == ASEGURADA:
            print("Estaba ASEGURADA antes de apagarse: sigo cerrado")
            self._entrar_asegurada(origen="reinicio", avisar=False)
        else:
            self.cerrojo.abrir()
            self._poner_estado(LIBRE)
        self.buzzer.pitido(1)
        if cfg.ASEGURAR_AL_ARRANCAR and self.estado == LIBRE:
            print("Modo prueba: me aseguro solo en 5 segundos...")
            time.sleep(5)
            self.asegurar("prueba")
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

    def _crear_led(self):
        if _cfg("USAR_LED_RGB", False):
            print(" + LED RGB en", cfg.PIN_RGB_R, cfg.PIN_RGB_G, cfg.PIN_RGB_B)
            return LedRGB(cfg.PIN_RGB_R, cfg.PIN_RGB_G, cfg.PIN_RGB_B,
                          _cfg("RGB_ANODO_COMUN", False))
        print(" + LEDs verde/rojo (sin RGB)")
        return DosLeds(cfg.PIN_LED_VERDE, cfg.PIN_LED_ROJO)

    def _crear_acel(self):
        from hal.sensores import Acelerometro
        return Acelerometro(cfg.PIN_I2C_SDA, cfg.PIN_I2C_SCL)

    def _crear_ultra(self):
        from hal.sensores import Ultrasonico
        return Ultrasonico(cfg.PIN_TRIG, cfg.PIN_ECHO)

    def _crear_reed(self):
        from hal.sensores import SensorCerrojo
        return SensorCerrojo(cfg.PIN_REED, _cfg("REED_CERRADO_ES", 0))

    def _crear_lazo(self):
        from hal.sensores import LazoAntiCorte
        return LazoAntiCorte(cfg.PIN_LAZO)

    def _crear_pir(self):
        from hal.sensores import SensorPIR
        return SensorPIR(cfg.PIN_PIR)

    def _crear_camara(self):
        return EnlaceCamara(cfg.PIN_CAM_TX, cfg.PIN_CAM_RX)

    def _crear_red(self):
        from red import Red
        red = Red(cfg)
        if not _cfg("MQTT_CLAVE", ""):
            print("   OJO: sin MQTT_CLAVE los mensajes no van firmados y")
            print("   NO se podra abrir el candado por MQTT/dashboard.")
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

    @staticmethod
    def _hace_menos(ahora, momento, ms):
        return momento is not None and time.ticks_diff(ahora, momento) < ms

    def _leer_estado_guardado(self):
        try:
            with open(ARCHIVO_ESTADO) as f:
                return f.read().strip()
        except OSError:
            return LIBRE

    def _luces_del_estado(self):
        if self.estado == LIBRE:
            self.luz.parpadear("verde", 800)
        elif self.estado == ASEGURADA:
            self.luz.fijo("azul")
        else:
            self.luz.parpadear("rojo", 120)

    def _poner_estado(self, nuevo, origen=""):
        anterior = self.estado
        self.estado = nuevo
        # En el archivo solo guardamos si el cerrojo esta cerrado o no
        guardado = LIBRE if nuevo == LIBRE else ASEGURADA
        try:
            if self._leer_estado_guardado() != guardado:
                with open(ARCHIVO_ESTADO, "w") as f:
                    f.write(guardado)
        except OSError:
            pass
        self._luces_del_estado()
        print(">> ESTADO:", nuevo)
        if self.red:
            self.red.publicar(b"bikesafe/estado", nuevo, True)
        if anterior != nuevo:
            self._evento("estado", "{} -> {}".format(anterior, nuevo), origen)

    def _evento(self, tipo, detalle, origen=""):
        """Todo lo importante queda en el historial (Firebase)."""
        if self.red:
            self.red.publicar(b"bikesafe/evento", json.dumps(
                {"tipo": tipo, "detalle": detalle, "origen": origen,
                 "estado": self.estado}))

    def _alerta(self, texto):
        print("!!", texto)
        if self.red:
            self.red.publicar(b"bikesafe/alerta", texto)
        self._evento("alerta", texto)

    def _telegram(self, texto):
        if self.camara:
            self.camara.mensaje(texto)

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
    def _entrar_asegurada(self, origen="", avisar=True):
        self.cerrojo.cerrar()
        time.sleep_ms(1200)          # esperar a que todo deje de vibrar
        if self.acel:
            try:
                self.acel.guardar_referencia()
            except OSError:
                print("Acelerometro: no pude guardar la referencia")
        self._toques = []
        self._ultimo_toque_ms = None
        self._inclinada_desde = None
        self._cerca_desde = None
        self._reed_abierto_desde = None
        self._personas_ia = []
        self._lazo_avisado = False
        self._acel_avisado = False
        self.luz.quitar_destello()
        self._poner_estado(ASEGURADA, origen)
        if avisar:
            extra = "" if origen in ("", "telegram") else " (desde {})".format(origen)
            self._telegram("\U0001F512 BikeSafe: bici ASEGURADA" + extra)

    def asegurar(self, origen=""):
        """Regresa True si se aseguro."""
        if self.estado != LIBRE:
            return False
        # El sensor magnetico confirma que el cable SI esta metido en el
        # cerrojo. Si no, no tiene caso cerrar: la bici quedaria suelta.
        if (self.reed and _cfg("REED_OBLIGATORIO", True)
                and not self.reed.cerrado()):
            self.buzzer.pitido(3, 40, 40)
            self.luz.destello("amarillo", 1500)
            texto = ("\u26D4 BikeSafe: NO cerre. El sensor del cerrojo dice ABIERTO: "
                     "mete bien el cable en el candado y vuelve a tocar Cerrar.")
            print(texto)
            self._telegram(texto)
            self._evento("cerrojo", "no cerro: cable fuera", origen)
            return False
        self.buzzer.pitido(1)
        self._entrar_asegurada(origen)
        return True

    def liberar(self, origen=""):
        if self.estado == LIBRE:
            return False
        self.buzzer.sirena(False)
        self._rafaga = 0
        self._buscar_hasta = None
        self.cerrojo.abrir()
        self._poner_estado(LIBRE, origen)
        self.buzzer.pitido(2)
        extra = "" if origen in ("", "telegram") else " (desde {})".format(origen)
        self._telegram("\U0001F513 BikeSafe: bici LIBERADA" + extra)
        return True

    def aviso(self, motivo, color="amarillo", nivel="AVISO", foto=True):
        """NIVEL 1: algo raro, pero todavia no es robo."""
        self._alerta("AVISO: " + motivo)
        self._n_avisos += 1
        self.buzzer.pitido(2, 60, 60)
        self.luz.destello(color, 1500)
        if foto:
            self._foto(nivel, motivo)

    def alarma(self, motivo):
        """NIVEL 2: robo. Sirena, luz, rafaga de fotos y aviso."""
        if self.estado == ALARMA:
            return
        self._alerta("ROBO: " + motivo)
        self._n_robos += 1
        self._buscar_hasta = None
        self._alarma_desde = time.ticks_ms()
        self.luz.quitar_destello()
        self._poner_estado(ALARMA, "sensores")
        self.buzzer.sirena(True)
        self._foto("ROBO", motivo, forzar=True)
        # Rafaga: mas fotos seguidas para tener mejor evidencia
        self._rafaga = _cfg("FOTOS_EXTRA_ROBO", 2)
        self._rafaga_ms = time.ticks_ms()

    def silenciar(self, origen=""):
        """Calla la sirena pero la bici SIGUE asegurada."""
        if self.estado != ALARMA:
            return False
        self.buzzer.sirena(False)
        self._rafaga = 0
        time.sleep_ms(300)
        if self.acel:
            try:
                self.acel.guardar_referencia()   # nueva posicion de la bici
            except OSError:
                pass
        self._toques = []
        self._inclinada_desde = None
        self._reed_abierto_desde = None
        self._poner_estado(ASEGURADA, origen)
        return True

    def buscar(self):
        """Boton "Buscar": suena unos segundos para encontrar la bici."""
        if self.estado == ALARMA:
            return False
        self.buzzer.sirena(True)
        self.luz.quitar_destello()
        self.luz.parpadear("blanco", 100)
        self._buscar_hasta = time.ticks_add(
            time.ticks_ms(), _cfg("DURACION_BUSCAR_MS", 5000))
        return True

    def _texto_estado(self):
        """Resumen para el boton "Estado" de Telegram."""
        dist = self.ultra.distancia_cm() if self.ultra else None
        minutos = time.ticks_diff(time.ticks_ms(), self._inicio_ms) // 60000
        renglones = ["BikeSafe: {}".format(self.estado)]
        if self.reed:
            renglones.append("Cerrojo (sensor magnetico): {}".format(
                self.reed.texto()))
        if self.lazo:
            renglones.append("Cable: {}".format(
                "CORTADO" if self.lazo.cortado() else "entero"))
        if dist is not None:
            renglones.append("Distancia al frente: {:.0f} cm".format(dist))
        if self.acel and self.estado != LIBRE:
            renglones.append("Inclinacion: {:.0f} grados".format(self._incl))
        if self.pir:
            renglones.append("Movimiento cerca: {}".format(
                "si" if self.pir.hay_alguien() else "no"))
        if self._ultima_ia:
            renglones.append("Ultima IA: {} {:.0f}%".format(
                self._ultima_ia[0], self._ultima_ia[1] * 100))
        if self.red:
            renglones.append("Dashboard (MQTT): {}".format(
                "conectado" if self.red.conectado() else "sin conexion"))
        renglones.append("Avisos: {}  Robos: {}".format(self._n_avisos,
                                                         self._n_robos))
        renglones.append("Encendido hace {} h {} min".format(minutos // 60,
                                                             minutos % 60))
        return "\n".join(renglones)

    # ===========================================================
    #  ORDENES DEL DUENO (Telegram por UART, dashboard por MQTT)
    # ===========================================================
    def ejecutar(self, comando, origen):
        """Un solo lugar para todas las ordenes. Regresa el texto con el
        que hay que contestarle al dueno (o None si ya se aviso)."""
        print("Orden '{}' desde {}".format(comando, origen))
        self._evento("comando", comando, origen)
        if comando == "asegurar":
            if self.estado != LIBRE:
                return "BikeSafe: ya estaba asegurada"
            self.asegurar(origen)          # ya avisa por Telegram
            return None
        if comando == "liberar":
            if self.estado == LIBRE:
                return "BikeSafe: ya estaba libre"
            self.liberar(origen)           # ya avisa por Telegram
            return None
        if comando == "silenciar":
            if self.silenciar(origen):
                return "\U0001F515 BikeSafe: alarma silenciada, la bici sigue asegurada"
            return "BikeSafe: no hay alarma sonando"
        if comando == "estado":
            return self._texto_estado()
        if comando == "buscar":
            if self.buscar():
                return "\U0001F50A BikeSafe: sonando {} segundos para que la encuentres".format(
                    _cfg("DURACION_BUSCAR_MS", 5000) // 1000)
            return "BikeSafe: la alarma ya esta sonando"
        if comando == "foto":
            self._foto("MANUAL", "Foto pedida desde " + origen, forzar=True)
            return None
        return self._comando_actuador(comando)

    def _comando_actuador(self, comando):
        """Ordenes directas a un actuador (topicos de la Tabla HAL)."""
        if comando == "servo:cerrar":
            self.asegurar("dashboard")
        elif comando == "servo:abrir":
            self.liberar("dashboard")
        elif comando == "buzzer:pitido":
            self.buzzer.pitido(1)
        elif comando == "buzzer:sirena_off":
            self.silenciar("dashboard")
        elif comando == "led:alerta":
            self.luz.destello("rojo", 3000)
        elif comando == "led:normal":
            self.luz.quitar_destello()
        elif comando.startswith("led:"):
            self.luz.destello(comando[4:], 3000)   # led:morado, led:cian...
        else:
            print("Comando desconocido:", comando)
        return None

    # ===========================================================
    #  IA: el servidor solo INFORMA; la decision es de la ESP32
    # ===========================================================
    def _resultado_ia(self, texto, ahora):
        try:
            datos = json.loads(texto)
            clase = datos.get("clase", "")
            conf = float(datos.get("conf", 0))
        except (ValueError, TypeError, AttributeError):
            print("IA: mensaje raro:", texto)
            return
        self._ultima_ia = (clase, conf)
        print("IA dice: {} {:.0f}%".format(clase, conf * 100))
        if self.estado != ASEGURADA:
            return                       # libre: no importa / alarma: ya suena
        if clase != "persona" or conf < _cfg("IA_CONFIANZA_MINIMA", 0.45):
            return
        ventana = _cfg("IA_VENTANA_MS", 120000)
        self._personas_ia = [t for t in self._personas_ia
                             if time.ticks_diff(ahora, t) < ventana]
        self._personas_ia.append(ahora)
        # Regla: persona confirmada + la bici se movio hace poco = ROBO
        movieron = self._hace_menos(ahora, self._ultimo_toque_ms, ventana)
        if (movieron and len(self._personas_ia) >=
                _cfg("IA_PERSONAS_PARA_ROBO", 2)):
            self.alarma("IA: persona manipulando la bici ({:.0f}%)".format(
                conf * 100))
            return
        # Si no, es un aviso (morado) y se le dice al dueno
        self._alerta("IA: persona junto a la bici ({:.0f}%)".format(conf * 100))
        self._n_avisos += 1
        self.buzzer.pitido(3, 80, 80)
        self.luz.destello("morado", 3000)
        self._telegram("\U0001F916 BikeSafe: la IA confirmo una PERSONA junto a tu bici "
                       "({:.0f}%)".format(conf * 100))

    # ===========================================================
    #  REVISIONES (se llaman en cada vuelta del ciclo)
    # ===========================================================
    def _revisar_movimiento(self, ahora):
        if not self.acel or not self._toca("acel", ahora, 50):
            return
        try:
            lectura = self.acel.leer()
        except OSError:
            # 5 fallas seguidas: el cable I2C se solto o lo arrancaron
            if self.acel.fallas >= 5 and not self._acel_avisado:
                self._acel_avisado = True
                self.aviso("El acelerometro no responde (cable suelto?)",
                           foto=True)
            if self.acel.fallas % 40 == 0:            # cada ~2 s
                try:
                    self.acel._despertar()
                except OSError:
                    pass
            return
        if self._acel_avisado:
            self._acel_avisado = False
            self._alerta("El acelerometro volvio a responder")
            self.acel.guardar_referencia()
            return
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
        if self._hace_menos(ahora, self._ultimo_toque_ms, 400):
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

    def _medir_distancia(self, ahora):
        """El ultrasonico se lee siempre (para el dashboard)."""
        if self.ultra and self._toca("ultra", ahora, 300):
            self._dist = self.ultra.distancia_cm()
            return True
        return False

    def _revisar_presencia(self, ahora, medi):
        if self.pir and self.pir.hay_alguien():
            self._pir_ms = ahora
        if not medi:
            return
        cerca = (self._dist is not None and
                 self._dist < cfg.DISTANCIA_CERCA_CM)
        # Con PIR: solo cuenta si ademas el PIR vio movimiento hace poco
        # (asi una pared o la mochila no generan fotos falsas)
        if cerca and self.pir:
            cerca = self._hace_menos(ahora, self._pir_ms, 5000)
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
                self.luz.destello("cian", 1000)
                self._foto("PRESENCIA", "Alguien a {:.0f} cm".format(
                    self._dist))

    def _revisar_cerrojo(self, ahora):
        """Si el sensor magnetico dice ABIERTO con la bici asegurada,
        alguien saco el cable o forzo el pasador = ROBO."""
        if not self.reed or not self._toca("reed", ahora, 100):
            return
        if not self.reed.abierto():
            self._reed_abierto_desde = None
            return
        if self._reed_abierto_desde is None:
            self._reed_abierto_desde = ahora
        elif (time.ticks_diff(ahora, self._reed_abierto_desde)
              >= _cfg("TIEMPO_CERROJO_ABIERTO_MS", 500)):
            self._reed_abierto_desde = None
            self.alarma("Cerrojo abierto a la fuerza")

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
            self.silenciar("tiempo")
            self._telegram("BikeSafe: la sirena se apago sola despues de "
                           "{} s. La bici sigue asegurada.".format(
                               cfg.DURACION_ALARMA_MS // 1000))

    def _revisar_rafaga(self, ahora):
        if self._rafaga <= 0:
            return
        if time.ticks_diff(ahora, self._rafaga_ms) >= _cfg(
                "ESPERA_RAFAGA_MS", 6000):
            self._rafaga -= 1
            self._rafaga_ms = ahora
            self._foto("ROBO", "Foto extra del robo", forzar=True)

    def _revisar_buscar(self, ahora):
        if (self._buscar_hasta is not None and
                time.ticks_diff(ahora, self._buscar_hasta) >= 0):
            self._buscar_hasta = None
            if self.estado != ALARMA:
                self.buzzer.sirena(False)
                self._luces_del_estado()

    def _revisar_camara(self):
        if not self.camara:
            return
        respuesta = self.camara.leer_respuesta()
        if not respuesta:
            return
        if respuesta.startswith("CMD|"):
            contestar = self.ejecutar(respuesta[4:].strip().lower(),
                                      "telegram")
            if contestar:
                self._telegram(contestar)
            return
        print("Camara dice:", respuesta)
        if self.red:
            self.red.publicar(b"bikesafe/camara", respuesta)

    def _revisar_red(self, ahora):
        if not self.red:
            return
        # No intentamos reconectar en plena alarma (puede tardar)
        self.red.atender(ahora, puede_reconectar=(self.estado != ALARMA))
        mensaje = self.red.siguiente()
        if mensaje:
            tipo, texto = mensaje
            if tipo == "ia":
                self._resultado_ia(texto, ahora)
            elif texto in ("liberar", "servo:abrir") and not (
                    _cfg("PERMITIR_ABRIR_POR_MQTT", True)
                    and _cfg("MQTT_CLAVE", "")):
                print("Abrir por MQTT no permitido (falta MQTT_CLAVE)")
            else:
                self.ejecutar(texto, "dashboard")
        if self._toca("publicar", ahora, cfg.PERIODO_PUBLICAR_MS):
            self._publicar_sensores()

    def _publicar_sensores(self):
        dist = None if self._dist is None else round(self._dist, 1)
        datos = {"estado": self.estado, "dist": dist,
                 "cambio": round(self._cambio, 2),
                 "incl": round(self._incl, 1),
                 "luz": self.luz.color_actual}
        if self.reed:
            datos["cerrojo"] = self.reed.texto()
        if self.lazo:
            datos["lazo"] = "CORTADO" if self.lazo.cortado() else "ENTERO"
        if self.pir:
            datos["pir"] = 1 if self.pir.hay_alguien() else 0
        self.red.publicar(b"bikesafe/sensores", json.dumps(datos))
        # Un topico por sensor (Tabla HAL del curso)
        if dist is not None:
            self.red.publicar(b"bikesafe/sensor/distancia", str(dist))
        self.red.publicar(b"bikesafe/sensor/movimiento", str(datos["cambio"]))
        self.red.publicar(b"bikesafe/sensor/inclinacion", str(datos["incl"]))
        if self.reed:
            self.red.publicar(b"bikesafe/sensor/cerrojo", datos["cerrojo"])
        if self.lazo:
            self.red.publicar(b"bikesafe/sensor/lazo", datos["lazo"])

    # ===========================================================
    #  CICLO PRINCIPAL
    # ===========================================================
    def vuelta(self):
        ahora = time.ticks_ms()
        medi = self._medir_distancia(ahora)

        if self.estado == ASEGURADA:
            self._revisar_movimiento(ahora)
        if self.estado == ASEGURADA:        # pudo cambiar a ALARMA arriba
            self._revisar_cerrojo(ahora)
        if self.estado == ASEGURADA:
            self._revisar_lazo(ahora)
        if self.estado == ASEGURADA:
            self._revisar_presencia(ahora, medi)
        if self.estado == ALARMA:
            self._revisar_rafaga(ahora)
            self._revisar_fin_alarma(ahora)
        if self.estado == LIBRE:
            self._cambio = 0.0
            self._incl = 0.0
        self._revisar_buscar(ahora)

        self._revisar_camara()
        self._revisar_red(ahora)

        # Cosas que parpadean o suenan solas
        self.buzzer.actualizar(ahora)
        self.luz.actualizar(ahora)

    def _activar_watchdog(self):
        """Si el programa se traba mas de 20 s, la placa se reinicia sola.
        OJO: una vez activo ya no se puede apagar; con Thonny la placa se
        reinicia a los 20 s de presionar STOP. Por eso viene en False y
        solo se activa para la exposicion (USAR_WATCHDOG en config.py)."""
        if not _cfg("USAR_WATCHDOG", False):
            return
        try:
            from machine import WDT
            self._wdt = WDT(timeout=20000)
            print(" + Watchdog activo (reinicio automatico)")
        except Exception as e:
            print(" ! Watchdog no disponible:", e)

    def correr(self):
        self._activar_watchdog()
        while True:
            if self._wdt:
                self._wdt.feed()
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
