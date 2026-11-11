from HAL import Hal
from FSM_Maestro import FSM_Maestro
from Modelo import Modelo
from Comunicacion_MQTT import Comunicacion_MQTT
import time

def main():
    print("\n========================================")
    print(" INICIANDO FIRMWARE - MAESTRO (PRUEBA) ")
    print("========================================")
    
    # 1. Instanciar Hardware (HAL)
    print("[MAIN] Cargando HAL...")
    hal = Hal()
    
    # 2. Instanciar el simulador en lugar de la red real
    print("[MAIN] Omitiendo red real. Usando simulador MQTT...")
    """
    mqtt = Comunicacion_MQTT("tvnetkom 522-2.4G",
                             "GPON00855522",
                             "192.168.1.46",
                             "PinkGuard_Maestro")
                             """
    mqtt = Comunicacion_MQTT("iPhone de Yoscar",
                             "yoscar12",
                             "172.20.10.2",
                             "PinkGuard_Maestro")
    modelo_estado = Modelo()
    
    # 3. Instanciar la Máquina de Estados pasándole las dependencias
    fsm = FSM_Maestro(hal, mqtt, modelo_estado)
    
    # 4. Bucle principal del sistema
    while True:
        fsm.actualizar()

if __name__ == "__main__":
    main()