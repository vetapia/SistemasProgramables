import network
import time
import ujson
import socket
from config import ajustes
from hal import BrazaleteHAL

# --- 1. CONFIGURACIÓN DE RED Y UDP ---
SSID = ajustes.ssid
PASSWORD = ajustes.password
PC_IP = ajustes.pc_ip
PC_PORT = ajustes.pc_port


def conectar_wifi(hw):
    hw.set_color(255, 128, 0)  # Amarillo mientras conecta
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    try:
        wlan.config(pm=wlan.PM_NONE)
    except Exception:
        pass
    
    if not wlan.isconnected():
        print("Conectando a WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print(".", end="")
    print("\nWiFi conectado. IP:", wlan.ifconfig()[0])
    hw.set_color(0, 255, 0)    # Verde al conectar
    hw.tocar_tono(880, 120)


# --- 2. ARRANQUE ---
hw = BrazaleteHAL()
conectar_wifi(hw)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

hw.calibrar_centro()

# --- 3. BUCLE PRINCIPAL (20 FPS) ---
while True:
    try:
        hw.actualizar()

        # Leer sensores desde hal.py
        inclinacion = hw.leer_inclinacion()
        flex1 = hw.leer_flex1()

        # Enviar paquete JSON a GameMaker
        payload = ujson.dumps({
            "inclinacion": round(inclinacion, 3),
            "flex1": round(flex1, 3)
        })
        try:
            udp_socket.sendto(payload.encode("utf-8"), (PC_IP, PC_PORT))
            print(f"Inclinación: {inclinacion:>6.3f} | Flex Crudo: {hw.flex1_crudo:4d} | Flex Final: {flex1:.3f}")
        except OSError:
            pass  # Si el búfer Wi-Fi está ocupado un instante, salta este frame sin trabarse

        

    except Exception as e:
        hw.set_color(255, 0, 0)  # Rojo si ocurre un error
        print("Error en el bucle:", e)
        if not network.WLAN(network.STA_IF).isconnected():
            conectar_wifi(hw)

    time.sleep(0.05)
