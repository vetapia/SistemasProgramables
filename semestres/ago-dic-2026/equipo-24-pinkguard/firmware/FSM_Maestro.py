import time

class FSM_Maestro:
    ESTADO_BOOTEO = "BOOTEO"
    ESTADO_ESPERA = "ESPERA"
    ESTADO_ALERTA = "ALERTA"

    def __init__(self, hal, mqtt_manager, modelo):
        self.hal = hal
        self.mqtt = mqtt_manager
        self.modelo = modelo
        self.estado_actual = self.ESTADO_BOOTEO
        
        self.tiempo_inicio_alerta = 0
        self.tiempo_ultimo_audio = 0
        self.tiempo_fase_servo = 0
        
        self.angulos_servo = [0, 45, 90, 135, 180, 135, 90, 45]
        self.indice_angulo = 0
        self.fase_escaneo = "ESPERANDO"
        self.rf_ultimo_estado = 0

        print(f"[FSM] Sistema arrancó en estado: {self.estado_actual}")

    def _postear_estado(self, disparador):
        payload = f"Trig:{disparador}|PIR:{self.modelo.pir_valor}|LDR:{self.modelo.ldr_valor}|RF:{self.modelo.rf_presionado}|Rele:{self.modelo.rele_estado}|Servo:{self.modelo.servo_angulo}"
        print(f"\n[SIMULACIÓN MQTT] Posteando estado -> {payload}")
        self.mqtt.postear_dato("pinkguard/estado", payload)

    def _tomar_foto_esclavo(self):
        print("[SIMULACIÓN CÁMARA] ¡Enviando pulso al ESP32 Esclavo para FOTO!")
        from machine import Pin
        pin_disparo = Pin(4, Pin.OUT)
        pin_disparo.value(1)
        time.sleep(0.5)
        pin_disparo.value(0)

    def transicionar(self, nuevo_estado):
        print(f"\n[FSM] Transicionando: [{self.estado_actual}] ---> [{nuevo_estado}]")
        self.estado_actual = nuevo_estado
        
        if self.estado_actual == self.ESTADO_ALERTA:
            self.tiempo_inicio_alerta = time.time()
            
            # 1. LDR: Lectura ÚNICA
            self.modelo.ldr_valor = self.hal.leer_ldr()
            print(f"[ALERTA-INIT] Lectura LDR capturada: {self.modelo.ldr_valor}")
            
            # 2. Relé: Activar físicamente
            self.modelo.rele_estado = True
            self.hal.activar_rele(True)
            print("[ALERTA-INIT] Relé Activado.")
            
            # 3. Bocina: Iniciar
            self.modelo.bocina_estado = True
            self.tiempo_ultimo_audio = time.time() - 20 
            
            # 4. Radar PIR: Reiniciar secuencia y mover físicamente
            self.indice_angulo = 0
            self.modelo.servo_angulo = self.angulos_servo[self.indice_angulo]
            self.fase_escaneo = "MOVIENDO"
            self.tiempo_fase_servo = time.ticks_ms()
            self.hal.mover_servo(self.modelo.servo_angulo)
            print(f"[ALERTA-INIT] Servo movido a {self.modelo.servo_angulo}°")

        elif self.estado_actual == self.ESTADO_ESPERA:
            # Apagar actuadores físicamente al volver a ESPERA
            self.modelo.rele_estado = False
            self.modelo.bocina_estado = False
            self.modelo.servo_angulo = 0
            
            self.hal.activar_rele(False)
            self.hal.detener_audio()
            self.hal.mover_servo(0)
            print("[ESPERA-INIT] Actuadores apagados y reseteados.")

    def actualizar(self):
        if self.estado_actual == self.ESTADO_BOOTEO:
            print("[BOOTEO] Verificando sistemas...")
            exito_mqtt = self.mqtt.iniciar_comunicacion()
            if exito_mqtt:
                self.transicionar(self.ESTADO_ESPERA)
            else:
                time.sleep(3)

        elif self.estado_actual == self.ESTADO_ESPERA:
            lectura_rf = self.hal.leer_rf()
            self.modelo.rf_presionado = lectura_rf
            
            # Detecta si se presiona el RF para ENTRAR a la alerta
            if lectura_rf == 1 and self.rf_ultimo_estado == 0:
                print(f"[ESPERA] ¡RF detectado! Iniciando alerta...")
                self.transicionar(self.ESTADO_ALERTA)
            elif lectura_rf == 0:
                time.sleep(0.1)
                
            self.rf_ultimo_estado = lectura_rf

        elif self.estado_actual == self.ESTADO_ALERTA:
        # --- TAREA 1: RF (SALIR DE LA ALERTA) ---
            lectura_rf = self.hal.leer_rf()
            self.modelo.rf_presionado = lectura_rf
            
            if lectura_rf == 1 and self.rf_ultimo_estado == 0:
                print("\n[ALERTA] ¡Señal RF recibida! Cancelando alerta...")
                self._postear_estado("RF_CANCEL")
                self.rf_ultimo_estado = lectura_rf
                self.transicionar(self.ESTADO_ESPERA)
                return
            
            self.rf_ultimo_estado = lectura_rf

            # --- TAREA 2: BUCLE DE AUDIO (Físico) ---
            if time.time() - self.tiempo_ultimo_audio >= 10:
                print("[ALERTA] Bucle de Audio: Reproduciendo pista...")
                self.hal.reproducir_audio()
                self.tiempo_ultimo_audio = time.time()

            # --- TAREA 3 (INDEPENDIENTE): MONITOREO CONSTANTE DEL PIR ---
            # Leemos el PIR en cada ciclo de la FSM
            pir_actual = self.hal.leer_pir()
            
            # Si detecta movimiento (1) y antes estaba en reposo (0)
            if pir_actual == 1 and self.modelo.pir_valor == 0:
                self.modelo.pir_valor = 1
                angulo_actual = self.angulos_servo[self.indice_angulo]
                print(f"\n   --> ¡Movimiento independiente detectado en {angulo_actual}°!")
                self._postear_estado("PIR_DETECCION")
                self._tomar_foto_esclavo()
            elif pir_actual == 0:
                self.modelo.pir_valor = 0

            # --- TAREA 4: COREOGRAFÍA DEL SERVO (NUNCA SE DETIENE) ---
            tiempo_actual_ms = time.ticks_ms()
            diferencia_ms = time.ticks_diff(tiempo_actual_ms, self.tiempo_fase_servo)

            if self.fase_escaneo == "MOVIENDO":
                if diferencia_ms >= 500:
                    self.fase_escaneo = "ESPERANDO"
                    self.tiempo_fase_servo = time.ticks_ms()

            elif self.fase_escaneo == "ESPERANDO":
                if diferencia_ms >= 1500:
                    self.indice_angulo = (self.indice_angulo + 1) % len(self.angulos_servo)
                    self.modelo.servo_angulo = self.angulos_servo[self.indice_angulo]
                    
                    # El servo se mueve de forma fluida sin importar el PIR
                    self.hal.mover_servo(self.modelo.servo_angulo)
                    
                    self.fase_escaneo = "MOVIENDO"
                    self.tiempo_fase_servo = time.ticks_ms()
