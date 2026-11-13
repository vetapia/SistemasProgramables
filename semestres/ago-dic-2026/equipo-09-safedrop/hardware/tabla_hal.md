# SafeDrop — Tabla HAL (equipo 09)

**Integrantes:** Alan Medina Rivas (23240436) · Victor Hugo Ojeda Cabrera (23240390)

**Semestre:** ago-dic-2026 · **Estado:** pines del montaje integrado
definidos. Los componentes individuales se probaron por separado; falta
comprobar su funcionamiento simultáneo.

## Hardware integrado

| # | Componente | Tipo | Pin ESP32 de control | Tópico publicación | Tópico suscripción | Estado |
|---|---|---|---|---|---|---|
| 1 | PIR HC-SR501 | Sensor | GPIO27 (OUT) | `safedrop/sensores/pir` | — | Probado individualmente por MQTT |
| 2 | LDR LM393 (AO) | Sensor | GPIO34 (ADC1) | `safedrop/sensores/ldr` | — | Probado individualmente por MQTT |
| 3 | HC-SR04 | Sensor | GPIO18 TRIG / GPIO19 ECHO con divisor | `safedrop/sensores/distancia` | — | Probado individualmente por MQTT |
| 4 | Relé 5 V 2 canales (canal 1) | Actuador iluminación | GPIO26 IN1 | `safedrop/estado/rele` | `safedrop/rele/cmd` | MQTT probado; prueba unitaria con foco en caja protegida reportada |
| 5 | Servo SG90 | Actuador cerradura | GPIO23 PWM | `safedrop/estado/puerta` | `safedrop/puerta/cmd` | Movimiento físico con alimentación regulada probado; MQTT conjunto por verificar |
| 6 | Buzzer activo 3.3 V | Actuador aviso | GPIO25 | `safedrop/eventos/objeto` (evento del sistema) | `safedrop/buzzer/cmd` | Probado individualmente por MQTT |
| 7 | Foco 120/127 V | Carga del relé, **fuera de protoboard** | Sin GPIO directo; se conmuta por relé | — | — | Prueba unitaria con caja protectora reportada; montaje final por revisar |
| 8 | ESP32-S3 + OV3660 | Visión, MCU separado | No comparte GPIO con ESP32 de control | Captura RGB565 por TCP al servidor | — | Cámara y QR probados; puente MQTT por integrar |
| 9 | Celda de carga 5 kg + HX711 | **Sensor no convencional** | GPIO32 DT / GPIO33 SCK | `safedrop/sensores/peso_raw` (cuentas sin calibrar) | — | **Recibido**; driver y prueba añadidos, cableado/lectura/calibración pendientes |

**Sensor no convencional confirmado:** celda de carga de 5 kg con módulo HX711, ya recibido. Terminales previstos: DOUT/DT GPIO32 y SCK GPIO33. Requiere confirmar soldaduras, instalación mecánica, lecturas reales y calibración.

## Distribución de alimentación y señales

- **3V3 ESP32:** LDR LM393 y módulo HX711 de cuatro pines si su VCC admite 3.3 V. Buzzer de 3.3 V según su consumo; la versión de prueba lo conmuta por GPIO25.
- **5 V externos regulados, suficientes para el conjunto:** VCC del PIR,
  HC-SR04, relé y positivo del SG90. Para el SG90 preferir conexión de
  alimentación directa desde la fuente y no a través de pistas finas de
  protoboard. ESP32 estándar alimentada por USB.
- **GND común en baja tensión:** unir todos los GND del lado de 3.3/5 V
  con GND de ESP32, incluido el negativo de la fuente de servo.
- **HC-SR04:** ECHO (5 V) → 1 kΩ → nodo GPIO19 → 2 kΩ → GND.
  No conectar ECHO directamente al ESP32.
- **PIR:** OUT → GPIO27, comprobar nivel alto de la salida (≤3.3 V).
- **LDR:** AO → GPIO34; DO sin conectar.
- **Relé:** IN1 → GPIO26, IN2 sin usar; módulo probado activo en LOW.
- **Servo SG90:** señal naranja → GPIO23, rojo → +5 V regulados, marrón → GND compartido.
  Posiciones programadas inicialmente 0° (cerrado), 90° (abierto).
- **HX711:** VCC → 3V3 (si admite 3.3 V), GND → común, DOUT/DT → GPIO32,
  SCK → GPIO33. Barra de carga: rojo → E+, negro → E-, blanco → A-, verde → A+,
  según los colores indicados en el kit. Montar un extremo fijo y otro en plataforma.

La instalación del foco de red doméstica requiere un circuito
**aislado, protegido y dentro de una caja adecuada**, con cableado
realizado o revisado por personal calificado. Nunca llevar fase/neutro
de 120/127 V a la protoboard ni a los rieles de la ESP32.
El equipo reportó prueba unitaria del foco con relé en caja de protección;
la inspección eléctrica del montaje definitivo sigue siendo necesaria.

## Comportamiento esperado del firmware integrado

- PIR + LDR en modo AUTO → relé de iluminación. Se mantiene encendido
  30 segundos desde el último movimiento mientras permanezca oscuro;
  nueva detección reinicia el tiempo. Un retorno de luz lo apaga.
- HC-SR04 cerca de objeto nuevo (≤15 cm tras 2 lecturas)
  → buzzer de 250 ms y evento MQTT.
- Relé admite `AUTO`, `ON`, `OFF`.
- Servo admite `ABRIR`, `CERRAR`.
- Buzzer admite `ON` y `OFF`.
- HX711: al habilitar `HX711_HABILITADO = True` tras su prueba, publica
  cuentas sin calibrar en `safedrop/sensores/peso_raw`. Los gramos requieren
  tara y calibración con masa conocida.

Los umbrales LDR 3000/2500 y distancias 15/20 cm son
valores iniciales para calibración. No existe actualmente un sensor
que confirme que la puerta alcanzó el ángulo ordenado.

## Pruebas y pendientes

- [x] PIR, LDR, HC-SR04, relé y buzzer probados individualmente
- [x] SG90 con movimiento físico probado
- [x] Código conjunto de sensores y actuadores; interfaz HX711 opcional incluida
- [ ] Validar funcionamiento simultáneo del circuito completo
- [ ] Verificar alimentación y torque del SG90 en la cerradura
- [x] Prueba unitaria del relé y foco con caja de protección, reportada por el equipo
- [ ] Revisar el aislamiento y el cableado del conjunto definitivo del foco
- [x] Recibir el módulo HX711 y la celda de carga de 5 kg
- [ ] Soldar pines si corresponde, conectar y probar lecturas del HX711
- [ ] Conectar decisión QR del servidor Python al tópico del SG90
- [ ] Montar mecánicamente la celda y calibrar con masa conocida
- [ ] Agregar fotos del circuito, esquema y evidencia de MQTT

La cámara ESP32-S3 se alimenta por USB aparte y envía imágenes
por Wi-Fi al servidor Python. Su flujo TCP de imágenes ya fue probado;
el MQTT de autorización y Firebase siguen en desarrollo.
