# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   mqtt.py
# Objetivo:  Cliente MQTT 3.1.1 asíncrono para publicar telemetría y recibir alertas de plagas
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import asyncio
import json

import config as cfg

DETECTIONS = b"meowguard/detections"
TELEMETRY = b"meowguard/telemetry"


def field(value):
    if isinstance(value, str):
        value = value.encode()
    return bytes((len(value) >> 8, len(value) & 255)) + value


def packet(header, body=b""):
    size = len(body)
    length = bytearray()
    while size >= 128:
        length.append((size & 127) | 128)
        size >>= 7
    length.append(size)
    return bytes((header,)) + bytes(length) + body


async def receive(reader):
    header = (await reader.readexactly(1))[0]
    size = 0
    shift = 0
    for _ in range(4):
        value = (await reader.readexactly(1))[0]
        size += (value & 127) << shift
        if not value & 128:
            break
        shift += 7
    else:
        raise ValueError("Longitud MQTT invalida")
    if size > 3072:
        raise ValueError("Mensaje MQTT demasiado grande")
    return header, await reader.readexactly(size) if size else b""


async def transmit(writer, data):
    writer.write(data)
    await asyncio.wait_for(writer.drain(), 3)


async def publish_status(writer, robot):
    try:
        count = 0
        while True:
            payload = json.dumps(robot.status()).encode()
            await transmit(writer, packet(0x30, field(TELEMETRY) + payload))
            count = (count + 1) % 3
            if count == 0:
                await transmit(writer, b"\xc0\x00")
            await asyncio.sleep_ms(2000)
    finally:
        writer.close()


async def run(station, robot):
    if not cfg.MQTT_HOST:
        return
    while True:
        if not station.isconnected():
            await asyncio.sleep_ms(1500)
            continue
        writer = None
        telemetry = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(cfg.MQTT_HOST, cfg.MQTT_PORT), 4)
            payload = field(cfg.MQTT_CLIENT_ID)
            flags = 2
            if cfg.MQTT_USER:
                flags |= 0x80
                payload += field(cfg.MQTT_USER)
                if cfg.MQTT_PASSWORD:
                    flags |= 0x40
                    payload += field(cfg.MQTT_PASSWORD)
            connect = b"\x00\x04MQTT\x04" + bytes((flags, 0, 15))
            await transmit(writer, packet(0x10, connect + payload))
            if await asyncio.wait_for(receive(reader), 4) != (0x20, b"\x00\x00"):
                raise OSError("El broker rechazo la conexion")
            await transmit(writer, packet(0x82, b"\x00\x01" + field(DETECTIONS) + b"\x00"))
            header, result = await asyncio.wait_for(receive(reader), 4)
            if header != 0x90 or result != b"\x00\x01\x00":
                raise OSError("El broker rechazo la suscripcion")
            robot.mqtt = True
            telemetry = asyncio.create_task(publish_status(writer, robot))
            while station.isconnected():
                header, body = await asyncio.wait_for(receive(reader), 12)
                if header >> 4 != 3 or (header >> 1) & 3 or len(body) < 2:
                    continue
                length = (body[0] << 8) + body[1]
                if body[2:2 + length] == DETECTIONS:
                    try:
                        item = json.loads(body[2 + length:].decode())
                        if isinstance(item, dict) and isinstance(item.get("label"), str):
                            robot.last_detection = item["label"][:48]
                    except ValueError:
                        pass
        except (OSError, ValueError, EOFError, asyncio.TimeoutError) as exc:
            print("MQTT:", repr(exc))
        finally:
            robot.mqtt = False
            if telemetry is not None:
                telemetry.cancel()
                try:
                    await telemetry
                except (asyncio.CancelledError, asyncio.TimeoutError, OSError):
                    pass
            if writer is not None:
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), 1)
                except (asyncio.TimeoutError, OSError):
                    pass
        await asyncio.sleep_ms(2500)
