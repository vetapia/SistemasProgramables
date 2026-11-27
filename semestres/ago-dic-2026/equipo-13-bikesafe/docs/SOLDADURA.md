# 🔥 Guía de soldadura: de protoboard a placa perforada

**Por qué:** en una bicicleta hay vibración constante. Un cable Dupont que se afloja en la demo apaga un sensor (o la alarma entera). En la placa fenólica todo queda **soldado, compacto y firme**.

![Placa perforada](../hardware/placa-perforada.png)

## Material

| Qué | De dónde |
|---|---|
| Cautín + estaño | Préstamo de la maestra |
| Placa fenólica perforada | Regalo de la maestra |
| Tiras de headers **hembra** (para la ESP32 y el MPU6050) y **macho** (conectores) | Kit / papelería electrónica |
| Alambre calibre 22 (rígido) para rieles y puentes | Kit |
| Reed switch + imán chico | Por comprar (~$20–$30 MXN) |
| LED RGB y buzzer | Préstamo de la maestra |
| Cinchos (cable ties) | Ferretería |

## Lista de conexiones (netlist)

Todas las piezas comparten **GND**. La Freenove va con su propio USB, pero su GND **debe** ir al riel GND de esta placa.

| # | Desde | Hacia | Nota |
|---|---|---|---|
| 1 | ESP32 **3V3** | Riel 3.3 V | Alimenta al MPU6050 |
| 2 | Powerbank **5 V** | Riel +5 V | Servo, HC-SR04 |
| 3 | ESP32 **GND** | Riel GND | |
| 4 | MPU6050 VCC / GND / SDA / SCL | 3.3 V / GND / **GPIO21** / **GPIO22** | Headers hembra |
| 5 | HC-SR04 VCC / GND / TRIG | +5 V / GND / **GPIO26** | Conector de 4 pines hacia la pared frontal |
| 6 | HC-SR04 ECHO | 1 kΩ → nodo → **GPIO27**; nodo → 2 kΩ → GND | Divisor 5 V → 3.3 V (no omitirlo) |
| 7 | Reed switch | **GPIO18** y GND | Sin resistencia: pull-up interna |
| 8 | Lazo anti-corte | **GPIO14** y GND | Sin resistencia: pull-up interna |
| 9 | Servo: señal (naranja) / + (rojo) / − (café) | **GPIO13** / +5 V / GND | |
| 10 | Buzzer (+) / (−) | **GPIO25** / GND | Directo, sin el 2N2222 |
| 11 | LED RGB: R / G / B | 220 Ω → **GPIO33** / 220 Ω → **GPIO32** / 220 Ω → **GPIO19** | Patita larga: GND (cátodo común) o 3.3 V (ánodo común) |
| 12 | ESP32 **TX2 (17)** → Freenove **GPIO33** | | Cruzados |
| 13 | ESP32 **RX2 (16)** ← Freenove **GPIO32** | | Cruzados |
| 14 | Capacitor 1000 µF | +5 V y GND | Pata corta (−) a GND |
| 15 | Capacitor 470 µF | 3.3 V y GND | Pata corta (−) a GND |

## Orden de trabajo

1. **Práctica (20 min):** soldar 10 uniones con cables viejos. Una buena unión es brillante, en forma de cono, y el cable no se mueve al jalarlo.
2. **Headers hembra** para la ESP32 y el MPU6050. Así las placas se pueden quitar sin desoldar.
3. **Rieles** de +5 V, 3.3 V y GND con alambre desnudo por la cara de abajo.
4. **Resistencias:** el divisor 1 kΩ/2 kΩ y las 3 de 220 Ω del LED RGB.
5. **Conectores** (tiras macho) para todo lo que sale a la carcasa: servo, HC-SR04, reed, lazo y UART.
6. **Capacitores,** respetando la polaridad.
7. **Revisión con multímetro antes de conectar la energía:**
   - continuidad +5 V ↔ GND → **no debe pitar** (si pita hay un corto, como el que tuvimos con el RFID);
   - continuidad 3.3 V ↔ GND → **no debe pitar**;
   - continuidad de cada GPIO a su conector → **sí debe pitar**.
8. Correr las pruebas de `firmware/pruebas/`: `e13_led_rgb.py`, `e14_cerrojo_reed.py`, `e02_servo.py`, `e03_mpu6050.py`, `e09_ultrasonico.py`, `e08_buzzer.py` y `e11_lazo.py`.

## Errores que hay que evitar

- **Puentes de estaño** entre pines vecinos. Revisar con lupa (o la cámara del celular) cada fila de la ESP32.
- Calentar el **reed switch** mucho tiempo o doblarlo pegado al vidrio, porque se estrella. Hay que doblar sus patitas a 3 mm del cuerpo.
- Dejar el cautín sin estaño en la punta, porque se oxida y deja de pegar.
- Soldar con la placa **energizada**. Siempre se suelda desconectado.
