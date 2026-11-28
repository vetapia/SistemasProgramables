# Realtime Database

| Ruta | Origen | Campos principales |
|---|---|---|
| `/meowguard/detections/{id}` | Servidor Python | `id`, `label`, `confidence` (0 a 1), `bbox_xyxy` (px), `source`, `ts_ms` |
| `/meowguard/telemetry/latest` | ESP32 → MQTT → servidor Python | `mode`, `motion`, `power`, `front`, `rear`, `left`, `right`, `imu`, `yaw_dps`, `heading_error_deg`, `pwm_left`, `pwm_right`, `drift`, `encoders`, `wheel_alert`, `wheel_cms`, `atomizer`, `mqtt`, `last_detection`, `ts_ms` |
| `/access/{uid}` | Administrador del proyecto | Valor textual `viewer` o `writer` |

El ESP32 reporta una muestra MQTT cada dos segundos. Realtime Database elimina los campos enviados como `null`; por ejemplo, la falta de eco frontal se convierte en un campo ausente. `wheel_alert` incluye `wheel` y `reason` cuando hay una sospecha individual. `ts_ms` es la marca de tiempo del servidor de Firebase.

En Firebase activa el acceso por correo y contraseña. Crea una cuenta para cada rol y registra sus UID como hijos de `access` desde la consola. Publica `reglas.json` en Realtime Database. El dashboard usa una cuenta `viewer`; sólo la cuenta `writer` del servidor realiza escrituras. Las credenciales del servidor se configuran mediante variables de entorno. El archivo de reglas deja denegados los accesos de otras cuentas.

En MQTT, `meowguard/detections` lleva eventos de IA y `meowguard/telemetry` el estado del carrito, ambos en JSON. Reserva la publicación de cada tema a su emisor y da permiso de lectura al consumidor correspondiente en el broker.
