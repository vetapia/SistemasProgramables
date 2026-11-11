from HAL import Hal
import time

class TestBocina:
    def __init__(self):
        print("[TEST] Inicializando hardware (HAL)...")
        self.hal = Hal()
        # Le damos un poco más de tiempo al DFPlayer para arrancar
        time.sleep(2) 
        
    def ejecutar_prueba(self):
        print("\n==== INICIANDO PRUEBA DE DFPLAYER MINI ====")
        
        print("1. Configurando volumen a 25...")
        self.hal.df.volume(25)
        time.sleep(1)
        
        print("2. Enviando comando de reproducción (Pista 1)...")
        self.hal.reproducir_audio()
        
        print("3. Esperando 10 segundos para que escuches el audio...")
        for i in range(10, 0, -1):
            print(f"   -> Sonando... {i}s")
            time.sleep(1)
            
        print("4. Enviando comando de detener...")
        self.hal.detener_audio()
        print("==== PRUEBA FINALIZADA ====")

if __name__ == '__main__':
    prueba = TestBocina()
    prueba.ejecutar_prueba()