# ============================================
# Proyecto:  BikeSafe - Candado inteligente portatil
# Archivo:   hal/actuadores.py
# Objetivo:  Una clase por cada actuador (servo del cerrojo,
#            buzzer, LEDs) y el enlace con la placa de la camara
# Equipo:    Oscar Sandoval Cabrera (23240457),
#            Diego Josue Talamantes Santiago (23240355)
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import time
from machine import Pin, PWM, UART


# ---------------------------------------------------------------
#  CERROJO (servomotor SG90)
# ---------------------------------------------------------------
class Cerrojo:
    """Mueve el pestillo que traba el cable.

    Un servo se controla con pulsos 50 veces por segundo (50 Hz).
    El ANCHO del pulso le dice el angulo:
        0.5 ms -> 0 grados      2.5 ms -> 180 grados
    """

    def __init__(self, pin, angulo_abierto, angulo_cerrado):
        self._pwm = PWM(Pin(pin), freq=50, duty=0)   # duty 0 = servo relajado
        self._abierto = angulo_abierto
        self._cerrado = angulo_cerrado

    def _mover(self, grados):
        grados = max(0, min(180, grados))
        # duty va de 0 a 1023. A 50 Hz cada ciclo dura 20 ms, asi que
        # 0.5 ms = 26 y 2.5 ms = 128.
        self._pwm.duty(int(26 + grados * 102 / 180))
        time.sleep_ms(600)                # darle tiempo de llegar
        self._pwm.duty(0)                 # relajar: no vibra ni gasta pila

    def cerrar(self):
        self._mover(self._cerrado)

    def abrir(self):
        self._mover(self._abierto)

    def a_grados(self, grados):
        self._mover(grados)


# ---------------------------------------------------------------
#  ZUMBADOR (buzzer con transistor 2N2222)
# ---------------------------------------------------------------
class Zumbador:
    """Funciona con buzzer ACTIVO (suena solo) o PASIVO (hay que
    generarle el tono con PWM). Se elige en config.BUZZER_ACTIVO."""

    def __init__(self, pin, activo=True):
        self._activo = activo
        self._sirena = False
        self._fase = False
        self._cambio_ms = 0
        if activo:
            self._pin = Pin(pin, Pin.OUT, value=0)
            self._pwm = None
        else:
            self._pwm = PWM(Pin(pin), freq=2000, duty=0)

    def encender(self, tono=2500):
        if self._activo:
            self._pin.value(1)
        else:
            self._pwm.freq(tono)
            self._pwm.duty(512)

    def apagar(self):
        if self._activo:
            self._pin.value(0)
        else:
            self._pwm.duty(0)

    def pitido(self, veces=1, ms=90, pausa=90):
        """Pitidos cortos. Detiene el programa un instante (es poco)."""
        for i in range(veces):
            self.encender()
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
#  LED
# ---------------------------------------------------------------
class Led:
    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT, value=0)
        self._periodo = 0
        self._cambio_ms = 0

    def encender(self):
        self._periodo = 0
        self._pin.value(1)

    def apagar(self):
        self._periodo = 0
        self._pin.value(0)

    def parpadear(self, periodo_ms):
        """Parpadea solo, sin detener el programa."""
        self._periodo = periodo_ms

    def actualizar(self, ahora):
        if self._periodo and time.ticks_diff(ahora, self._cambio_ms) >= self._periodo:
            self._cambio_ms = ahora
            self._pin.value(0 if self._pin.value() else 1)


# ---------------------------------------------------------------
#  ENLACE CON LA CAMARA (UART = un cable de datos + GND)
# ---------------------------------------------------------------
class EnlaceCamara:
    """Le manda renglones de texto a la Freenove:

        FOTO|ROBO|Movimiento continuo      -> toma foto y avisa
        MSG|Bici asegurada                 -> solo manda mensaje

    La Freenove contesta "OK|..." o "ERR|...".
    """

    def __init__(self, tx, rx):
        self._uart = UART(2, baudrate=9600, tx=tx, rx=rx, timeout=0)
        self._pendiente = b""

    @staticmethod
    def _limpiar(texto):
        # Quitamos lo que romperia el formato del renglon
        return str(texto).replace("|", "/").replace("\n", " ")

    def pedir_foto(self, nivel, motivo):
        self._uart.write("FOTO|{}|{}\n".format(self._limpiar(nivel),
                                               self._limpiar(motivo)))

    def mensaje(self, texto):
        self._uart.write("MSG|{}\n".format(self._limpiar(texto)))

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
