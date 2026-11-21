"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   hal.py
 Objetivo:  Encapsula las conexiones físicas y los controladores de sensores y actuadores mediante clases
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import time
from machine import Pin, ADC, PWM, SoftI2C, SPI, time_pulse_us


class MotorBanda:
    """Controla un motor DC mediante dos relevadores SPDT en inversión.

    El control es manual por pulsos. No hay posicionamiento automático en esta
    versión. La posición en centímetros sólo se estima después de calibrar
    cm_per_100ms en config.json.
    """

    def __init__(self, pin_rele_1, pin_rele_2, config):
        self.config = config
        self.rele1 = Pin(pin_rele_1, Pin.OUT, value=1)
        self.rele2 = Pin(pin_rele_2, Pin.OUT, value=1)
        self.active_low = bool(config.get("relay_active_low", True))
        self.enabled = bool(config.get("motor_enabled", False))
        self.stops_confirmed = bool(config.get("physical_stops_confirmed", False))
        self.center_confirmed = False
        self.emergency_latched = False
        self.direction = "stop"
        self.last_direction = None
        self.deadline = None
        self.pending_direction = None
        self.pending_duration_ms = 0
        self.pending_start = None
        self.pulse_count = 0
        self.position_offset_cm = None
        self.cm_per_100ms = config.get("cm_per_100ms", None)
        self.max_pulse_ms = int(config.get("motor_max_pulse_ms", 100))
        self.reverse_pause_ms = int(config.get("motor_reverse_pause_ms", 300))
        self.track_length_cm = float(config.get("track_length_cm", 19.0))
        self.carriage_length_cm = float(config.get("carriage_length_cm", 6.0))
        self.margin_cm = float(config.get("track_margin_cm", 0.5))
        self.max_offset_cm = max(0.0, (self.track_length_cm - self.carriage_length_cm) / 2.0 - self.margin_cm)
        self.forward_sign = int(config.get("motor_forward_sign", 1))
        self._write(False, False)

    def _level(self, on):
        if self.active_low:
            return 0 if on else 1
        return 1 if on else 0

    def _write(self, relay1_on, relay2_on):
        self.rele1.value(self._level(relay1_on))
        self.rele2.value(self._level(relay2_on))

    def detener(self):
        #Desenergiza ambos relevadores (estado de reposo NC/NC).
        self._write(False, False)
        self.direction = "stop"
        self.deadline = None
        self.pending_direction = None
        self.pending_start = None

    def fijar_centro(self):
        #Registra que el operador colocó físicamente el carro en la marca.
        self.detener()
        self.center_confirmed = True
        self.position_offset_cm = 0.0
        self.pulse_count = 0
        return True

    def emergencia(self):
        self.detener()
        self.emergency_latched = True

    def rearmar(self):
        self.detener()
        self.emergency_latched = False
        self.center_confirmed = False
        self.position_offset_cm = None
        self.pulse_count = 0

    def solicitar_pulso(self, direction, duration_ms=None):
        #Solicita un pulso no bloqueante. Devuelve (ok, mensaje).
        direction = str(direction).lower()
        if direction not in ("forward", "reverse"):
            return False, "Direccion no valida"
        if self.emergency_latched:
            return False, "Parada de emergencia enclavada"
        if not self.enabled:
            return False, "Motor deshabilitado en config.json"
        if not self.stops_confirmed:
            return False, "Confirme topes mecanicos antes de habilitar el motor"
        if not self.center_confirmed:
            return False, "Primero coloque el carro en la marca central y pulse C"
        if self.direction != "stop" or self.pending_direction is not None:
            return False, "Motor ocupado; espere a que termine el pulso"

        duration = self.max_pulse_ms if duration_ms is None else int(duration_ms)
        duration = max(50, min(self.max_pulse_ms, duration))

        # Límite virtual disponible sólo después de calibrar el desplazamiento.
        if self.cm_per_100ms is not None and self.position_offset_cm is not None:
            cm_pulse = float(self.cm_per_100ms) * (duration / 100.0)
            sign = self.forward_sign if direction == "forward" else -self.forward_sign
            proposed = self.position_offset_cm + (sign * cm_pulse)
            if abs(proposed) > self.max_offset_cm:
                return False, "Limite virtual alcanzado; no se mueve"

        now = time.ticks_ms()
        if self.last_direction and self.last_direction != direction:
            self.pending_direction = direction
            self.pending_duration_ms = duration
            self.pending_start = time.ticks_add(now, self.reverse_pause_ms)
            self.detener()
            # detener() cancela pending; restaurar la solicitud diferida.
            self.pending_direction = direction
            self.pending_duration_ms = duration
            self.pending_start = time.ticks_add(now, self.reverse_pause_ms)
            return True, "Cambio de sentido programado despues de pausa"

        self._start(direction, duration)
        return True, "Pulso iniciado"

    def _start(self, direction, duration_ms):
        if direction == "forward":
            self._write(True, False)
        else:
            self._write(False, True)
        self.direction = direction
        self.deadline = time.ticks_add(time.ticks_ms(), duration_ms)
        self.last_direction = direction
        self._active_duration_ms = duration_ms

    def actualizar(self):
        now = time.ticks_ms()
        if self.pending_direction is not None and time.ticks_diff(now, self.pending_start) >= 0:
            direction = self.pending_direction
            duration = self.pending_duration_ms
            self.pending_direction = None
            self.pending_start = None
            self._start(direction, duration)

        if self.deadline is not None and time.ticks_diff(now, self.deadline) >= 0:
            elapsed = self._active_duration_ms
            direction = self.direction
            self.detener()
            self.pulse_count += 1
            if self.cm_per_100ms is not None and self.position_offset_cm is not None:
                cm = float(self.cm_per_100ms) * (elapsed / 100.0)
                sign = self.forward_sign if direction == "forward" else -self.forward_sign
                self.position_offset_cm += sign * cm

    def estado(self):
        return {
            "direction": self.direction,
            "enabled": self.enabled,
            "center_confirmed": self.center_confirmed,
            "position_offset_cm": self.position_offset_cm,
            "pulse_count": self.pulse_count,
            "emergency_latched": self.emergency_latched
        }


class ReleVentilacion:
    #Controla conjuntamente ventilador y LEDs mediante un relevador.

    def __init__(self, pin, active_low=True):
        self.pin = Pin(pin, Pin.OUT, value=1 if active_low else 0)
        self.active_low = bool(active_low)
        self.encendido = False

    def set_on(self, on):
        self.encendido = bool(on)
        if self.active_low:
            self.pin.value(0 if self.encendido else 1)
        else:
            self.pin.value(1 if self.encendido else 0)

    def encender(self):
        self.set_on(True)

    def apagar(self):
        self.set_on(False)


class IndicadorListo:
    #Mueve el SG90 para mostrar u ocultar la bandera física de "LISTO".

    def __init__(self, pin, config):
        self.pwm = PWM(Pin(pin), freq=50)
        self.hidden_angle = int(config.get("servo_hidden_angle", 30))
        self.ready_angle = int(config.get("servo_ready_angle", 120))
        self.min_angle = int(config.get("servo_min_angle", 20))
        self.max_angle = int(config.get("servo_max_angle", 150))
        self.angle = None
        self.oculta()

    def mover_a(self, angle):
        angle = max(self.min_angle, min(self.max_angle, int(angle)))
        pulse_us = 700 + int((angle / 180.0) * 1600)
        if hasattr(self.pwm, "duty_u16"):
            self.pwm.duty_u16(int(pulse_us * 65535 / 20000))
        else:
            self.pwm.duty(int(pulse_us * 1023 / 20000))
        self.angle = angle
        return angle

    def mostrar_listo(self):
        return self.mover_a(self.ready_angle)

    def oculta(self):
        return self.mover_a(self.hidden_angle)

    def deinit(self):
        try:
            self.pwm.deinit()
        except Exception:
            pass


class Buzzer:
    #Buzzer activo alto con pitidos temporizados no bloqueantes.

    def __init__(self, pin, active_high=True):
        self.pin = Pin(pin, Pin.OUT, value=0 if active_high else 1)
        self.active_high = bool(active_high)
        self.deadline = None
        self.encendido = False

    def set_on(self, on):
        self.encendido = bool(on)
        level = 1 if self.encendido else 0
        if not self.active_high:
            level = 0 if self.encendido else 1
        self.pin.value(level)
        self.deadline = None

    def beep(self, duration_ms=180):
        self.set_on(True)
        self.deadline = time.ticks_add(time.ticks_ms(), max(40, int(duration_ms)))

    def actualizar(self):
        if self.deadline is not None and time.ticks_diff(time.ticks_ms(), self.deadline) >= 0:
            self.set_on(False)

    def apagar(self):
        self.set_on(False)


class SensorPresion:
    #Lee FSR402 mediante ADC con histéresis para presencia del talón.

    def __init__(self, pin, config):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        try:
            self.adc.width(ADC.WIDTH_12BIT)
        except Exception:
            pass
        self.press_threshold = int(config.get("fsr_threshold", 1000))
        self.release_threshold = int(config.get("fsr_release_threshold", 850))
        self.pressed = False
        self.last_raw = 0

    def leer(self):
        self.last_raw = self.adc.read()
        if self.pressed:
            if self.last_raw <= self.release_threshold:
                self.pressed = False
        elif self.last_raw >= self.press_threshold:
            self.pressed = True
        return {"raw": self.last_raw, "pressed": self.pressed}


class SensorDistancia:
    #HC-SR04, devuelve distancia en cm o None cuando no hay eco válido.

    def __init__(self, trig_pin, echo_pin, config):
        self.trig = Pin(trig_pin, Pin.OUT, value=0)
        self.echo = Pin(echo_pin, Pin.IN)
        self.timeout_us = int(config.get("ultrasonic_timeout_us", 30000))

    def leer_cm(self):
        self.trig.value(0)
        time.sleep_us(3)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)
        try:
            duration = time_pulse_us(self.echo, 1, self.timeout_us)
        except Exception:
            return None
        if duration <= 0:
            return None
        return round((duration * 0.0343) / 2.0, 2)


class SensorTemperatura:
    #Lee MLX90614 por I2C.

    MLX_ADDR = 0x5A
    REG_AMBIENT = 0x06
    REG_OBJECT1 = 0x07

    def __init__(self, i2c):
        self.i2c = i2c
        self.disponible = False
        try:
            self.disponible = self.MLX_ADDR in self.i2c.scan()
        except Exception:
            self.disponible = False

    def _read_register(self, register):
        data = self.i2c.readfrom_mem(self.MLX_ADDR, register, 3)
        raw = data[0] | (data[1] << 8)
        if raw == 0xFFFF:
            raise ValueError("Dato MLX90614 invalido")
        return round(raw * 0.02 - 273.15, 2)

    def leer(self):
        if not self.disponible:
            return {"available": False, "ambient_c": None, "object_c": None}
        try:
            ambient = self._read_register(self.REG_AMBIENT)
            obj = self._read_register(self.REG_OBJECT1)
            return {"available": True, "ambient_c": ambient, "object_c": obj}
        except Exception:
            return {"available": False, "ambient_c": None, "object_c": None}


class PantallaLCD:

    def __init__(self, driver):
        self.driver = driver

    def mostrar(self, line1="", line2=""):
        if self.driver is None:
            return
        try:
            self.driver.display(str(line1)[:16], str(line2)[:16])
        except Exception as exc:
            print("Error LCD:", exc)


class PantallaOLED:

    def __init__(self, driver):
        self.driver = driver

    def mostrar_lineas(self, lines):
        if self.driver is None:
            return
        try:
            self.driver.fill(0)
            self.driver.text("VISION DIA FOOT", 0, 0)
            y = 14
            for line in lines[:4]:
                self.driver.text(str(line)[:16], 0, y)
                y += 12
            self.driver.show()
        except Exception as exc:
            print("Error OLED:", exc)


class VisionDiaFootHAL:
    #Inicializa y agrupa todos los objetos de hardware.

    def __init__(self, config):
        self.config = config
        pins = config.get("pins", {})

        self.i2c = SoftI2C(
            sda=Pin(int(pins.get("i2c_sda", 21))),
            scl=Pin(int(pins.get("i2c_scl", 22))),
            freq=int(config.get("i2c_frequency", 100000))
        )
        try:
            self.i2c_devices = self.i2c.scan()
        except Exception:
            self.i2c_devices = []
        print("I2C detectados:", [hex(x) for x in self.i2c_devices])

        self.presion = SensorPresion(int(pins.get("fsr", 34)), config)
        self.distancia = SensorDistancia(
            int(pins.get("ultrasonic_trig", 14)),
            int(pins.get("ultrasonic_echo", 35)), config
        )
        self.temperatura = SensorTemperatura(self.i2c)

        self.motor_banda = MotorBanda(
            int(pins.get("motor_relay_1", 32)),
            int(pins.get("motor_relay_2", 33)), config
        )
        self.ventilacion = ReleVentilacion(
            int(pins.get("fan_relay", 26)),
            config.get("fan_relay_active_low", True)
        )
        self.bandera = IndicadorListo(int(pins.get("servo", 13)), config)
        self.buzzer = Buzzer(int(pins.get("buzzer", 25)), config.get("buzzer_active_high", True))

        self.lcd = PantallaLCD(self._init_lcd(config))
        self.oled = PantallaOLED(self._init_oled(config, pins))

        # Estado seguro al terminar inicialización.
        self.motor_banda.detener()
        self.ventilacion.apagar()
        self.bandera.oculta()
        self.buzzer.apagar()

    def _init_lcd(self, config):
        if not config.get("use_lcd", True):
            return None
        address = int(config.get("lcd_address", 0x27))
        if address not in self.i2c_devices:
            print("LCD no detectada en", hex(address))
            return None
        try:
            from lcd1602 import LCD1602
            return LCD1602(self.i2c, address, 16, 2)
        except Exception as exc:
            print("No se pudo inicializar LCD:", exc)
            return None

    def _init_oled(self, config, pins):
        if not config.get("use_oled", True):
            return None
        try:
            spi = SPI(
                2,
                baudrate=int(config.get("oled_spi_baudrate", 1000000)),
                polarity=0,
                phase=0,
                sck=Pin(int(pins.get("oled_sck", 18))),
                mosi=Pin(int(pins.get("oled_mosi", 23))),
                miso=Pin(int(pins.get("oled_miso_dummy", 39)))
            )
            dc = Pin(int(pins.get("oled_dc", 4)), Pin.OUT, value=0)
            res = Pin(int(pins.get("oled_res", 2)), Pin.OUT, value=1)
            cs_dummy = Pin(int(pins.get("oled_cs_dummy", 19)), Pin.OUT, value=1)
            from ssd1306 import SSD1306_SPI
            return SSD1306_SPI(128, 64, spi, dc, res, cs_dummy)
        except Exception as exc:
            print("OLED no disponible:", exc)
            return None

    def leer_sensores(self):
        pressure = self.presion.leer()
        distance = self.distancia.leer_cm()
        temperature = self.temperatura.leer()
        return {
            "fsr_raw": pressure["raw"],
            "pressure_ok": pressure["pressed"],
            "distance_cm": distance,
            "ambient_temp_c": temperature["ambient_c"],
            "object_temp_c": temperature["object_c"],
            "temperature_available": temperature["available"]
        }

    def actualizar_actuadores(self):
        self.motor_banda.actualizar()
        self.buzzer.actualizar()

    def apagar_salidas(self):
        self.motor_banda.detener()
        self.ventilacion.apagar()
        self.bandera.oculta()
        self.buzzer.apagar()
