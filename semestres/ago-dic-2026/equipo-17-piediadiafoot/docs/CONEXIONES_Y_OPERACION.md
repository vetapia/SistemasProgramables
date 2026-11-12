# Conexiones físicas y operación — PIE DIABETICO - DIA FOOD

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 | 


## ESP32 DevKit V1 — asignación de pines propuesta

| Componente | Pin ESP32 | Observaciones |
|---|---:|---|
| Relevador motor 1 IN1 | GPIO32 | Activo en LOW según configuración actual |
| Relevador motor 2 IN2 | GPIO33 | Activo en LOW según configuración actual |
| Relevador ventilador + LEDs | GPIO26 | Activo en LOW según configuración actual |
| Servo SG90 / bandera LISTO | GPIO13 | Fuente externa adecuada; GND común de señal y servo |
| Buzzer | GPIO25 | Activo alto según prueba original |
| FSR402 ADC | GPIO34 | ADC1, entrada; divisor de 10 kΩ |
| HC-SR04 TRIG | GPIO14 | Salida |
| HC-SR04 ECHO | GPIO35 | Entrada; adaptar ECHO de 5 V a nivel seguro para ESP32 |
| I2C SDA | GPIO21 | Compartido por LCD y MLX90614 |
| I2C SCL | GPIO22 | Compartido por LCD y MLX90614 |
| OLED SCK | GPIO18 | SPI2 |
| OLED SDA/MOSI | GPIO23 | Es dato SPI, no SDA I2C |
| OLED DC | GPIO4 | Señal D/C |
| OLED RES | GPIO2 | Reset |
| OLED CS físico | GND | Mantener permanentemente seleccionado |
| OLED CS ficticio | GPIO19 | Sólo conectado al objeto `SSD1306_SPI`; NO conectarlo al pin CS de la pantalla |
| OLED MISO ficticio | GPIO39 | No conectar a la OLED; se reserva como MISO sin usar para evitar conflicto con GPIO34 del FSR |

### OLED — detalle importante

La prueba funcional fue SPI2 con CS físico de la pantalla a GND y un objeto de pin CS ficticio. En esta integración GPIO34 no se usa para MISO porque está ocupado por el FSR402. Se propone GPIO39 como MISO no conectado. Hay que validar que esta reasignación concreta mantenga el comportamiento en la placa durante la primera prueba de integración; si no, se deberá revisar el constructor SPI de la versión exacta de MicroPython sin cambiar el cableado CS físico probado.

### HC-SR04

El sensor está fijo, horizontal, apuntando hacia los dedos, aproximadamente 2 cm sobre el acrílico. La altura exacta y el alineamiento con la superficie de los dedos deben verificarse en el montaje. Nunca conectar el ECHO de 5 V directamente a la ESP32; usar divisor resistivo o adaptador lógico.

La referencia de 39 cm es la medida desde la cara frontal de los transductores hasta el plano del tope del talón. El cálculo preliminar es:

```text
longitud_estimada_pie = 39 cm - distancia_ultrasonico_a_dedos
centro_objetivo = 30 cm - longitud_estimada_pie / 2
ajuste_respecto_al_centro = centro_objetivo - 15 cm
```

El cálculo depende de que el sensor apunte en el eje longitudinal del pie y de que el talón permanezca contra el tope de referencia. 

### MLX90614

Ubicación prevista: lateral derecho, apuntando directamente al talón, sin tubo y sin acrílico entre el sensor y la piel. Antes de activar validación térmica automática, comprobar que el registro de temperatura de objeto responde y calibrar la diferencia/umbral en el montaje. `temperature_validation_enabled` queda en `false` inicialmente.

### FSR402

Colocado bajo el talón, con divisor de 10 kΩ. El programa usa `fsr_threshold=1000` y `fsr_release_threshold=850` como valores iniciales heredados de la prueba; no están calibrados para la maqueta terminada. La lectura ADC identifica apoyo, no mide presión clínica.

### Motor de banda y relevadores

La banda tendrá control manual por pulsos. La guía se reporta de 19 cm y el carro/cámara ocupa aproximadamente 6 cm; por geometría, el recorrido de centro del carro podría ser cerca de 13 cm en total, antes de márgenes.

El esquema de inversión que debe verificarse en el cableado instalado es: COM de cada relevador a cada cable del motor; NC de ambos al negativo de la fuente; NO de ambos al positivo de la fuente. La lógica activa sólo un relevador a la vez y ambos apagados es reposo. Verificar con multímetro y motor desconectado antes de aplicar potencia.

Los topes mecánicos propuestos evitan que el carro se salga, pero no desconectan eléctricamente el motor. Pulsos repetidos contra un tope pueden atascarlo y elevar corriente. Los topes por sí solos no equivalen a finales de carrera eléctricos.

### Alimentación

- No alimentar servo, motor, ventilador ni LEDs directamente desde GPIO.
- Usar fuentes adecuadas para los motores/actuadores.
- Confirmar polaridad, corriente, tierra y disipación antes de encender potencia.
- La tecla E es una parada lógica; conservar un interruptor físico de corte de potencia accesible.

## Comunicación de la ESP32-WROVER-CAM con el servidor de visión

La ESP32-WROVER-CAM se encarga de capturar imágenes del área de exploración y proporcionar los fotogramas al servidor de procesamiento mediante una conexión HTTP dentro de la red local.

A diferencia de los sensores y actuadores del ESP32 DevKit, la transmisión de imágenes no se realiza directamente mediante MQTT. Se utiliza un servidor HTTP local alojado en la propia ESP32-WROVER-CAM, mientras que MQTT se reserva para el intercambio de lecturas, estados, comandos y resultados del procesamiento.

### Funcionamiento de la transmisión

El proceso de comunicación se desarrolla de la siguiente manera:

1. **Inicialización de la cámara:** la ESP32-WROVER-CAM inicializa el módulo de cámara y establece su conexión con la red Wi-Fi.
2. **Servidor HTTP:** la placa habilita un servicio HTTP local para permitir que otros dispositivos de la misma red soliciten los fotogramas capturados.
3. **Solicitud de imagen:** el programa de la laptop, mediante `vision_mqtt.py`, realiza una solicitud HTTP GET al endpoint `/frame` de la ESP32-WROVER-CAM.
4. **Transmisión del fotograma:** la placa responde con los datos de imagen capturados en formato RGB565.
5. **Reconstrucción de imagen:** el servidor Python recibe los datos binarios y utiliza NumPy para reconstruir la matriz correspondiente al fotograma.
6. **Conversión y procesamiento:** la imagen se convierte al formato BGR utilizado por OpenCV y se envía al modelo YOLO para realizar el procesamiento y la detección de las zonas de interés.
7. **Publicación del resultado:** una vez procesado el fotograma, el servidor comunica los resultados y las decisiones correspondientes mediante los tópicos MQTT configurados en el sistema.

### Parámetros de comunicación

| Parámetro | Descripción |
|---|---|
| Dispositivo servidor | ESP32-WROVER-CAM |
| Dispositivo cliente | Laptop |
| Protocolo de transmisión | HTTP |
| Puerto | 80 |
| Método de solicitud | GET |
| Endpoint | `/frame` |
| Resolución configurada | QVGA (320 × 240 píxeles) |
| Formato de imagen | RGB565 |
| Procesamiento en laptop | NumPy, OpenCV y YOLO |

La dirección de acceso se construye utilizando la dirección IP local asignada a la ESP32-WROVER-CAM y el endpoint correspondiente:

`http://IP_DE_LA_ESP32_WROVER/frame`

La dirección IP debe coincidir con la configuración de red utilizada por el servidor Python.

### Distribución de protocolos

La arquitectura utiliza dos mecanismos de comunicación con responsabilidades diferenciadas:

- **HTTP:** permite solicitar y recibir los fotogramas capturados por la ESP32-WROVER-CAM.
- **MQTT:** permite intercambiar información entre el ESP32 DevKit y el servidor Python, incluyendo lecturas de sensores, estados de actuadores, comandos y resultados de procesamiento.

Esta separación permite manejar la transferencia de imágenes independientemente de los mensajes de control y supervisión del sistema.

### Consideraciones de operación

Para que la comunicación funcione correctamente se deben cumplir las siguientes condiciones:

- La ESP32-WROVER-CAM y la laptop deben encontrarse conectadas a la misma red local o contar con conectividad IP entre ellas.
- La dirección IP configurada en el servidor Python debe corresponder a la dirección actual de la ESP32-WROVER-CAM.
- El servicio HTTP de la placa debe estar inicializado antes de que la laptop solicite los fotogramas.
- El servidor Python debe contar con las dependencias necesarias para reconstruir y procesar las imágenes.
- El modelo YOLO debe encontrarse disponible en la ruta configurada para el equipo que ejecuta el procesamiento.

La transmisión de fotogramas permite incorporar el análisis visual al flujo de operación de PIE DIAFOOT sin utilizar MQTT para transportar directamente las imágenes.