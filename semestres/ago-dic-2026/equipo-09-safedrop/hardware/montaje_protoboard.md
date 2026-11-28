# SafeDrop — Guía práctica de montaje en protoboard

**Equipo 09 · Sistemas Programables · ago-dic-2026**  
**Integrantes:** Alan Medina Rivas (23240436) y Victor Hugo Ojeda Cabrera (23240390)

## Alcance

Unificar **ESP32 de control**, PIR HC-SR501, LDR LM393, HC-SR04,
**relé de 5 V**, buzzer activo de 3.3 V y **servo SG90**. El foco doméstico
depende del relé pero **NO se cablea en la protoboard**; su circuito
de corriente alterna va en caja protegida, instalado o revisado por
personal calificado. El **HX711 con celda de carga de 5 kg ya se recibió**
y se agrega al esquema. Antes de medir peso hay que soldar los terminales
si vienen sueltos, comprobar las conexiones y calibrar el sensor.

La **ESP32-S3 con cámara OV3660** usa alimentación USB propia y se
comunica por Wi-Fi con el servidor Python en la PC; **no** necesita
jumpers hacia la ESP32 de control.

## Material mínimo de baja tensión

- Una ESP32 estándar, ESP32-S3 con cámara, protoboard y jumpers.
- PIR, módulo LDR LM393, HC-SR04, módulo relé 2 canales 5 V, buzzer
  activo de 3.3 V, servomotor SG90 y **celda de carga 5 kg + HX711**.
- Resistencias para divisor de voltaje del ECHO: **2.2 kΩ + 3.3 kΩ**
  (equivale a aproximadamente 3.0 V de salida). El divisor previo de
  1 kΩ + 2 kΩ también sirve si ya fue probado.
- Fuente regulada de 5 V con corriente suficiente para el servo y
  relé (orientación: 5 V, 2 A), con un adaptador de salida a terminales
  que permita conectar cables de baja tensión.
- ESP32 estándar alimentada por su USB desde la PC.

## Paso 1 — Alimentación, SIN enchufar

1. Desconectar todo y colocar ESP32 estándar sobre la ranura central.
2. Identificar riel **3V3** y riel **GND** en la protoboard.
3. Llevar el 3V3 de la placa al riel de 3.3 V.
4. Llevar GND de la placa al riel GND de la protoboard.
5. Distribuir 5 V de la **fuente externa regulada** a un riel **distinto**,
   identificado como +5 V, y su negativo al GND común.
6. Para el SG90, alimentar cable rojo y marrón desde el ramal de la
   fuente 5 V con buena conexión (preferentemente directo, no por
   pistas de protoboard que puedan calentarse con picos).
7. **No unir +5 V con 3V3, ni introducir +5 V al GPIO.**
   Tampoco unir directamente dos salidas de fuentes +5 V.

## Paso 2 — Cableado de señales

| Componente | Terminal | Destino |
|---|---|---|
| PIR HC-SR501 | VCC, OUT, GND | +5 V, GPIO27, GND |
| LDR LM393 | VCC, GND, AO, DO | 3V3, GND, GPIO34, libre |
| HC-SR04 | VCC, GND, TRIG, ECHO | +5 V, GND, GPIO18, divisor a GPIO19 |
| Relé 5 V (canal 1) | VCC, GND, IN1, IN2 | +5 V, GND, GPIO26, libre |
| Buzzer activo 3.3 V | positivo, negativo | GPIO25, GND (solo corriente compatible) |
| SG90 | naranja, rojo, marrón | GPIO23, +5 V estable, GND común |
| HX711 5 kg | VCC, GND, DT/DOUT, SCK | 3V3, GND, GPIO32, GPIO33 (verificar módulo 3.3 V) |
| Celda 5 kg | rojo, negro, blanco, verde | HX711 E+, E-, A-, A+ respectivamente |

**PIR:** comprobar que OUT no supere los 3.3 V compatibles con ESP32.

**Buzzer:** no alimentar un buzzer de corriente elevada directamente
desde GPIO; usar etapa de transistor si su consumo supera la capacidad
del pin.

## Paso 3 — Divisor ECHO de HC-SR04

```text
HC-SR04 ECHO --- [2.2 kΩ] ---+--- GPIO19 ESP32
                             |
                           [3.3 kΩ]
                           |
                          GND
```

El HC-SR04 estándar entrega ECHO de 5 V, por eso no puede ir directo
al GPIO19. **R superior:** 2.2 kΩ desde ECHO al nodo del GPIO19.
**R inferior:** 3.3 kΩ desde ese nodo a GND. Si ya está funcionando con
1 kΩ y 2 kΩ, conservarlo; no hacen falta nuevas resistencias.

## Paso 4 — Foco doméstico por relé

El software ordena activar el **canal 1 del relé en GPIO26**.
La lámpara de 120/127 V solo debe cablearse mediante un circuito
de alimentación de red **cerrado, aislado y protegido**, instalado o
revisado por personal calificado, o mediante conjunto de tomacorriente
con relé preensamblado apto para red eléctrica. No llevar fase, neutro,
contactos de potencia ni cables pelados de red a la protoboard.

El equipo **ya reportó una prueba unitaria del relé con el foco** dentro
de una caja de protección. Al modificar sensores y cables de la
protoboard, desconectar primero toda alimentación y no manipular
la instalación de red. La prueba del programa conjunto debe confirmar
el estado del relé antes de operar la iluminación; mantener el montaje
eléctrico aislado y bajo revisión calificada.

## Paso 5 — Preparar el HX711 de 5 kg

1. Comprobar las etiquetas **E+, E-, A+, A-**, `VCC`, `GND`, `DT/DOUT`
   y `SCK` del modelo recibido. Si los pines vienen sueltos, necesitan
   soldadura firme; no confiar en un contacto apoyado en la protoboard.
2. Alimentar desde **3V3** de la ESP32 si el breakout admite 3.3 V.
   Conectar `GND` común, `DT/DOUT → GPIO32` y `SCK → GPIO33`.
3. Según el kit: cable **rojo → E+**, **negro → E-**,
   **blanco → A-**, **verde → A+**.
4. Sujetar mecánicamente un extremo de la barra y apoyar la plataforma
   de pesaje en el otro extremo; comprobar orientación y no exceder 5 kg.
5. En la ESP32 copiar `hx711.py` y ejecutar `hx711_prueba.py` con
   la plataforma vacía al inicio. Verificar que las cuentas RAW cambian
   al poner un objeto; después calibrar con una masa conocida.
6. En `safedrop_integrado.py`, cambiar `HX711_HABILITADO = False` a
   `True` y copiar también `hx711.py` para publicar las cuentas por MQTT.
   No llamar gramos a estos valores hasta completar la calibración.

## Paso 6 — Colocar firmware

- En ESP32 estándar: `config.py` privado con `WIFI_SSID`,
  `WIFI_PASSWORD`, `BROKER_IP` (IP de PC con Mosquitto).
- Ejecutar en Thonny `firmware/esp32-control/safedrop_integrado.py`.
- No ejecutar simultáneamente scripts individuales sobre la misma placa.
- La cámara ESP32-S3 sigue ejecutando su propio firmware y el servidor
  Python de la PC recibe por TCP puerto 5000.

## Paso 7 — Pruebas MQTT en Windows CMD

Suscripción para ver todos los mensajes:

```cmd
"C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -t "safedrop/#" -v
```

Comandos de prueba, uno por uno:

```cmd
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t safedrop/rele/cmd -m ON
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t safedrop/rele/cmd -m OFF
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t safedrop/rele/cmd -m AUTO
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t safedrop/puerta/cmd -m ABRIR
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t safedrop/puerta/cmd -m CERRAR
"C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -t safedrop/buzzer/cmd -m ON
```

Tras aproximadamente 30 segundos de estabilización del PIR, se
publican lecturas de PIR, LDR y HC-SR04. Al habilitar el HX711 se
publican también sus cuentas sin calibrar. En modo AUTO, activar movimiento y
oscurecer el LDR debe activar el relé (sin foco conectado durante
las pruebas eléctricas iniciales). En modo AUTO, el relé debe permanecer
encendido 30 segundos desde la última detección del PIR, excepto si vuelve
la claridad. Llevar objeto a menos de 15 cm
del HC-SR04 desde una condición libre debe emitir un pitido.

**SG90:** verificar movimientos ABRIR/CERRAR sin varillaje ni bloqueo,
calibrando valores antes de fijar la cerradura.

## Funcionamiento esperado

- `safedrop/sensores/pir`, `.../ldr`, `.../distancia`: telemetría.
- `safedrop/sensores/peso_raw`: cuentas HX711 al habilitarlo, sin calibrar.
- `safedrop/rele/cmd`: ON, OFF y AUTO (automático por PIR + oscuridad).
- `safedrop/puerta/cmd`: ABRIR y CERRAR; no es validación QR.
- `safedrop/buzzer/cmd`: ON produce pitido corto.
- `safedrop/estado/rele`, `safedrop/estado/puerta`: estados ordenados.

**Pendiente por probar:** todo al mismo tiempo, torque mecánico real
del servo, prueba y calibración del HX711, verificación del sistema de foco
instalado en caja y autorización QR antes de abrir la puerta. Las pruebas
unitarias de relé/foco y movimiento SG90 ya fueron reportadas; el sistema
completo todavía requiere validación simultánea.
