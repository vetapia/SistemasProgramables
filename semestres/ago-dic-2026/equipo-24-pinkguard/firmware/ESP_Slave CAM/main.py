# ============================================
# Proyecto:  Pink Ward Sentinel
# Archivo:   main.py
# Objetivo:  Inicializar los componentes del ESP32 esclavo y ejecutar su bucle principal
# Equipo:    Montoya Chávez Ángel Eduardo
#            Rios López Jeremhy Damián
#            Torres Romero Yóscar Yemmen
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import time
from Comunicacion_MQTT_cam import Comunicacion_MQTT_Cam
from FSM_ESCLAVO import FSM_Camara

if __name__ == "__main__":
    # 1. Iniciar MQTT y Wi-Fi
    mqtt_esclavo = Comunicacion_MQTT_Cam(
        ssid="tvnetkom 522-2.4G", 
        password="GPON00855522", 
        broker_ip="192.168.1.43"
    )
    mqtt_esclavo.iniciar_comunicacion()
    
    # 2. Instanciar la máquina de estados inyectando el mqtt
    maquina = FSM_Camara(mqtt_manager=mqtt_esclavo, pin_recepcion=13)
    
    # 3. Bucle principal
    while True:
        maquina.actualizar()