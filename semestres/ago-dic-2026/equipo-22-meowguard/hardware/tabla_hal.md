
# Hardware Abstraction Layer (HAL)

| # | Componente | Tipo | Pin ESP32 | Tópico Publicación | Tópico Suscripción | Unidad | Rango |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Ultrasonido HC-SR04 | Sensor | TRIG: 25 / ECHO: 35 | `meowguard/sensores/ultrasonico` | — | cm | 2 - 400 |
| 2 | HW-201 Izquierdo | Sensor | GPIO 32 | `meowguard/sensores/ir_izq` | — | Boolean | 0 / 1 |
| 3 | HW-201 Derecho | Sensor | GPIO 33 | `meowguard/sensores/ir_der` | — | Boolean | 0 / 1 |
| 4 | Motor Izquierdo | Actuador | GPIO 13 / 14 | — | `meowguard/actuadores/motores` | Cmd | adelante / detenido |
| 5 | Motor Derecho | Actuador | GPIO 23 / 18 | — | `meowguard/actuadores/motores` | Cmd | adelante / detenido |
| 6 | Atomizador | Actuador | GPIO por definir | — | `meowguard/actuadores/atomizador` | Boolean | ON / OFF |
