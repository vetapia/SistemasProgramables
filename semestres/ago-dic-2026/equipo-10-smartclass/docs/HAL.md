# Tabla HAL — SmartClass

Pines y tópicos reales del sistema final. Los valores salen del código de cada nodo (`firmware/hal/main.py` y `firmware/cam/main.py`).

## Nodo dispensador (ESP32 DevKit) — `firmware/hal/main.py`

| # | Componente                   | Tipo     | Pin ESP32 | Tópico de publicación          | Tópico de suscripción | Unidad   | Rango válido |
|---|------------------------------|----------|-----------|--------------------------------|-----------------------|----------|--------------|
| 1 | Sensor IR de obstáculos (mano) | Sensor | GPIO 18   | `smartclass/s/ir_disp`         | —                     | Digital  | 0-1 (0 = mano detectada) |
| 2 | DHT11 (temperatura y humedad) | Sensor  | GPIO 4    | `smartclass/s/clima` (JSON)    | —                     | °C / %   | 0-50 °C / 20-90 % |
| 3 | Relevador de la bomba de gel | Actuador | GPIO 26   | `smartclass/e/bomba` (estado)  | `smartclass/a/bomba`  | Digital  | 0-1 (1 = una dosis de 1.2 s) |
| 4 | Relevador del ventilador     | Actuador | GPIO 27   | `smartclass/e/vent` (estado)   | `smartclass/a/vent`   | Digital  | `1`, `0` o `auto` (automático: enciende con más de 30 °C y apaga con 28 °C o menos) |

Además, el nodo publica su latido en `smartclass/nodo/dispensador` cada 10 s y se suscribe a `smartclass/config/wifi` para recibir una red WiFi nueva desde el dashboard.

## Nodo puerta (ESP32-WROVER con cámara OV2640) — `firmware/cam/main.py`

| #  | Componente                   | Tipo       | Pin ESP32        | Tópico de publicación        | Tópico de suscripción          | Unidad   | Rango válido |
|----|------------------------------|------------|------------------|------------------------------|--------------------------------|----------|--------------|
| 5  | Sensor IR de obstáculos      | Sensor     | GPIO 15          | `smartclass/s/ir`            | —                              | Digital  | 0-1 (0 = persona detectada) |
| 6  | Ultrasónico HC-SR04          | Sensor     | Trig: 32, Echo: 33 | `smartclass/s/distancia`   | —                              | cm       | 2-400 (una persona a menos de 60 cm activa el reconocimiento) |
| 7  | Cámara OV2640                | Cámara     | Pines internos de la placa | `smartclass/cam/frame` | —                           | JPEG     | Resolución VGA, calidad 15 |
| 8  | Anillo LED WS2812B (12 LEDs) | Actuador   | GPIO 2           | —                            | `smartclass/puerta/resultado`  | RGB      | 0-255 por canal |
| 9  | Buzzer activo                | Actuador   | GPIO 12          | —                            | `smartclass/puerta/resultado`  | Digital  | 0-1 |
| 10 | Pantalla OLED 0.96" (SSD1306) | Actuador  | I2C: SDA 13, SCL 14 | —                         | `smartclass/puerta/resultado`  | Texto    | 128 x 64 px |

Además, el nodo publica su latido en `smartclass/nodo/puerta` cada 10 s y se suscribe a:

- `smartclass/puerta/cmd`: comandos del registro de alumnos.
- `smartclass/s/clima`: temperatura y humedad que muestra en la pantalla.
- `smartclass/config/wifi`: red WiFi nueva enviada desde el dashboard.

## Respuesta de la puerta según el resultado del servidor

El servidor publica en `smartclass/puerta/resultado` un JSON con el campo `estado`:

| Estado        | Anillo LED | Buzzer | Pantalla                      |
|---------------|------------|--------|-------------------------------|
| `reconocido`  | Verde      | Corto  | "BIENVENIDO", nombre y hora   |
| `desconocido` | Rojo (si se repite en las 4 fotos) | Largo | "Alumno no registrado" |
| `sin_rostro`  | Rojo (si ninguna de las 4 fotos tiene rostro) | Largo | "No se detecta su rostro" |

## Todos los tópicos MQTT

| Tópico                        | Dirección              |
|-------------------------------|------------------------|
| `smartclass/cam/frame`        | Puerta → Servidor      |
| `smartclass/s/distancia`      | Puerta → Servidor      |
| `smartclass/s/ir`             | Puerta → Servidor      |
| `smartclass/s/clima`          | Dispensador → Servidor y Puerta |
| `smartclass/s/ir_disp`        | Dispensador → Servidor |
| `smartclass/e/bomba`          | Dispensador → Servidor |
| `smartclass/e/vent`           | Dispensador → Servidor |
| `smartclass/nodo/puerta`      | Puerta → Servidor      |
| `smartclass/nodo/dispensador` | Dispensador → Servidor |
| `smartclass/puerta/resultado` | Servidor → Puerta      |
| `smartclass/puerta/cmd`       | Servidor → Puerta      |
| `smartclass/a/bomba`          | Dashboard o pruebas → Dispensador |
| `smartclass/a/vent`           | Dashboard o pruebas → Dispensador |
| `smartclass/config/wifi`      | Servidor → Puerta y Dispensador |
