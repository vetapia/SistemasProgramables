from machine import Pin
import time

# Pin GPIO del Maestro conectado por un cable Dupont al Esclavo
PIN_DISPARO = 4 

def main():
    # Configuramos como salida, inicialmente en 0 (LOW)
    gpio_disparo = Pin(PIN_DISPARO, Pin.OUT)
    gpio_disparo.value(0)

    print("\n--- MAESTRO: MOCKUP DE TECLADO ---")
    print("Presiona [1] en la consola y da Enter para enviar la orden a la Cámara.")
    print("Presiona [0] para salir.")

    while True:
        opcion = input("\nComando para la cámara: ")

        if opcion == '1':
            print("[MAESTRO] Enviando pulso de despertador a la Cámara...")
            
            # Mandamos un pulso en ALTO (HIGH) durante medio segundo
            gpio_disparo.value(1)
            time.sleep(0.5)
            
            # Regresamos el pin a BAJO (LOW)
            gpio_disparo.value(0)
            print("[MAESTRO] Pulso enviado con éxito.")
            
        elif opcion == '0':
            print("[MAESTRO] Saliendo...")
            break
        else:
            print("[MAESTRO] Opción no válida. Usa 1 para disparar.")

if __name__ == "__main__":
    main()