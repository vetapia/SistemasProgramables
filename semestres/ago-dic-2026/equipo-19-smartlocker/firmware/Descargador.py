# ============================================================
# Descargador.py
# Conecta a una de las redes de configuracion.py e instala umqtt.simple.
# Ejecutar manualmente desde Thonny si la libreria no esta instalada.
# ============================================================

import network
import time
import configuracion

TIEMPO_ESPERA_WIFI_S = configuracion.TIEMPO_ESPERA_WIFI_S


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Wi-Fi ya conectado. IP:", wlan.ifconfig()[0])
        return wlan

    for ssid, password in configuracion.WIFI_REDES:
        if not ssid or ssid.startswith("NOMBRE_WIFI_"):
            continue
        if password is None:
            password = ""
        if password.startswith("CONTRASENA_WIFI_") or password == "CONTRASENA_HOTSPOT":
            continue

        print("Conectando a:", ssid)
        try:
            wlan.disconnect()
        except Exception:
            pass
        try:
            wlan.connect(ssid, password)
        except Exception as e:
            print("No se pudo iniciar conexión:", e)
            continue

        inicio = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), inicio) >= TIEMPO_ESPERA_WIFI_S * 1000:
                print("Tiempo agotado para:", ssid)
                break
            time.sleep(0.25)

        if wlan.isconnected():
            print("Wi-Fi conectado. IP:", wlan.ifconfig()[0])
            return wlan

    print("No se pudo conectar a las redes configuradas.")
    return None


def instalar_umqtt():
    try:
        import mip
    except ImportError:
        print("El firmware no incluye mip.")
        print("Actualiza MicroPython o instala umqtt.simple con Thonny/mpremote.")
        return False

    try:
        print("Instalando umqtt.simple...")
        mip.install("umqtt.simple")
        print("Instalación finalizada. Prueba: from umqtt.simple import MQTTClient")
        return True
    except Exception as e:
        print("No se pudo instalar umqtt.simple:", e)
        print("Verifica el acceso a Internet y vuelve a intentarlo.")
        return False


def main():
    wlan = conectar_wifi()
    if wlan is None:
        return
    instalar_umqtt()


main()

