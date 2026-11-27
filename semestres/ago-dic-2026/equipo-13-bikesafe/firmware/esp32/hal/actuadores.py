# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   hal/actuadores.py
# Objetivo:  Una clase por cada actuador (servo del cerrojo, buzzer,
#            LED RGB de estado) y el enlace UART con la placa de la camara
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================
#
# Los 3 actuadores del proyecto:
#   1. Cerrojo  -> servo SG90 que mueve el pasador del candado
#   2. Zumbador -> buzzer (activo o pasivo) para pitidos y sirena
#   3. Luz      -> LED RGB que cambia de color segun el estado
#                  (si todavia no tienen el RGB, funciona con los
#                   dos LEDs de antes: verde y rojo)

import time
from machine import Pin, PWM, UART


def _duty(pwm, valor_1023):
    """Pone el ciclo de trabajo con la funcion que tenga el firmware
    (duty_u16 en MicroPython nuevo, duty en el viejo)."""
    if hasattr(pwm, "duty_u16"):
        pwm.duty_u16(int(valor_1023) * 64)
    else:
        pwm.duty(int(valor_1023))


# ---------------------------------------------------------------
#  1. CERROJO (servomotor SG90)
# ---------------------------------------------------------------
class Cerrojo:
    """Mueve el pasador que traba el cable.

    Un servo se controla con pulsos 50 veces por segundo (50 Hz).
    El ANCHO del pulso le dice el angulo:
        0.5 ms -> 0 grados      2.5 ms -> 180 grados
    """

    def __init__(self, pin, angulo_abierto, angulo_cerrado):
        self._pwm = PWM(Pin(pin), freq=50)
        _duty(self._pwm, 0)                # 0 = servo relajado
        self._abierto = angulo_abierto
        self._cerrado = angulo_cerrado
        self.angulo = None                 # ultimo angulo que se mando

    def _mover(self, grados):
        grados = max(0, min(180, grados))
        # duty va de 0 a 1023. A 50 Hz cada ciclo dura 20 ms, asi que
        # 0.5 ms = 26 y 2.5 ms = 128.
        _duty(self._pwm, 26 + grados * 102 / 180)
        time.sleep_ms(600)                 # darle tiempo de llegar
        _duty(self._pwm, 0)                # relajar: no vibra ni gasta pila
        self.angulo = grados

    def cerrar(self):
        self._mover(self._cerrado)

    def abrir(self):
        self._mover(self._abierto)

    def a_grados(self, grados):
        self._mover(grados)


# ---------------------------------------------------------------
#  2. ZUMBADOR (buzzer)
# ---------------------------------------------------------------
class Zumbador:
    """Funciona con buzzer ACTIVO (suena solo con 3.3 V) o PASIVO
    (hay que generarle el tono con PWM). Se elige en
    config.BUZZER_ACTIVO. Si no saben cual es: el activo suena al
    conectarlo directo a 3.3 V; el pasivo solo hace 'clic'."""

    def __init__(self, pin, activo=True):
        self._activo = activo
        self._sirena = False
        self._fase = False
        self._cambio_ms = 0
        if activo:
            self._pin = Pin(pin, Pin.OUT, value=0)
            self._pwm = None
        else:
            self._pwm = PWM(Pin(pin), freq=2000)
            _duty(self._pwm, 0)

    @property
    def sonando(self):
        return self._sirena

    def encender(self, tono=2500):
        if self._activo:
            self._pin.value(1)
        else:
            self._pwm.freq(tono)
            _duty(self._pwm, 512)

    def apagar(self):
        if self._activo:
            self._pin.value(0)
        else:
            _duty(self._pwm, 0)

    def pitido(self, veces=1, ms=90, pausa=90, tono=2500):
        """Pitidos cortos. Detiene el programa un instante (es poco)."""
        for i in range(veces):
            self.encender(tono)
            time.sleep_ms(ms)
            self.apagar()
            if i < veces - 1:
                time.sleep_ms(pausa)

    # --- sirena SIN detener el programa ---
    def sirena(self, prendida):
        self._sirena = prendida
        if not prendida:
            self.apagar()

    def actualizar(self, ahora):
        """Llamar en cada vuelta del ciclo principal."""
        if not self._sirena:
            return
        if time.ticks_diff(ahora, self._cambio_ms) >= 180:
            self._cambio_ms = ahora
            self._fase = not self._fase
            if self._activo:
                # activo: prende/apaga rapido (bip-bip-bip)
                self._pin.value(1 if self._fase else 0)
            else:
                # pasivo: alterna dos tonos (ui-uu-ui-uu)
                self.encender(3200 if self._fase else 2200)


# ---------------------------------------------------------------
#  3. LUZ DE ESTADO (LED RGB)
# ---------------------------------------------------------------
# Cada color es la combinacion (rojo, verde, azul) de patitas prendidas.
COLORES = {
    "apagado":  (0, 0, 0),
    "rojo":     (1, 0, 0),
    "verde":    (0, 1, 0),
    "azul":     (0, 0, 1),
    "amarillo": (1, 1, 0),
    "morado":   (1, 0, 1),
    "cian":     (0, 1, 1),
    "blanco":   (1, 1, 1),
}


class LedRGB:
    """LED RGB de 4 patitas. Cada color se prende con su pin.

    Catodo comun: la patita larga va a GND y un pin en 1 prende el color.
    Anodo comun:  la patita larga va a 3.3 V y un pin en 0 prende el color.
    """

    def __init__(self, pin_r, pin_g, pin_b, anodo_comun=False):
        self._inv = anodo_comun
        apagado = 1 if anodo_comun else 0
        self._pines = [Pin(p, Pin.OUT, value=apagado)
                       for p in (pin_r, pin_g, pin_b)]

    def mostrar(self, color):
        for pin, prendido in zip(self._pines, COLORES.get(color, (0, 0, 0))):
            pin.value((1 - prendido) if self._inv else prendido)


class DosLeds:
    """Para cuando todavia no tienen el RGB: usa el LED verde y el rojo
    de antes. Los colores se 'traducen' a lo mas parecido."""

    _EQUIVALE = {"verde": (1, 0), "azul": (1, 0), "cian": (1, 0),
                 "rojo": (0, 1), "morado": (0, 1),
                 "amarillo": (1, 1), "blanco": (1, 1), "apagado": (0, 0)}

    def __init__(self, pin_verde, pin_rojo):
        self._verde = Pin(pin_verde, Pin.OUT, value=0)
        self._rojo = Pin(pin_rojo, Pin.OUT, value=0)

    def mostrar(self, color):
        v, r = self._EQUIVALE.get(color, (0, 0))
        self._verde.value(v)
        self._rojo.value(r)


class Luz:
    """Maneja el color del LED SIN detener el programa.

    Tiene 3 capas, de menor a mayor prioridad:
      - fondo:    el color del estado (fijo o parpadeando)
      - destello: un color por unos segundos (aviso, persona, ...)
    """

    def __init__(self, led):
        self._led = led
        self._color = "apagado"
        self._periodo = 0            # 0 = fijo
        self._encendido = True
        self._cambio_ms = 0
        self._destello = None        # (color, hasta_ms)
        self.color_actual = "apagado"
        self._mostrar("apagado")

    def _mostrar(self, color):
        if color != self.color_actual:
            self._led.mostrar(color)
            self.color_actual = color

    def fijo(self, color):
        self._color, self._periodo, self._encendido = color, 0, True
        if not self._destello:
            self._mostrar(color)

    def parpadear(self, color, periodo_ms):
        self._color, self._periodo = color, periodo_ms

    def destello(self, color, duracion_ms):
        self._destello = (color, time.ticks_add(time.ticks_ms(), duracion_ms))
        self._mostrar(color)

    def quitar_destello(self):
        self._destello = None

    def actualizar(self, ahora):
        if self._destello:
            color, hasta = self._destello
            if time.ticks_diff(ahora, hasta) < 0:
                self._mostrar(color)
                return
            self._destello = None
        if self._periodo:
            if time.ticks_diff(ahora, self._cambio_ms) >= self._periodo:
                self._cambio_ms = ahora
                self._encendido = not self._encendido
            self._mostrar(self._color if self._encendido else "apagado")
        else:
            self._mostrar(self._color)


# ---------------------------------------------------------------
#  ENLACE CON LA CAMARA (UART = 2 cables de datos + GND)
# ---------------------------------------------------------------
class EnlaceCamara:
    """Le manda renglones de texto a la Freenove:

        FOTO|ROBO|Movimiento continuo      -> toma foto y avisa
        MSG|Bici asegurada                 -> solo manda mensaje

    La Freenove contesta "OK|..." o "ERR|..." y tambien manda los
    botones del bot como "CMD|asegurar".
    """

    def __init__(self, tx, rx):
        self._uart = UART(2, baudrate=9600, tx=tx, rx=rx, timeout=0)
        self._pendiente = b""

    @staticmethod
    def _limpiar(texto):
        # Quitamos lo que romperia el formato del renglon
        return str(texto).replace("|", "/").replace("\r", " ")

    def pedir_foto(self, nivel, motivo):
        self._uart.write("FOTO|{}|{}\n".format(
            self._limpiar(nivel), self._limpiar(motivo).replace("\n", " ")))

    def mensaje(self, texto):
        # Los saltos de linea viajan como "~" (el enlace es por renglones)
        texto = self._limpiar(texto).replace("\n", "~")
        self._uart.write("MSG|{}\n".format(texto))

    def leer_respuesta(self):
        """Regresa un renglon completo de la camara o None."""
        dato = self._uart.read()
        if dato:
            self._pendiente += dato
            if len(self._pendiente) > 300:      # basura: tirar
                self._pendiente = b""
        if b"\n" in self._pendiente:
            renglon, self._pendiente = self._pendiente.split(b"\n", 1)
            try:
                return renglon.decode().strip()
            except Exception:
                return None
        return None
