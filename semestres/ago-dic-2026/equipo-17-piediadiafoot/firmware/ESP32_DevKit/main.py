"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   main.py
 Objetivo:  Coordina el procedimiento mediante una máquina de estados.
             La manipulación de GPIO y periféricos está encapsulada en hal.py.
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 | 
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import time
import network
import ujson as json
from mqtt_client import MQTTClient
from hal import VisionDiaFootHAL

with open("config.json", "r") as file:
    CFG = json.load(file)

TOPIC_SENSORS = CFG.get("topic_sensors", "proyecto/sensores/lectura")
TOPIC_STATE = CFG.get("topic_state", "proyecto/actuador/estado")
TOPIC_COMMAND = CFG.get("topic_command", "proyecto/actuador/cmd")
TOPIC_IA = CFG.get("topic_ia", "proyecto/ia/decision")
TOPIC_CAMERA_STATE = CFG.get("topic_camera_state", "proyecto/camara/estado")


class VisionDiaFootController:
    #Lógica de aplicación; recibe datos HAL y coordina el procedimiento.

    STATE_INIT = "INICIALIZANDO"
    STATE_WAIT_FOOT = "ESPERANDO_PIE"
    STATE_CHECK_POSITION = "VALIDANDO_POSICION"
    STATE_WAIT_HEEL = "CONFIRMAR_TALON"
    STATE_WAIT_TEMP = "VALIDAR_TEMPERATURA"
    STATE_WAIT_CAMERA = "ESPERANDO_CAMARA_IA"
    STATE_MANUAL_ALIGN = "AJUSTE_MANUAL_CAMARA"
    STATE_READY = "LISTO_PARA_ESCANEO"
    STATE_FINISH = "ESPERANDO_RETIRO_PIE"
    STATE_RETURN_CENTER = "REGRESAR_CAMARA_CENTRO"
    STATE_COMPLETE = "REVISION_FINALIZADA"
    STATE_EMERGENCY = "EMERGENCIA"
    STATE_MQTT = "ESPERANDO_MQTT"

    def __init__(self, hardware, config):
        self.hw = hardware
        self.cfg = config
        self.state = self.STATE_INIT
        self.mqtt = None
        self.mqtt_connected = False
        self.camera_ready = False
        self.yolo_ready = False
        self.last_camera_status_ms = None
        self.last_ia = {}
        self.last_ia_ms = None
        self.last_reading = {}
        self.heel_confirmed = False
        self.thermal_confirmed = False
        self.framing_confirmed = False
        self.finish_requested = False
        self.return_center_pending = False
        self.emergency = False
        self.last_beep_ms = 0
        self.last_sensor_ms = 0
        self.last_publish_ms = 0
        self.last_display_ms = 0
        self.last_oled_page_ms = 0
        self.oled_page = 0
        self.foot_removed_since = None
        self.session_counter = 0
        self.last_sensor_json = {}
        self.temperature_validation_enabled = bool(config.get("temperature_validation_enabled", False))
        self.temperature_delta_min = config.get("temperature_delta_min_c", None)
        self.distance_reference = float(config.get("distance_reference_cm", 39.0))
        self.acrylic_length = float(config.get("acrylic_length_cm", 30.0))
        self.acrylic_center = self.acrylic_length / 2.0
        self.foot_length_min = float(config.get("foot_length_min_cm", 10.0))
        self.foot_length_max = float(config.get("foot_length_max_cm", 30.0))
        self.distance_min = float(config.get("distance_min_cm", 5.0))
        self.distance_max = float(config.get("distance_max_cm", 29.0))
        self.position_tolerance = float(config.get("position_tolerance_cm", 2.0))
        self.removal_confirm_ms = int(config.get("foot_removal_confirm_ms", 2000))
        self.camera_timeout_ms = int(config.get("camera_status_timeout_ms", 6000))
        self.ia_timeout_ms = int(config.get("ia_timeout_ms", 4000))

    def set_mqtt(self, client):
        self.mqtt = client
        self.mqtt_connected = client is not None

    def _publish(self, topic, data, retain=False):
        if self.mqtt is None:
            return False
        try:
            self.mqtt.publish(topic, json.dumps(data), retain=retain)
            return True
        except Exception as exc:
            print("Error publicando MQTT:", exc)
            return False

    def handle_message(self, topic, payload):
        try:
            message = json.loads(payload.decode())
        except Exception as exc:
            print("JSON MQTT invalido:", exc)
            return

        if topic == TOPIC_IA:
            self.last_ia = message
            self.last_ia_ms = time.ticks_ms()
            return

        if topic == TOPIC_CAMERA_STATE:
            self.camera_ready = bool(message.get("camera_ready", False))
            self.yolo_ready = bool(message.get("yolo_ready", False))
            self.last_camera_status_ms = time.ticks_ms()
            return

        if topic != TOPIC_COMMAND:
            return

        command = message.get("cmd", "")
        print("Comando MQTT:", message)

        if command == "motor":
            if self.emergency:
                print("Motor bloqueado: emergencia activa")
                return
            direction = message.get("direction", "")
            duration = message.get("duration_ms", self.cfg.get("motor_max_pulse_ms", 100))
            ok, reason = self.hw.motor_banda.solicitar_pulso(direction, duration)
            print("Motor:", reason)
            if ok:
                self.framing_confirmed = False

        elif command == "stop_motor":
            self.hw.motor_banda.detener()

        elif command == "set_center":
            self.hw.motor_banda.fijar_centro()
            self.framing_confirmed = False
            if self.return_center_pending:
                self.return_center_pending = False
                self._set_state(self.STATE_COMPLETE)
                print("Camara confirmada nuevamente en el centro. Sesion cerrada.")
            else:
                print("Referencia central registrada. Use C solo cuando el carro este en la marca.")

        elif command == "heel_confirm":
            if self.last_reading.get("pressure_ok", False):
                self.heel_confirmed = bool(message.get("confirmed", True))
            else:
                print("No se confirma talon: FSR no detecta apoyo")

        elif command == "thermal_confirm":
            self.thermal_confirmed = bool(message.get("confirmed", True))

        elif command == "framing_confirm":
            if self.hw.motor_banda.center_confirmed:
                self.framing_confirmed = bool(message.get("confirmed", True))
            else:
                print("Primero marque el centro con C")

        elif command == "finish_review":
            self.finish_requested = True
            self.state = self.STATE_FINISH
            self.foot_removed_since = None
            print("El medico finalizo la revision; esperando retiro del pie")

        elif command == "emergency_stop":
            self._emergency_stop()

        elif command == "reset_emergency":
            self.emergency = False
            self.hw.motor_banda.rearmar()
            self.heel_confirmed = False
            self.thermal_confirmed = False
            self.framing_confirmed = False
            self.finish_requested = False
            self.return_center_pending = False
            self.state = self.STATE_WAIT_FOOT
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self.hw.buzzer.apagar()
            print("Emergencia rearmada; requiere nueva referencia C y nueva validacion")

        elif command == "beep":
            self.hw.buzzer.beep(int(message.get("duration_ms", 180)))

        elif command == "capture_ack":
            # Reservado para enlazar confirmaciones de captura del backend.
            pass

    def _emergency_stop(self):
        self.emergency = True
        self.hw.motor_banda.emergencia()
        self.hw.ventilacion.apagar()
        self.hw.bandera.oculta()
        self.hw.buzzer.beep(700)
        self.state = self.STATE_EMERGENCY
        self._publish(TOPIC_STATE, self._state_payload())
        print("PARADA DE EMERGENCIA ACTIVADA")

    def _distance_analysis(self, distance_cm):
        if distance_cm is None:
            return None, None, False
        if distance_cm < self.distance_min or distance_cm > self.distance_max:
            return None, None, False
        length = self.distance_reference - float(distance_cm)
        if length < self.foot_length_min or length > self.foot_length_max:
            return length, None, False
        target_center = self.acrylic_length - (length / 2.0)
        recommended_offset = target_center - self.acrylic_center
        return round(length, 2), round(recommended_offset, 2), True

    def _temperature_ok(self, reading):
        if not reading.get("temperature_available"):
            return False
        if not self.temperature_validation_enabled or self.temperature_delta_min is None:
            return self.thermal_confirmed
        ambient = reading.get("ambient_temp_c")
        obj = reading.get("object_temp_c")
        if ambient is None or obj is None:
            return False
        return abs(float(obj) - float(ambient)) >= float(self.temperature_delta_min)

    def _beep_limited(self, now, duration=150):
        period = int(self.cfg.get("alert_repeat_ms", 2500))
        if time.ticks_diff(now, self.last_beep_ms) >= period:
            self.hw.buzzer.beep(duration)
            self.last_beep_ms = now

    def _set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self._publish(TOPIC_STATE, self._state_payload())

    def _state_payload(self):
        return {
            "workflow_state": self.state,
            "motor": self.hw.motor_banda.estado(),
            "fan_led_on": self.hw.ventilacion.encendido,
            "flag_ready": self.state == self.STATE_READY,
            "mqtt_connected": self.mqtt_connected,
            "camera_ready": self.camera_ready,
            "yolo_ready": self.yolo_ready,
            "emergency": self.emergency
        }

    def _render_displays(self, reading, foot_length, offset):
        ambient = reading.get("ambient_temp_c")
        obj = reading.get("object_temp_c")
        distance = reading.get("distance_cm")
        fsr = reading.get("fsr_raw", 0)
        temp_txt = "--" if obj is None else str(obj)
        dist_txt = "--" if distance is None else str(distance)
        offset_txt = "--" if offset is None else ("%+.1fcm" % offset)
        classes = self.last_ia.get("detections", [])
        class_txt = "Sin deteccion"
        confidence_txt = "--"
        if classes:
            class_txt = str(classes[0].get("class_name", "Deteccion"))[:16]
            confidence_txt = str(round(float(classes[0].get("confidence", 0.0)) * 100)) + "%"

        #Alterna cada cuatro segundos entre una página de mediciones y otra
        # de comunicación/IA para aprovechar el OLED 128x64.
        if time.ticks_diff(time.ticks_ms(), self.last_oled_page_ms) >= 4000:
            self.oled_page = 1 - self.oled_page
            self.last_oled_page_ms = time.ticks_ms()

        if self.oled_page == 0:
            length_txt = "--" if foot_length is None else str(foot_length)
            lines = [
                "Tobj:" + temp_txt + "C",
                "Tamb:" + ("--" if ambient is None else str(ambient))[:8],
                "FSR:" + str(fsr)[:7] + " D:" + dist_txt[:6],
                "L:" + length_txt[:5] + " Aj:" + offset_txt[:7]
            ]
        else:
            lines = [
                "Estado:" + self.state[:9],
                "Camara:" + ("OK" if self.camera_ready else "NO"),
                "YOLO:" + ("OK" if self.yolo_ready else "NO"),
                "IA:" + class_txt[:8] + " " + confidence_txt[:4]
            ]
        self.hw.oled.mostrar_lineas(lines)

        lcd_messages = {
            self.STATE_WAIT_FOOT: ("Coloque el pie", "Talon al tope"),
            self.STATE_CHECK_POSITION: ("Validando pie", "Mantenga quieto"),
            self.STATE_WAIT_HEEL: ("Talón al tope", "Confirme tecla A"),
            self.STATE_WAIT_TEMP: ("Revise sensor IR", "Confirme tecla T"),
            self.STATE_WAIT_CAMERA: ("Esperando camara", "Revise laptop"),
            self.STATE_MANUAL_ALIGN: ("Ajuste camara", "F/B y confirme V"),
            self.STATE_READY: ("Posicion correcta", "Medico: capture P"),
            self.STATE_FINISH: ("Revision finalizada", "Retire el pie"),
            self.STATE_RETURN_CENTER: ("Regrese camara", "Centro y confirme C"),
            self.STATE_COMPLETE: ("Sesion terminada", "Sistema en espera"),
            self.STATE_EMERGENCY: ("EMERGENCIA", "Solicite asistencia"),
            self.STATE_MQTT: ("Conectando sistema", "Espere por favor"),
            self.STATE_INIT: ("Iniciando sistema", "Espere por favor")
        }
        msg = lcd_messages.get(self.state, ("Vision Dia Foot", "En espera"))
        self.hw.lcd.mostrar(msg[0], msg[1])
        print("Estado:", self.state, "Pie(cm):", foot_length, "Ajuste(cm):", offset, "IA:", class_txt)

    def _complete_review(self):
        #Al retirar el pie se apagan los elementos de preparación. La cámara
        # debe volver MANUALMENTE a su marca central y confirmarse con C.
        self.hw.ventilacion.apagar()
        self.hw.bandera.oculta()
        self.hw.motor_banda.detener()
        self.hw.buzzer.apagar()
        self.finish_requested = False
        self.heel_confirmed = False
        self.thermal_confirmed = False
        self.framing_confirmed = False
        self.foot_removed_since = None
        self.return_center_pending = True
        self._set_state(self.STATE_RETURN_CENTER)

    def update(self, reading):
        now = time.ticks_ms()
        self.last_reading = reading
        self.hw.actualizar_actuadores()

        if self.emergency:
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self._set_state(self.STATE_EMERGENCY)
            return

        #Sin MQTT no se permite declarar la estación lista ni mantener
        # activos los actuadores de preparación.
        if not self.mqtt_connected:
            self.hw.motor_banda.detener()
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self._set_state(self.STATE_MQTT)
            self._maybe_publish_and_display(reading, None, None, now)
            return

        #Después de terminar y retirar el pie, el operador devuelve la cámara
        # al centro con F/B y confirma la marca física con C.
        if self.return_center_pending:
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self._set_state(self.STATE_RETURN_CENTER)
            self._maybe_publish_and_display(reading, None, None, now)
            return

        # Un estado de cámara/YOLO se considera vencido si deja de actualizarse.
        if self.last_camera_status_ms is None or time.ticks_diff(now, self.last_camera_status_ms) > self.camera_timeout_ms:
            self.camera_ready = False
            self.yolo_ready = False
        #El status retenido de la laptop no basta: exigimos una inferencia
        # reciente para detectar que YOLO sigue ejecutándose.
        if self.last_ia_ms is None or time.ticks_diff(now, self.last_ia_ms) > self.ia_timeout_ms:
            self.yolo_ready = False

        pressure = bool(reading.get("pressure_ok", False))
        distance = reading.get("distance_cm")
        foot_length, recommended_offset, distance_ok = self._distance_analysis(distance)
        temperature_available = bool(reading.get("temperature_available", False))

        if self.finish_requested:
            self.hw.motor_banda.detener()
            self._set_state(self.STATE_FINISH)
            if not pressure:
                if self.foot_removed_since is None:
                    self.foot_removed_since = now
                elif time.ticks_diff(now, self.foot_removed_since) >= self.removal_confirm_ms:
                    self._complete_review()
            else:
                self.foot_removed_since = None
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not pressure:
            if self.state == self.STATE_READY or self.hw.ventilacion.encendido:
                self.hw.ventilacion.apagar()
                self.hw.bandera.oculta()
            #Si se retira el pie, cualquier confirmación de esa sesión caduca.
            self.framing_confirmed = False
            self.heel_confirmed = False
            self.thermal_confirmed = False
            if self.state != self.STATE_COMPLETE:
                self._set_state(self.STATE_WAIT_FOOT)
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not distance_ok:
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self._set_state(self.STATE_CHECK_POSITION)
            self._beep_limited(now)
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not self.heel_confirmed:
            self._set_state(self.STATE_WAIT_HEEL)
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not temperature_available:
            self._set_state(self.STATE_WAIT_TEMP)
            self._beep_limited(now)
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not self._temperature_ok(reading):
            self._set_state(self.STATE_WAIT_TEMP)
            self._beep_limited(now)
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not self.camera_ready or not self.yolo_ready:
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self._set_state(self.STATE_WAIT_CAMERA)
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        if not self.hw.motor_banda.center_confirmed or not self.framing_confirmed:
            self._set_state(self.STATE_MANUAL_ALIGN)
            self.hw.ventilacion.apagar()
            self.hw.bandera.oculta()
            self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)
            return

        self._set_state(self.STATE_READY)
        self.hw.ventilacion.encender()
        self.hw.bandera.mostrar_listo()
        self._maybe_publish_and_display(reading, foot_length, recommended_offset, now)

    def _maybe_publish_and_display(self, reading, foot_length, offset, now):
        sensor_period = int(self.cfg.get("sensor_period_ms", 1000))
        if time.ticks_diff(now, self.last_publish_ms) >= sensor_period:
            self.last_publish_ms = now
            payload = dict(reading)
            payload.update({
                "foot_length_estimated_cm": foot_length,
                "camera_center_offset_estimated_cm": offset,
                "workflow_state": self.state,
                "heel_confirmed": self.heel_confirmed,
                "thermal_confirmed": self.thermal_confirmed,
                "framing_confirmed": self.framing_confirmed,
                "camera_ready": self.camera_ready,
                "yolo_ready": self.yolo_ready,
                "temperature_validation_calibrated": self.temperature_validation_enabled
            })
            self._publish(TOPIC_SENSORS, payload)
            self._publish(TOPIC_STATE, self._state_payload())

        if time.ticks_diff(now, self.last_display_ms) >= int(self.cfg.get("display_period_ms", 1000)):
            self.last_display_ms = now
            self._render_displays(reading, foot_length, offset)


#Inicialización y ciclo principal
print("Vision Dia Foot: iniciando controlador...")
hardware = VisionDiaFootHAL(CFG)
controller = VisionDiaFootController(hardware, CFG)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("Wi-Fi conectado:", wlan.ifconfig())
        return wlan
    wlan.connect(CFG["wifi_ssid"], CFG["wifi_password"])
    start = time.ticks_ms()
    while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), start) < 20000:
        time.sleep_ms(500)
    if not wlan.isconnected():
        raise OSError("No se pudo conectar a Wi-Fi")
    print("Wi-Fi OK:", wlan.ifconfig()[0])
    return wlan


def mqtt_callback(topic, payload):
    controller.handle_message(topic, payload)


def connect_mqtt():
    client = MQTTClient(
        CFG.get("client_id", "vision-dia-foot-devkit"),
        CFG["mqtt_host"],
        int(CFG.get("mqtt_port", 1883)),
        CFG.get("mqtt_user"),
        CFG.get("mqtt_password"),
        keepalive=30,
        callback=mqtt_callback
    )
    client.connect()
    #MQTT SUBSCRIBE: comandos, resultados YOLO y disponibilidad de cámara.
    client.subscribe(TOPIC_COMMAND)
    client.subscribe(TOPIC_IA)
    client.subscribe(TOPIC_CAMERA_STATE)
    print("MQTT conectado. Suscrito a:", TOPIC_COMMAND, TOPIC_IA, TOPIC_CAMERA_STATE)
    return client


wlan = None
mqtt = None
last_wifi_try = 0
last_mqtt_try = 0
last_ping = time.ticks_ms()
controller.state = controller.STATE_INIT
hardware.lcd.mostrar("Iniciando VDF", "Espere por favor")
hardware.oled.mostrar_lineas(["Arrancando...", "Motor bloqueado", "Esperando MQTT"])

while True:
    now = time.ticks_ms()
    hardware.actualizar_actuadores()

    if wlan is None or not wlan.isconnected():
        if time.ticks_diff(now, last_wifi_try) >= 5000:
            last_wifi_try = now
            try:
                wlan = connect_wifi()
            except Exception as exc:
                print("Wi-Fi pendiente:", exc)
                controller.mqtt_connected = False
                hardware.motor_banda.detener()
                hardware.ventilacion.apagar()
                hardware.bandera.oculta()

    if wlan is not None and wlan.isconnected() and mqtt is None:
        if time.ticks_diff(now, last_mqtt_try) >= 5000:
            last_mqtt_try = now
            try:
                mqtt = connect_mqtt()
                controller.set_mqtt(mqtt)
                controller._publish(TOPIC_STATE, controller._state_payload(), retain=True)
            except Exception as exc:
                print("MQTT pendiente:", exc)
                mqtt = None
                controller.set_mqtt(None)

    if mqtt is not None:
        try:
            mqtt.check_msg()
            if time.ticks_diff(now, last_ping) >= 10000:
                mqtt.ping()
                last_ping = now
        except Exception as exc:
            print("MQTT desconectado:", exc)
            try:
                mqtt.disconnect()
            except Exception:
                pass
            mqtt = None
            controller.set_mqtt(None)
            hardware.motor_banda.detener()
            hardware.ventilacion.apagar()
            hardware.bandera.oculta()

    if time.ticks_diff(now, controller.last_sensor_ms) >= int(CFG.get("sensor_period_ms", 1000)):
        controller.last_sensor_ms = now
        try:
            sensor_data = hardware.leer_sensores()
            controller.update(sensor_data)
        except Exception as exc:
            print("Error en ciclo de sensores:", exc)
            hardware.motor_banda.detener()
            hardware.ventilacion.apagar()
            hardware.bandera.oculta()

    time.sleep_ms(20)
