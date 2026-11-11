from machine import Pin, PWM, ADC
import time
from dfplayer import DFPlayer

class Hal:
    def __init__(self, pin_servo=26, pin_pir=27, pin_ldr=32, pin_rf=14, pin_rele=25, tx_df=17, rx_df=16):
        # 1. Servomotor
        self.servo = PWM(Pin(pin_servo), freq=50)
        self.mover_servo(0)
        
        # 2. Relevador (Salida, Active LOW)
        self.rele = Pin(pin_rele, Pin.OUT)
        self.rele.value(1) # 1 es Apagado en lógica invertida
        
        # 3. Sensores Básicos (Entradas)
        self.pir = Pin(pin_pir, Pin.IN)
        self.adc_ldr = ADC(Pin(pin_ldr))
        self.adc_ldr.atten(ADC.ATTN_11DB)
        
        # 4. Módulo RF (Lectura normal / Polling)
        self.rf_btn = Pin(pin_rf, Pin.IN, Pin.PULL_DOWN)
        
        # 5. DFPlayer Mini
        self.df = DFPlayer(uart_id=1, tx_pin_id=tx_df, rx_pin_id=rx_df)
        time.sleep(0.5) 
        self.df.volume(20) 

    # --- MÉTODOS DE ACTUADORES ---
    def mover_servo(self, angulo):
        min_duty = 40
        max_duty = 115
        angulo_seguro = max(0, min(180, int(angulo))) 
        duty = int(min_duty + (angulo_seguro / 180) * (max_duty - min_duty))
        self.servo.duty(duty)

    def activar_rele(self, encender):
        self.rele.value(0 if encender else 1)

    def reproducir_audio(self):
        self.df.play(1, 1)

    def detener_audio(self):
        self.df.stop()

    # --- MÉTODOS DE SENSORES ---
    def leer_pir(self):
        return self.pir.value()

    def leer_ldr(self):
        return self.adc_ldr.read()

    def leer_rf(self):
        """Lectura digital cruda del botón RF. Retorna 1 o 0"""
        return self.rf_btn.value()


class Test:
    def __init__(self, hal_instance):
        """Recibe una instancia de la clase Hal ya inicializada."""
        self.hal = hal_instance

    def escanear_con_pir(self):
        """Mueve el servo y lee el PIR en cada posición."""
        print("Iniciando escaneo de movimiento (Radar PIR)...")
        
        # Secuencia de ángulos de ida y vuelta
        angulos = [0, 45, 90, 135, 180, 135, 90, 45]
        
        try:
            while True:
                for angulo in angulos:
                    # 1. Mover el servo
                    self.hal.mover_servo(angulo)
                    
                    # 2. Dar tiempo mecánico para que el servo llegue a la posición
                    time.sleep(0.5) 
                    
                    # 3. Leer el sensor PIR en esta posición
                    if self.hal.leer_pir() == 1:
                        print(f"[ALERTA] Movimiento detectado en el ángulo: {angulo}°")
                        # self.hal.reproducir_audio()
                    else:
                        print(f"Despejado en: {angulo}°")
                        
                    # 4. Esperar el resto del ciclo antes del siguiente movimiento
                    time.sleep(1.5) 
                    
        except KeyboardInterrupt:
            print("\nPrueba detenida por el usuario.")
            self.hal.mover_servo(0)


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == '__main__':
    print("Inicializando hardware...")
    mi_hardware = Hal()
    
    print("Iniciando clase Test...")
    prueba = Test(mi_hardware)
    
    # Ejecuta el escaneo sincronizado
    prueba.escanear_con_pir()