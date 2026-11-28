# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   cam/main.py
# Objetivo:  Servidor HTTP MJPEG en ESP32-CAM para transmitir flujo de video en tiempo real
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import network
import uasyncio as asyncio
import camera

try:
    from cam_config import WIFI_SSID, WIFI_PASSWORD
except ImportError:
    WIFI_SSID = ""
    WIFI_PASSWORD = ""

BOUNDARY = b"meowguardframe"
STREAM = (
    b"HTTP/1.1 200 OK\r\nConnection: close\r\nCache-Control: no-store\r\n"
    b"Content-Type: multipart/x-mixed-replace; boundary=" + BOUNDARY + b"\r\n\r\n"
)
active_streams = 0


async def reconnect(station):
    while True:
        if not station.isconnected():
            try:
                station.connect(WIFI_SSID, WIFI_PASSWORD)
                for _ in range(15):
                    if station.isconnected():
                        print("ESP32-CAM: http://" + station.ifconfig()[0] + "/stream")
                        break
                    await asyncio.sleep_ms(1000)
            except OSError as exc:
                print("Wi-Fi camara:", exc)
        await asyncio.sleep_ms(3000)


async def send(writer, status, mime, payload):
    writer.write(
        b"HTTP/1.1 " + status + b"\r\nContent-Type: " + mime +
        b"\r\nConnection: close\r\nCache-Control: no-store\r\nContent-Length: " +
        str(len(payload)).encode() + b"\r\n\r\n"
    )
    writer.write(payload)
    await asyncio.wait_for(writer.drain(), 3)


async def http(reader, writer):
    global active_streams
    streaming = False
    try:
        request = (await asyncio.wait_for(reader.readline(), 2)).split()
        if len(request) < 2 or request[0] != b"GET":
            return
        path = request[1]
        if path in (b"/", b"/snapshot"):
            image = camera.capture()
            if image:
                await send(writer, b"200 OK", b"image/jpeg", image)
            else:
                await send(writer, b"503 Service Unavailable", b"text/plain", b"Sin imagen")
        elif path == b"/stream" and active_streams == 0:
            active_streams += 1
            streaming = True
            writer.write(STREAM)
            await asyncio.wait_for(writer.drain(), 3)
            while True:
                image = camera.capture()
                if image:
                    header = (b"--" + BOUNDARY + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                              + str(len(image)).encode() + b"\r\n\r\n")
                    writer.write(header)
                    writer.write(image)
                    writer.write(b"\r\n")
                    await asyncio.wait_for(writer.drain(), 3)
                    image = None
                await asyncio.sleep_ms(130)
        elif path == b"/stream":
            await send(writer, b"503 Service Unavailable", b"text/plain", b"Stream ocupado")
        else:
            await send(writer, b"404 Not Found", b"text/plain", b"Usa /stream o /snapshot")
    except (OSError, asyncio.TimeoutError):
        pass
    finally:
        if streaming:
            active_streams -= 1
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), 1)
        except (OSError, asyncio.TimeoutError):
            pass


async def main():
    if not WIFI_SSID:
        raise ValueError("Configura WIFI_SSID y WIFI_PASSWORD en cam_config.py.")
    station = network.WLAN(network.STA_IF)
    station.active(True)
    initialized = camera.init(0, format=camera.JPEG, framesize=camera.FRAME_QVGA,
                              fb_location=camera.PSRAM)
    if initialized is False:
        raise OSError("No inicio la OV2640. Revisa PSRAM, alimentacion y flex.")
    task = asyncio.create_task(reconnect(station))
    server = await asyncio.start_server(http, "0.0.0.0", 80)
    try:
        while True:
            await asyncio.sleep_ms(10000)
    finally:
        task.cancel()
        server.close()
        camera.deinit()


if __name__ == "__main__":
    asyncio.run(main())
