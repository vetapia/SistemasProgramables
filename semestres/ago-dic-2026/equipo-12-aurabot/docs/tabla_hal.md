# Tabla de Abstracción de Hardware (HAL)

| Componente | Tipo | Pin ESP32 | Tópico publicación | Tópico suscripción | Unidad | Rango |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PIR (HC-SR501) | Sensor | GPIO 13 | aurabot/sensor/pir/central | --- | 1/0 (Presencia) | 0 a 1 |
| Ultrasónico (HC-SR04) | Sensor | TRIG: 26, ECHO: 25 | aurabot/sensor/ultrasonico/central | --- | cm | 2 a 400 |
| Luz (LDR) | Sensor | GPIO 34 | aurabot/sensor/luz/central | --- | % | 0 a 100 |
| Servomotor Cabeza (SG90) | Actuador | GPIO 18 | aurabot/actuador/servo/central | aurabot/comando/servo/central | Comando / Grados | 0 a 180 |
| Servomotor Brazo Izq. (SG90) | Actuador | GPIO 19 | aurabot/actuador/servo/central | aurabot/comando/servo/central | Comando / Grados | 0 a 180 |
| Servomotor Brazo Der. (SG90) | Actuador | GPIO 27 | aurabot/actuador/servo/central | aurabot/comando/servo/central | Comando / Grados | 0 a 180 |
| Relevador (1 Canal) | Actuador | GPIO 23 | aurabot/actuador/relevador/central | aurabot/comando/relevador/central | Estado (Texto) | "encender", "apagar" |
| Pantalla OLED | Actuador | SDA: 21, SCL: 22 | aurabot/actuador/oled/central | aurabot/comando/oled/central | Expresión | "feliz", "neutral", "apagada" |
| DFPlayer Mini + Bocina | Actuador | TX: 17, RX: 16 | --- | aurabot/comando/audio/central | Pista / Comando | 1 a 30, "stop" |
| ESP32-WROVER | Cámara | N/A (Mapeo interno) | aurabot/sensor/camara/cam | --- | JPEG (Bytes) | 38,400 (QQVGA) |
