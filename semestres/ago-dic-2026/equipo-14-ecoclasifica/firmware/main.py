# ============================================
# Proyecto:  EcoClasifica
# Archivo:   main.py
# Objetivo:  Flujo principal MQTT, lectura de sensores y control de actuadores
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import time
from machine import Pin
from red import conecta_wifi, conecta_mqtt
import config
import hal.sensores as sensores

# Inicializar actuadores físicos
rele = Pin(config.PIN_RELE, Pin.OUT)
buzzer = Pin(config.PIN_BUZZER, Pin.OUT)
led_integrado = Pin(config.PIN_LED, Pin.OUT)

def set_actuador(pin_obj, estado, activo_bajo):
    if activo_bajo:
        pin_obj.value(0 if estado else 1)
    else:
        pin_obj.value(1 if estado else 0)

def mqtt_callback(topic, msg):
    topico = topic.decode('utf-8')
    mensaje = msg.decode('utf-8')
    print(f"Comando recibido - Tópico: {topico}, Mensaje: {mensaje}")
    
    # Actuadores físicos
    if topico == "ecoclasifica/actuador/rele/cmd":
        set_actuador(rele, int(mensaje), config.RELE_ACTIVO_BAJO)
    elif topico == "ecoclasifica/actuador/buzzer/cmd":
        set_actuador(buzzer, int(mensaje), config.BUZZER_ACTIVO_BAJO)
    elif topico == "ecoclasifica/actuador/led/cmd":
        led_integrado.value(int(mensaje))
        
    # Simulación de compuertas (Servos)
    elif topico == "ecoclasifica/actuador/servo_papel/cmd":
        print(f">>> SIMULACIÓN: Abriendo compuerta PAPEL a {mensaje} grados (Servo no conectado)")
    elif topico == "ecoclasifica/actuador/servo_plastico/cmd":
        print(f">>> SIMULACIÓN: Abriendo compuerta PLÁSTICO a {mensaje} grados (Servo no conectado)")
    elif topico == "ecoclasifica/actuador/servo_metal/cmd":
        print(f">>> SIMULACIÓN: Abriendo compuerta METAL a {mensaje} grados (Servo no conectado)")

def main():
    conecta_wifi()
    cliente = conecta_mqtt(mqtt_callback)
    
    # Suscripciones
    cliente.subscribe("ecoclasifica/actuador/rele/cmd")
    cliente.subscribe("ecoclasifica/actuador/buzzer/cmd")
    cliente.subscribe("ecoclasifica/actuador/led/cmd")
    cliente.subscribe("ecoclasifica/actuador/servo_papel/cmd")
    cliente.subscribe("ecoclasifica/actuador/servo_plastico/cmd")
    cliente.subscribe("ecoclasifica/actuador/servo_metal/cmd")
    print("Suscrito a tópicos de actuadores.")

    ultimo_envio = time.ticks_ms()
    
    while True:
        cliente.check_msg()
        
        if time.ticks_diff(time.ticks_ms(), ultimo_envio) > 2000:
            # Leer sensores
            distancia = sensores.leer_distancia()
            luz = sensores.leer_ldr()
            golpe = sensores.leer_mpu()
            
            # Publicar datos
            cliente.publish("ecoclasifica/sensor/distancia", str(distancia))
            cliente.publish("ecoclasifica/sensor/luz", str(luz))
            cliente.publish("ecoclasifica/sensor/golpe", str(golpe))
            
            print(f"Publicado -> Distancia: {distancia}cm, Luz: {luz}, Golpe: {golpe}g")
            ultimo_envio = time.ticks_ms()
            
        time.sleep(0.1)

if __name__ == "__main__":
    main()