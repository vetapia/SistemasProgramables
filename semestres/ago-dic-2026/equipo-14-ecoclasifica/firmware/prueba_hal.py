# ============================================
# Proyecto:  EcoClasifica
# Archivo:   prueba_hal.py
# Objetivo:  Prueba aislada (sin WiFi ni MQTT) de los 3 sensores y 3 actuadores antes de integrar.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
# Solo para pruebas: aquí sí se usa time.sleep porque no es el loop del proyecto.

import time
from hal.sensores import Sensores
from hal.actuadores import Actuadores

sensores = Sensores()
actuadores = Actuadores()


def esperar(ms):
    """Espera ms milisegundos sin dejar de actualizar los sensores."""
    inicio = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), inicio) < ms:
        sensores.actualizar()
        time.sleep_ms(10)


print("--- 1/6 LDR: tapa y destapa el sensor (10 lecturas) ---")
for _ in range(10):
    print("LDR =", sensores.obtener_luz(), "(0 = luz, 1 = oscuridad)")
    esperar(400)

print("--- 2/6 HC-SR04: acerca y aleja la mano (15 lecturas) ---")
for _ in range(15):
    d = sensores.leer_distancia()
    print("Distancia =", "sin lectura" if d is None else "{:.1f} cm".format(d))
    esperar(400)

print("--- 3/6 MPU6050: dale un golpecito a la protoboard (15 lecturas) ---")
for _ in range(15):
    pico = sensores.obtener_golpe()
    if pico is None:
        print("MPU6050 desconectado (revisa SDA/SCL/VCC/GND)")
    else:
        print("Golpe (pico) = {:.2f} g".format(pico))
    esperar(400)

print("--- 4/6 Servos: cada tapa abre y cierra ---")
for nombre in ('papel', 'plastico', 'metal'):
    print("Tapa", nombre, "-> abierta")
    actuadores.abrir_tapa(nombre)
    esperar(1200)
    print("Tapa", nombre, "-> cerrada")
    actuadores.cerrar_tapa(nombre)
    esperar(1200)

print("--- 5/6 Buzzer: debe sonar 1 segundo ---")
actuadores.buzzer(True)
esperar(1000)
actuadores.buzzer(False)
print("Si sonó al revés (suena en reposo y se calla al 'encender'), cambia BUZZER_ACTIVO_BAJO en config.py")

print("--- 6/6 Relé: 2 clics ---")
for _ in range(2):
    actuadores.rele(True)
    esperar(800)
    actuadores.rele(False)
    esperar(800)
print("Si el relé hace clic al arrancar y se suelta al 'encender', cambia RELE_ACTIVO_BAJO en config.py")

print("--- Prueba completa ---")

