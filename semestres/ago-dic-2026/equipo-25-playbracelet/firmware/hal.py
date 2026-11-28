import time
import math
from machine import Pin, I2C, ADC, PWM
from MPU6050 import MPU6050


class BrazaleteHAL:
    def __init__(self):
        # --- Parámetros de calibración ---
        self.MAX_INCLINACION_GRADOS = 45.0
        self.ZONA_MUERTA_GRADOS = 4.0

        self.VALOR_PLANO = 150
        self.VALOR_DOBLADO = 800
        self.SUAVIZADO = 0.15

        # --- Inicialización de Sensores ---
        self.i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        self.mpu = MPU6050(self.i2c)

        self.sensor_flex1 = ADC(Pin(32))
        self.sensor_flex1.atten(ADC.ATTN_11DB)
        self.sensor_flex1.width(ADC.WIDTH_12BIT)

        # --- Inicialización de Actuadores ---
        self.led_r = PWM(Pin(25), freq=1000, duty=0)
        self.led_g = PWM(Pin(26), freq=1000, duty=0)
        self.led_b = PWM(Pin(27), freq=1000, duty=0)

        self.buzzer = PWM(Pin(16), freq=1000, duty=0)
        self._buzzer_apagar_en = 0

        # --- Estados internos ---
        self.angulo_cero = 0.0
        self.flex1_crudo = self.sensor_flex1.read()
        self._flex1_suavizado = float(self.flex1_crudo)

    # ================= SENSORES =================
    def _leer_angulo_crudo(self):
        acel = self.mpu.read_accel_data(g=True)
        return math.atan2(acel["y"], acel["z"]) * (180.0 / math.pi)

    def calibrar_centro(self, muestras=30):
        print("Mantén el brazo en posición neutra (centro)...")
        suma = 0.0
        for _ in range(muestras):
            suma += self._leer_angulo_crudo()
            time.sleep(0.02)
        self.angulo_cero = suma / muestras
        print(f"Centro calibrado en: {self.angulo_cero:.1f}°")

    def leer_inclinacion(self):
        angulo_actual = self._leer_angulo_crudo()
        delta = (angulo_actual - self.angulo_cero + 180.0) % 360.0 - 180.0

        if abs(delta) < self.ZONA_MUERTA_GRADOS:
            return 0.0

        inclinacion = delta / self.MAX_INCLINACION_GRADOS
        return max(-1.0, min(1.0, inclinacion))

    def leer_flex1(self):
        self.flex1_crudo = self.sensor_flex1.read()
        self._flex1_suavizado = (self.SUAVIZADO * self.flex1_crudo) + ((1.0 - self.SUAVIZADO) * self._flex1_suavizado)

        flexion = (self._flex1_suavizado - self.VALOR_PLANO) / (self.VALOR_DOBLADO - self.VALOR_PLANO)
        return max(0.0, min(1.0, flexion)) * 100.0

    # ================= ACTUADORES =================
    def set_color(self, r, g, b):
        # Compensa el rojo al 35% para equilibrar las resistencias de 220 ohms
        self.led_r.duty(int((r / 255) * 1023))
        self.led_g.duty(int((g / 255) * 1023))
        self.led_b.duty(int((b / 255) * 1023))

    def tocar_tono(self, frecuencia, duracion_ms):
        self.buzzer.freq(frecuencia)
        self.buzzer.duty(512)
        self._buzzer_apagar_en = time.ticks_add(time.ticks_ms(), duracion_ms)

    def actualizar(self):
        # Apaga el buzzer cuando vence su tiempo sin detener el ciclo principal
        if self.buzzer.duty() > 0 and time.ticks_diff(time.ticks_ms(), self._buzzer_apagar_en) >= 0:
            self.buzzer.duty(0)
