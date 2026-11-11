# ============================================
# Proyecto:  EcoClasifica
# Archivo:   main.py
# Objetivo:  Loop principal: publica sensores por MQTT y ejecuta comandos de actuadores.
# Equipo:    Franco Torres Rodríguez 23240410 / Tiquet Andrade Ariel Carolina 23241131
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

import time
from machine import Pin

import config
from red import Red
from hal.sensores import Sensores
from hal.actuadores import Actuadores

INTERVALO_PUBLICACION_MS = 2000

# Tópicos de comando (el payload es b"1" o b"0")
T_RELE = b"ecoclasifica/actuador/rele/cmd"
T_BUZZER = b"ecoclasifica/actuador/buzzer/cmd"
T_LED = b"ecoclasifica/actuador/led/cmd"
T_SERVOS = {
    b"ecoclasifica/actuador/servo_papel/cmd": "papel",
    b"ecoclasifica/actuador/servo_plastico/cmd": "plastico",
    b"ecoclasifica/actuador/servo_metal/cmd": "metal",
}

sensores = Sensores()
actuadores = Actuadores()
led = Pin(config.PIN_LED, Pin.OUT, value=0)


def on_mensaje(topico, msg):
    print("Comando:", topico, msg)
    encender = (msg == b"1")
    try:
        if topico == T_RELE:
            actuadores.rele(encender)
        elif topico == T_BUZZER:
            actuadores.buzzer(encender)
        elif topico == T_LED:
            led.value(1 if encender else 0)
        elif topico in T_SERVOS:
            tapa = T_SERVOS[topico]
            if encender:
                actuadores.abrir_tapa(tapa)
            else:
                actuadores.cerrar_tapa(tapa)
    except Exception as e:
        print("Error ejecutando comando:", e)


red = Red(on_mensaje, [T_RELE, T_BUZZER, T_LED] + list(T_SERVOS.keys()))

if red.conectar_wifi():
    print("WiFi OK, IP:", red.ip())
else:
    print("WiFi: no se pudo conectar (se reintentará en el loop)")

ultimo_pub = time.ticks_ms()
while True:
    sensores.actualizar()
    red.actualizar()

    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_pub) >= INTERVALO_PUBLICACION_MS:
        ultimo_pub = ahora

        distancia = sensores.leer_distancia()
        golpe = sensores.obtener_golpe()
        luz = sensores.obtener_luz()

        # -1 significa "sin lectura válida" (sensor desconectado o fuera de rango)
        d_txt = -1 if distancia is None else round(distancia, 1)
        g_txt = -1 if golpe is None else round(golpe, 2)

        red.publicar("ecoclasifica/sensor/distancia", d_txt)
        red.publicar("ecoclasifica/sensor/luz", luz)
        red.publicar("ecoclasifica/sensor/golpe", g_txt)
        print("Dist:", d_txt, "cm | Luz:", luz, "| Golpe:", g_txt, "g")

    time.sleep_ms(20)
