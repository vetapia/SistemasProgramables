# Hardware Abstraction Layer (HAL) — OmniVault

| # | Componente | Pin ESP32 | E/S | Voltaje | Tópico MQTT | Formato / Unidad |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Sensor IR FC-51 (Monedas) | GPIO 13 | Entrada | 3.3V | `omnivault/sensor/moneda` | JSON `{"estado": int}` (0=Detectado) |
| 2 | Lector de Huella AS608 | GPIO 16 (RX2)| Entrada | 3.3V | `omnivault/sensor/huella` | JSON `{"id_usuario": int}` (0-127) |
| 3 | Servomotor Seguro (SG90) | GPIO 2 | Salida | 5.0V | `omnivault/actuador/puerta/cmd`| String (`"OPEN"` / `"CLOSE"`) |
| 4 | DFPlayer Mini (Audio) | GPIO 27 | Salida | 5.0V | `omnivault/actuador/audio/cmd` | JSON `{"track": int}` (1-10) |
| 5 | Cámara ESP32-CAM S3 | UART 0 | E/S | 5.0V | `omnivault/cam/frame` | String (Base64 JPEG) |