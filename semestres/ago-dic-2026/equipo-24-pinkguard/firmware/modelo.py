class Modelo:
    def __init__(self):
        # --- ESTADOS DE LOS SENSORES
        self.pir_valor = -1         # -1: Sin leer, 0: Sin movimiento, 1: Movimiento
        self.ldr_valor = -1         # -1: Sin leer, Rango 0 a 4095
        self.rf_presionado = 0      # 0: No presionado, 1: Presionado

        # --- ESTADOS DE LOS ACTUADORES 
        self.servo_angulo = 0       # 0 a 180 grados
        self.rele_estado = False    # False = OFF, True = ON
        self.bocina_estado = False  # False = STOP, True = PLAY