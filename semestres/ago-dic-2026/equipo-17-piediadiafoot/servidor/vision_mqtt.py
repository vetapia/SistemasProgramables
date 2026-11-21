"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   vision_mqtt.py
 Objetivo:
     - Recibir fotogramas RGB565 desde la ESP32-WROVER por HTTP /frame.
     - Ejecutar YOLO y publicar las detecciones por MQTT.
     - Recibir lecturas de sensores y estados del DevKit.
     - Enviar comandos del operador mediante MQTT.
     - Guardar varias fotografías originales, anotadas y sus metadatos JSON.
     - Publicar disponibilidad de cámara/YOLO y aceptar solicitud de captura para facilitar la futura integración con un dashboard.
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 | 
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import json
import os
import time
import queue
import urllib.request
import urllib.error
from datetime import datetime

import numpy as np
import cv2
import paho.mqtt.client as mqtt
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_ia.json")
with open(CONFIG_FILE, "r", encoding="utf-8") as file:
    CFG = json.load(file)

TOPIC_COMMAND = CFG.get("topic_command", "proyecto/actuador/cmd")
TOPIC_SENSORS = CFG.get("topic_sensors", "proyecto/sensores/lectura")
TOPIC_STATE = CFG.get("topic_state", "proyecto/actuador/estado")
TOPIC_IA = CFG.get("topic_ia", "proyecto/ia/decision")
TOPIC_CAMERA_COMMAND = CFG.get("topic_camera_command", "proyecto/camara/cmd")
TOPIC_CAMERA_STATE = CFG.get("topic_camera_state", "proyecto/camara/estado")

mqtt_ready = False
last_sensor_json = {}
last_state_json = {}
last_state_received = 0.0
camera_command_queue = queue.Queue()


def on_connect(client, userdata, flags, reason_code, properties=None):
    global mqtt_ready
    try:
        connected = int(reason_code) == 0
    except Exception:
        connected = str(reason_code).lower() in ("success", "0")
    mqtt_ready = connected
    if connected:
        print("MQTT conectado a", CFG["mqtt_host"])
        client.subscribe([
            (TOPIC_SENSORS, 0),
            (TOPIC_STATE, 0),
            (TOPIC_CAMERA_COMMAND, 0)
        ])
    else:
        print("MQTT rechazado:", reason_code)


def on_disconnect(client, userdata, *args):
    global mqtt_ready
    mqtt_ready = False
    print("MQTT desconectado.")


def on_message(client, userdata, message):
    global last_sensor_json, last_state_json, last_state_received
    try:
        payload = json.loads(message.payload.decode("utf-8", errors="replace"))
    except Exception:
        payload = {"raw": message.payload.decode("utf-8", errors="replace")}

    if message.topic == TOPIC_SENSORS:
        last_sensor_json = payload
        print("[SENSORES]", json.dumps(payload, ensure_ascii=False))
    elif message.topic == TOPIC_STATE:
        last_state_json = payload
        last_state_received = time.monotonic()
        print("[ESTADO]", json.dumps(payload, ensure_ascii=False))
    elif message.topic == TOPIC_CAMERA_COMMAND:
        #No se guarda la imagen desde el hilo MQTT: se encola y el hilo principal la guarda
        #  con el fotograma que tiene en memoria.
        if payload.get("cmd") == "capture":
            camera_command_queue.put("mqtt")


def fetch_rgb565_frame(url, width, height, timeout=3.0):
    """Obtiene RGB565 crudo desde /frame y lo convierte a BGR para OpenCV."""
    request = urllib.request.Request(
        url,
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()

    expected = width * height * 2
    if len(raw) != expected:
        raise ValueError(
            "Tamano RGB565 inesperado: recibidos %s bytes; esperados %s. "
            "Comprueba QVGA/RGB565 y el endpoint /frame." % (len(raw), expected)
        )

    pixels = np.frombuffer(raw, dtype=">u2").reshape((height, width))
    red = (((pixels >> 11) & 0x1F) * 255 // 31).astype(np.uint8)
    green = (((pixels >> 5) & 0x3F) * 255 // 63).astype(np.uint8)
    blue = ((pixels & 0x1F) * 255 // 31).astype(np.uint8)
    return np.dstack((blue, green, red))


def publish_json(topic, payload, retain=False):
    if not mqtt_ready:
        return False
    try:
        result = client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=0, retain=retain)
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as exc:
        print("Error publicando", topic, ":", exc)
        return False


def send_command(payload):
    if not publish_json(TOPIC_COMMAND, payload):
        print("No se envio comando: MQTT no esta conectado o fallo la publicacion.")
        return False
    print("[COMANDO]", json.dumps(payload, ensure_ascii=False))
    return True


def publish_camera_status(camera_ready, yolo_ready, detail=""):
    status = {
        "type": "camera_status",
        "camera_ready": bool(camera_ready),
        "yolo_ready": bool(yolo_ready),
        "detail": str(detail),
        "timestamp_unix": round(time.time(), 3)
    }
    publish_json(TOPIC_CAMERA_STATE, status, retain=True)


def create_session_directory(foot_side):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = os.path.join(BASE_DIR, CFG.get("capture_directory", "capturas"))
    safe_side = str(foot_side).lower().replace(" ", "_")
    session_path = os.path.join(output_root, "sesion_" + stamp + "_" + safe_side)
    os.makedirs(session_path, exist_ok=True)
    return session_path, stamp


def save_capture(frame, annotated, detections, session_path, session_stamp,
                 capture_index, source, foot_side):
    """Guarda original, anotada y JSON asociado. Devuelve rutas relativas."""
    now = datetime.now()
    file_stamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]
    prefix = "VDF_%s_%03d" % (file_stamp, capture_index)
    original_name = prefix + "_original.jpg"
    annotated_name = prefix + "_yolo.jpg"
    json_name = prefix + "_datos.json"

    original_path = os.path.join(session_path, original_name)
    annotated_path = os.path.join(session_path, annotated_name)
    json_path = os.path.join(session_path, json_name)

    if not cv2.imwrite(original_path, frame):
        raise IOError("No se pudo guardar la fotografia original")
    if not cv2.imwrite(annotated_path, annotated):
        raise IOError("No se pudo guardar la fotografia anotada")

    metadata = {
        "project": "Vision Dia Foot",
        "session_id": session_stamp,
        "capture_index": capture_index,
        "timestamp_local": now.isoformat(timespec="milliseconds"),
        "capture_source": source,
        "foot_side": foot_side,
        "original_image": original_name,
        "annotated_image": annotated_name,
        "detections": detections,
        "sensor_readings": last_sensor_json,
        "station_state": last_state_json,
        "medical_note": "Resultado experimental de vision; no constituye diagnostico medico."
    }
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    return original_path, annotated_path, json_path


# Cliente Paho compatible con Paho MQTT 1.x y 2.x.
try:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=CFG.get("client_id", "vision-dia-foot-laptop")
    )
except (AttributeError, TypeError):
    client = mqtt.Client(client_id=CFG.get("client_id", "vision-dia-foot-laptop"))

if CFG.get("mqtt_user"):
    client.username_pw_set(CFG["mqtt_user"], CFG.get("mqtt_password", ""))
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

print("Conectando a MQTT...")
client.connect(CFG["mqtt_host"], int(CFG.get("mqtt_port", 1883)), keepalive=30)
client.loop_start()

try:
    model_path = CFG["model_path"]
    if not os.path.isfile(model_path):
        raise FileNotFoundError("No encuentro el modelo configurado: " + model_path)
    print("Cargando modelo YOLO:", model_path)
    model = YOLO(model_path)

    frame_url = CFG["camera_stream_url"].rstrip("/")
    if not frame_url.endswith("/frame"):
        frame_url += "/frame"
    width = int(CFG.get("camera_width", 320))
    height = int(CFG.get("camera_height", 240))
    frame_period = max(0.01, float(CFG.get("frame_period_seconds", 0.05)))
    confidence = float(CFG.get("confidence", 0.35))
    publish_period = max(0.2, float(CFG.get("publish_every_seconds", 1.0)))
    show_window = bool(CFG.get("show_window", True))
    capture_requires_ready = bool(CFG.get("capture_requires_ready", True))

    print("Leyendo fotogramas de:", frame_url)
    frame = fetch_rgb565_frame(frame_url, width, height)
    print("Camara OK:", frame.shape)
    publish_camera_status(True, True, "Primer fotograma y modelo YOLO disponibles")

    session_path = None
    session_stamp = None
    session_active = False
    capture_index = 0
    current_foot_side = CFG.get("foot_side", "no_especificado")
    last_publish = 0.0
    last_frame_time = 0.0
    last_status_publish = 0.0
    camera_is_available = True
    consecutive_frame_errors = 0
    last_detections = []
    last_annotated = frame.copy()
    last_result = None

    pulse_ms = int(CFG.get("manual_motor_pulse_ms", 100))
    print("\nCONTROLES DE VISION DIA FOOT")
    print("F/B: pulso manual de banda | S: detener | C: marcar centro")
    print("A: confirmar talon | T: confirmar revision visual IR | V: confirmar encuadre")
    print("P: fotografia | N: finalizar revision | I/D: lado de la siguiente sesion")
    print("E: emergencia | R: rearmar | Q: salir")
    print("Motor bloqueado en config del DevKit hasta validar topes y corriente.")
    print("Lado inicial de pie:", current_foot_side)
    print("Las carpetas de captura se crean al llegar a LISTO_PARA_ESCANEO.")

    while True:
        now_perf = time.monotonic()
        if now_perf - last_frame_time < frame_period:
            if show_window:
                key = cv2.waitKey(1) & 0xFF
            else:
                time.sleep(0.002)
                key = 255
        else:
            last_frame_time = now_perf
            try:
                frame = fetch_rgb565_frame(frame_url, width, height)
                consecutive_frame_errors = 0
                if not camera_is_available:
                    camera_is_available = True
                    publish_camera_status(True, True, "Camara recuperada")
            except (OSError, urllib.error.URLError, ValueError) as exc:
                consecutive_frame_errors += 1
                print("No llego fotograma:", exc)
                if consecutive_frame_errors >= 3 and camera_is_available:
                    camera_is_available = False
                    publish_camera_status(False, True, "No se reciben fotogramas HTTP")
                if show_window:
                    key = cv2.waitKey(1) & 0xFF
                else:
                    key = 255
                time.sleep(0.05)
                frame = None

            if frame is not None:
                result = model.predict(source=frame, conf=confidence, verbose=False)[0]
                last_result = result
                detections = []
                names = result.names
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        xyxy = [round(float(value), 1) for value in box.xyxy[0].tolist()]
                        if isinstance(names, dict):
                            class_name = str(names.get(class_id, class_id))
                        else:
                            class_name = str(names[class_id])
                        detections.append({
                            "class_id": class_id,
                            "class_name": class_name,
                            "confidence": round(conf, 4),
                            "xyxy": xyxy
                        })
                last_detections = detections
                annotated = result.plot()
                last_annotated = annotated.copy()

                now_unix = time.time()
                if mqtt_ready and now_unix - last_publish >= publish_period:
                    decision = {
                        "type": "yolo_inference",
                        "timestamp_unix": round(now_unix, 3),
                        "model_file": os.path.basename(model_path),
                        "detected": bool(detections),
                        "count": len(detections),
                        "detections": detections,
                        "note": "Resultado experimental de vision; no representa diagnostico medico."
                    }
                    publish_json(TOPIC_IA, decision)
                    last_publish = now_unix

                if mqtt_ready and now_unix - last_status_publish >= 2.0:
                    publish_camera_status(camera_is_available, True, "Video HTTP y YOLO activos")
                    last_status_publish = now_unix

                if show_window:
                    status = "MQTT OK" if mqtt_ready else "MQTT desconectado"
                    state = last_state_json.get("workflow_state", "SIN ESTADO")
                    cv2.putText(annotated, status, (10, 22), cv2.FONT_HERSHEY_SIMPLEX,
                                0.55, (0, 255, 0) if mqtt_ready else (0, 0, 255), 2)
                    cv2.putText(annotated, str(state)[:35], (10, 45), cv2.FONT_HERSHEY_SIMPLEX,
                                0.45, (255, 255, 0), 1)
                    cv2.imshow("Vision Dia Foot - YOLO / MQTT", annotated)
                    key = cv2.waitKey(1) & 0xFF
                else:
                    key = 255

        station_state = last_state_json.get("workflow_state", "")
        if station_state == "LISTO_PARA_ESCANEO" and not session_active:
            session_path, session_stamp = create_session_directory(current_foot_side)
            capture_index = 0
            session_active = True
            print("Nueva sesion:", session_path)
        elif station_state == "REVISION_FINALIZADA" and session_active:
            session_active = False
            print("Sesion cerrada. Seleccione el siguiente pie antes de la proxima revision.")

        #Procesar solicitudes de captura recibidas por MQTT (futuro dashboard).
        capture_source = None
        try:
            capture_source = camera_command_queue.get_nowait()
        except queue.Empty:
            pass
        if key in (ord('p'), ord('P')):
            capture_source = "tecla_P"

        if capture_source:
            state_name = last_state_json.get("workflow_state", "")
            state_is_fresh = (last_state_received > 0 and
                              (time.monotonic() - last_state_received) <= 3.0)
            if capture_requires_ready and (state_name != "LISTO_PARA_ESCANEO" or not state_is_fresh or not session_active):
                print("Captura rechazada: se requiere sesion activa y estado LISTO_PARA_ESCANEO reciente por MQTT.")
            elif frame is None or last_annotated is None or session_path is None:
                print("Captura no disponible: no hay fotograma reciente.")
            else:
                capture_index += 1
                try:
                    paths = save_capture(
                        frame.copy(), last_annotated.copy(), last_detections,
                        session_path, session_stamp, capture_index, capture_source,
                        current_foot_side
                    )
                    print("Fotografia guardada:", paths)
                    publish_json(TOPIC_CAMERA_STATE, {
                        "type": "capture_saved",
                        "camera_ready": camera_is_available,
                        "yolo_ready": True,
                        "capture_index": capture_index,
                        "timestamp_unix": round(time.time(), 3),
                        "detail": os.path.basename(paths[0])
                    }, retain=False)
                except Exception as exc:
                    print("Error guardando captura:", exc)

        #Comandos manuales de operación. Cada tecla F/B produce un pulso individual,
        # no se mantiene un movimiento continuo por tecla sostenida.
        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('i'), ord('I')):
            if not session_active:
                current_foot_side = "izquierdo"
                print("Siguiente sesion: pie izquierdo")
            else:
                print("No cambie de lado durante una sesion activa")
        elif key in (ord('d'), ord('D')):
            if not session_active:
                current_foot_side = "derecho"
                print("Siguiente sesion: pie derecho")
            else:
                print("No cambie de lado durante una sesion activa")
        elif key in (ord('f'), ord('F')):
            send_command({"cmd": "motor", "direction": "forward", "duration_ms": pulse_ms})
        elif key in (ord('b'), ord('B')):
            send_command({"cmd": "motor", "direction": "reverse", "duration_ms": pulse_ms})
        elif key in (ord('s'), ord('S')):
            send_command({"cmd": "stop_motor"})
        elif key in (ord('c'), ord('C')):
            send_command({"cmd": "set_center"})
        elif key in (ord('a'), ord('A')):
            send_command({"cmd": "heel_confirm", "confirmed": True})
        elif key in (ord('t'), ord('T')):
            send_command({"cmd": "thermal_confirm", "confirmed": True})
        elif key in (ord('v'), ord('V')):
            send_command({"cmd": "framing_confirm", "confirmed": True})
        elif key in (ord('n'), ord('N')):
            send_command({"cmd": "finish_review"})
        elif key in (ord('h'), ord('H')):
            send_command({"cmd": "beep", "duration_ms": 250})
        elif key in (ord('e'), ord('E')):
            send_command({"cmd": "emergency_stop"})
        elif key in (ord('r'), ord('R')):
            send_command({"cmd": "reset_emergency"})

finally:
    try:
        if mqtt_ready:
            client.publish(TOPIC_COMMAND, json.dumps({"cmd": "emergency_stop"}), qos=0)
            publish_camera_status(False, False, "Programa de laptop detenido")
            time.sleep(0.2)
    except Exception:
        pass
    if locals().get('show_window', True):
        cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()
    print("Programa de Vision Dia Foot finalizado.")
