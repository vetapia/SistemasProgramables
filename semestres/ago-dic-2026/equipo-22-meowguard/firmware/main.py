# ============================================
# Proyecto:  MEOWGUARD — Sistema Robótico Autónomo de Control de Plagas
# Archivo:   main.py
# Objetivo:  Programa principal del ESP32: navegación autónoma/manual, evasión, servidor local y MQTT
# Equipo:    Mónica Moreno Torres (23241119), Leonardo Gael Niño Cabrera (23240382)
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================
import asyncio
import json
import network
import time

import config as cfg
from hal.actuadores import Atomizador, Motores
from hal.sensores import Encoders, Giroscopio, Obstaculos
from hal.traccion import Traccion, WHEELS
from hal import mqtt

SIGNS = {"f": (1, 1), "b": (-1, -1), "l": (-1, 1), "r": (1, -1)}


def validate_pins():
    peripherals = (cfg.TRIG_PIN, cfg.ECHO_PIN, cfg.REAR_PIN, cfg.REAR_LEFT_PIN,
                   cfg.REAR_RIGHT_PIN, cfg.SDA_PIN, cfg.SCL_PIN,
                   cfg.ATOMIZER_POWER_PIN, cfg.ATOMIZER_SERVO_PIN, cfg.FAN_PIN)
    pins = cfg.MOTOR_PINS + peripherals + cfg.ENCODER_PINS
    connected = [pin for pin in pins if pin is not None]
    if len(connected) != len(set(connected)):
        raise ValueError("Hay GPIO repetidos en config.py")
    if any(pin is not None for pin in cfg.ENCODER_PINS) and None in cfg.ENCODER_PINS:
        raise ValueError("Configura los cuatro encoders o deja los cuatro en None.")


class Robot:
    def __init__(self):
        validate_pins()
        self.motors = Motores()
        self.atomizer = Atomizador()
        self.obstacles = Obstaculos()
        self.encoders = Encoders() if None not in cfg.ENCODER_PINS else None
        self.traction = Traccion(self.encoders)
        self.gyro = None
        self.gyro_state = "sin_imu"
        self.mode = "manual"
        self.command = "s"
        self.manual_since = time.ticks_ms()
        self.front = None
        self.front_at = None
        self.phase = "forward"
        self.phase_until = 0
        self.turn = "l"
        self.base = cfg.DEFAULT_POWER
        self.movement = "s"
        self.mqtt = False
        self.last_detection = None

    def calibrate(self):
        try:
            gyro = Giroscopio()
            print("Calibrando", gyro.model, "- no muevas el chasis")
            gyro.calibrar()
            self.gyro = gyro
            self.gyro_state = gyro.model
        except OSError as exc:
            self.gyro_state = "sin_imu"
            print("Giroscopio:", exc)

    def stop(self, now):
        self.command = "s"
        self.movement = "s"
        self.mode = "manual"
        self.phase = "forward"
        self.motors.stop(now)
        self.atomizer.stop()

    def accept(self, command):
        now = time.ticks_ms()
        if command in ("s", "stop", "manual", "auto"):
            self.stop(now)
            if command == "auto":
                self.mode = "auto"
        elif command in SIGNS:
            self.mode = "manual"
            self.command = command
            self.manual_since = now
        elif command == "spray":
            if self.mode != "manual" or self.command != "s" or self.movement != "s":
                return 409, "Deten el carro antes de atomizar"
            if not self.atomizer.start(now):
                return 409, "Atomizador no configurado o activo"
        elif command.startswith("power="):
            try:
                value = int(command[6:])
            except ValueError:
                return 400, "PWM invalido"
            if not 25 <= value <= 80:
                return 400, "PWM fuera del rango 25-80"
            self.base = value
        else:
            return 400, "Comando desconocido"
        return 200, "OK"

    def front_fresh(self, now):
        return self.front_at is not None and time.ticks_diff(now, self.front_at) < 400

    def desired(self, now, rear, left, right):
        front_valid = self.front_fresh(now) and self.front is not None
        front_clear = front_valid and self.front > cfg.FRONT_LIMIT_CM
        rear_blocked = rear or left or right
        if self.mode == "manual":
            if time.ticks_diff(now, self.manual_since) > 650:
                self.command = "s"
            if self.command == "f" and not front_clear:
                return "s"
            if self.command == "b" and rear_blocked:
                return "s"
            return self.command
        if not front_valid:
            self.phase = "forward"
            return "s"
        if self.phase == "reverse":
            if not rear_blocked and time.ticks_diff(now, self.phase_until) < 0:
                return "b"
            self.phase = "turn"
            self.phase_until = time.ticks_add(now, 450)
        if self.phase == "turn":
            if time.ticks_diff(now, self.phase_until) < 0:
                return self.turn
            self.phase = "forward"
            return "s"
        if front_clear:
            return "f"
        if left != right:
            self.turn = "r" if left else "l"
        else:
            self.turn = "l" if self.turn == "r" else "r"
        self.phase = "turn" if rear_blocked else "reverse"
        self.phase_until = time.ticks_add(now, 450 if rear_blocked else 300)
        return self.turn if rear_blocked else "b"

    def status(self):
        rear, left, right = self.obstacles.posteriores()
        return {
            "mode": self.mode, "motion": self.movement, "power": self.base,
            "front": self.front if self.front_fresh(time.ticks_ms()) else None,
            "rear": rear or left or right, "left": left, "right": right,
            "imu": self.gyro_state, "yaw_dps": round(self.traction.yaw, 1),
            "heading_error_deg": round(self.traction.angle, 1),
            "pwm_left": round(self.motors.power[0], 1),
            "pwm_right": round(self.motors.power[1], 1),
            "drift": self.traction.drift, "encoders": self.encoders is not None,
            "wheel_alert": (
                {"wheel": WHEELS[self.traction.wheel[0]], "reason": self.traction.wheel[1]}
                if self.traction.wheel else None),
            "wheel_cms": [round(v, 1) for v in self.traction.speeds] if self.traction.speeds else None,
            "atomizer": self.atomizer.phase if self.atomizer.power is not None else "sin_configurar",
            "mqtt": self.mqtt, "last_detection": self.last_detection,
        }

    async def measure_loop(self):
        while True:
            try:
                self.front = self.obstacles.frente()
            except OSError:
                self.front = None
            self.front_at = time.ticks_ms()
            await asyncio.sleep_ms(90)

    async def run(self):
        previous = time.ticks_ms()
        try:
            while True:
                now = time.ticks_ms()
                elapsed = max(1, time.ticks_diff(now, previous))
                previous = now
                desired = self.desired(now, *self.obstacles.posteriores())
                sample = None
                if self.gyro is not None:
                    try:
                        sample = self.gyro.yaw()
                        self.gyro_state = self.gyro.model
                    except OSError:
                        self.gyro_state = "error_i2c"
                if elapsed > 180:
                    self.stop(now)
                    desired = "s"
                left, right = self.traction.update(desired, self.base, sample, now, elapsed)
                if desired == "s":
                    self.motors.stop(now)
                else:
                    self.atomizer.stop()
                    self.motors.apply(SIGNS[desired], (left, right), now, elapsed)
                self.movement = desired
                self.atomizer.update(now)
                await asyncio.sleep_ms(20)
        finally:
            self.stop(time.ticks_ms())


def response(status, mime, body):
    reason = {200: "OK", 400: "Bad Request", 403: "Forbidden", 404: "Not Found",
              409: "Conflict"}[status]
    return (
        "HTTP/1.1 {} {}\r\nContent-Type: {}\r\nCache-Control: no-store\r\n"
        "Connection: close\r\nContent-Length: {}\r\n\r\n"
    ).format(status, reason, mime, len(body)).encode() + body


async def serve_request(reader, writer, robot):
    try:
        request = (await asyncio.wait_for(reader.readline(), 1)).decode().split()
        if len(request) < 2:
            return
        method, path = request[:2]
        if path == "/status" and method == "GET":
            output = response(200, "application/json", json.dumps(robot.status()).encode())
        elif path in ("/", "/control.html") and method == "GET":
            with open("control.html", "rb") as page:
                output = response(200, "text/html; charset=utf-8", page.read())
        elif path.startswith("/cmd?c=") and method == "POST":
            async def control_header():
                allowed = False
                for _ in range(32):
                    line = await reader.readline()
                    if line in (b"", b"\r\n"):
                        return allowed
                    if line.strip().lower() == b"x-meowguard: local":
                        allowed = True
                return False
            if await asyncio.wait_for(control_header(), 1):
                status, message = robot.accept(path[7:].split("&", 1)[0])
                output = response(status, "text/plain", message.encode())
            else:
                output = response(403, "text/plain", b"Usa la pagina de control del carro")
        else:
            output = response(404, "text/plain", b"Ruta desconocida")
        writer.write(output)
        await asyncio.wait_for(writer.drain(), 1)
    except (OSError, UnicodeError, asyncio.TimeoutError):
        pass
    finally:
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), 1)
        except (OSError, asyncio.TimeoutError):
            pass


async def connect_station(station):
    station.active(True)
    while True:
        if not station.isconnected():
            try:
                station.connect(cfg.WIFI_SSID, cfg.WIFI_PASSWORD)
                await asyncio.sleep_ms(9000)
                if station.isconnected():
                    print("Wi-Fi local:", station.ifconfig()[0])
            except OSError as exc:
                print("Wi-Fi:", exc)
        await asyncio.sleep_ms(3000)


async def main():
    robot = Robot()
    robot.calibrate()
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    try:
        ap.config(ssid=cfg.AP_SSID, key=cfg.AP_PASSWORD, security=3)
    except (ValueError, TypeError):
        ap.config(essid=cfg.AP_SSID, password=cfg.AP_PASSWORD, authmode=3)
    print("Control del carro: http://" + ap.ifconfig()[0])
    station = network.WLAN(network.STA_IF)

    async def handler(reader, writer):
        await serve_request(reader, writer, robot)

    server = await asyncio.start_server(handler, "0.0.0.0", 80)
    sensors = asyncio.create_task(robot.measure_loop())
    optional = []
    if cfg.WIFI_SSID:
        optional.append(asyncio.create_task(connect_station(station)))
        optional.append(asyncio.create_task(mqtt.run(station, robot)))
    try:
        await robot.run()
    finally:
        sensors.cancel()
        for task in optional:
            task.cancel()
        server.close()


if __name__ == "__main__":
    asyncio.run(main())
