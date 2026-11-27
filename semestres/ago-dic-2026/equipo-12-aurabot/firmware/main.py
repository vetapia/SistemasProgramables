# ============================================
# Proyecto:   AuraBot
# Archivo:    main.py
# Objetivo:   Bucle principal de telemetría y ejecución de comandos MQTT
# Equipo:    Sandoval Cuevas Pedro (23240325), Taboada Ramírez Salvador (23240999), Barroso Garcia Braulio Axel (23240327)
# Materia:    Sistemas Programables — ISC TecNM León
# Semestre:   ago-dic-2026
# ============================================

import time
import comunicacion
from hal import dispositivos as disp

def al_recibir_mensaje(topico, mensaje):
    topico_str = topico.decode("utf-8")
    msg_str = mensaje.decode("utf-8").strip().lower()
    print(f"MQTT [{topico_str}] -> {msg_str}")

    # Comandos para los 3 Servomotores (Cabeza + 2 Brazos)
    if topico_str == "aurabot/comando/servo/central":
        if msg_str == "saludar":
            disp.saludar_servos()
        elif msg_str == "respirar":
            disp.respirar_servos()
        elif msg_str == "reposo":
            disp.reposo_servos()

    # Comandos para Relevador (Luz ambiental)
    elif topico_str == "aurabot/comando/relevador/central":
        disp.controlar_relevador(msg_str)

    # Comandos para Pantalla OLED
    elif topico_str == "aurabot/comando/oled/central":
        disp.cambiar_oled(msg_str)

    # Comandos para DFPlayer Mini (Bocina)
    elif topico_str == "aurabot/comando/audio/central":
        if msg_str == "stop":
            disp.detener_audio()
        elif msg_str.isdigit():
            disp.reproducir_pista_mp3(int(msg_str))

# ============================================
# INICIALIZACIÓN DEL SISTEMA
# ============================================

print("Iniciando AuraBot...")
disp.reposo_servos()
disp.cambiar_oled("neutral")
time.sleep(1)
disp.set_volumen_dfplayer(20)

if comunicacion.conectar_wifi():
    cliente = comunicacion.iniciar_mqtt(al_recibir_mensaje)
    
    if cliente:
        # Suscripción adicional para el audio sin alterar comunicacion.py
        cliente.subscribe(b"aurabot/comando/audio/central")
        
        ultimo_envio = time.ticks_ms()
        
        while True:
            try:
                # Revisa si llegaron órdenes desde Python o MQTT Explorer
                cliente.check_msg()
                
                # Publica sensores cada 3 segundos
                if time.ticks_diff(time.ticks_ms(), ultimo_envio) > 3000:
                    pir_val = disp.leer_pir()
                    dist_val = disp.leer_distancia()
                    luz_val = disp.leer_luz()
                    
                    cliente.publish(b"aurabot/sensor/pir/central", str(pir_val).encode())
                    cliente.publish(b"aurabot/sensor/ultrasonico/central", str(dist_val).encode())
                    cliente.publish(b"aurabot/sensor/luz/central", str(luz_val).encode())
                    
                    ultimo_envio = time.ticks_ms()
                    
                time.sleep(0.05)
                
            except Exception as e:
                print("Error en bucle principal:", e)
                time.sleep(2)
