# Tabla HAL — ESP32 principal

| Componente | Señal | GPIO | Conexión |
|---|---|---:|---|
| L298N | Adelante derecha | 23 | Entrada lógica de ambos puentes para los motores derechos |
| L298N | Adelante izquierda | 13 | Entrada lógica de ambos puentes para los motores izquierdos |
| L298N | Atrás derecha | 18 | Entrada lógica de ambos puentes para los motores derechos |
| L298N | Atrás izquierda | 14 | Entrada lógica de ambos puentes para los motores izquierdos |
| HC-SR04 frontal | TRIG | 25 | Salida digital |
| HC-SR04 frontal | ECHO | 26 | Entrada con adaptación de 5 V a 3.3 V |
| HW-201 trasero | OUT | 35 | Entrada. Activo en 0 por defecto. Adapta el nivel si OUT da 5 V |
| MPU | SDA | 21 | I²C; resistencias de polarización a 3.3 V |
| MPU | SCL | 22 | I²C; resistencias de polarización a 3.3 V |
| MPU | VCC, GND, AD0 | — | 3V3, GND común, AD0 a GND para 0x68 |
| MPU | INT | — | Libre |
| Servo de atomizador | Señal | Por asignar | Opcional, alimentación adecuada para el servo y GND común |
| Atomizador | Habilitación | Por asignar | Etapa externa de potencia con reposo apagado |
| Ventilador | Habilitación | Por asignar | Etapa externa de potencia |
| Cuatro encoders | Salida de pulsos | Por asignar | Una entrada de 3.3 V por rueda |

GPIO 26 para ECHO procede del firmware anterior y se conserva como supuesto de montaje. GPIO 35 es el acordado para proximidad. Si tu HC-SR04 ya usa otro GPIO, edita `ECHO_PIN` y comprueba que sea distinto del HW-201. Los cuatro GPIO de motor y los dos de I²C coinciden con el acuerdo más reciente. La ESP32-CAM es otra placa y conserva el pinout del módulo AI Thinker.

## Conexiones de referencia

- Si el canal A de ambos L298N corresponde al lado izquierdo, lleva GPIO 13 a IN1, GPIO 14 a IN2, GPIO 23 a IN3 y GPIO 18 a IN4 en cada módulo. Si montaste los canales al revés, conserva la asignación por lado. Cada motor se conecta a su propio par OUT. Prueba el sentido con las ruedas elevadas.
- Para el PWM en las entradas IN, los canales deben estar habilitados. Usa los jumpers ENA y ENB de tu módulo si ya usabas esa configuración. El jumper de regulación de 5 V del módulo cumple una función distinta. La pausa de inversión se aplica con ambas entradas a nivel bajo.
- Alimenta motores, servo, cámara y atomizador desde fuentes o reguladores acordes con cada placa y con la corriente requerida. En las señales cableadas del ESP32 principal usa GND común. La ESP32-CAM se comunica por Wi-Fi.
- Para ECHO en un HC-SR04 de 5 V puedes usar una resistencia de 10 kΩ entre ECHO y el nodo GPIO 26 y una de 15 kΩ entre el nodo y GND, que dan aproximadamente 3.0 V para un pulso de 5 V. Confirma también el voltaje de salida del HW-201 antes de conectarlo a GPIO 35. GPIO 35 sólo es de entrada y carece de polarización interna.
- Si habilitas encoders, usa salidas de 3.3 V o adaptación de nivel. Los GPIO 34–39 disponibles en tu DevKit son entradas y requieren polarización externa si el encoder es de colector abierto. Configura los PPR tras medir los pulsos por vuelta de rueda.
- Al iniciar, verifica que la etapa externa del atomizador permanezca apagada hasta que el firmware la habilite. Si el módulo necesita pulsar un botón, prueba la posición de reposo y el recorrido del servo antes de completar la instalación.

[Esquemático de conexiones](diagrama.png) · [Arquitectura del sistema](arquitectura.png)

Referencias del componente: [ESP32](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf), [L298](https://www.st.com/resource/en/datasheet/l298.pdf), [MPU-9250](https://invensense.tdk.com/wp-content/uploads/2015/02/RM-MPU-9250A-00-v1.6.pdf).
