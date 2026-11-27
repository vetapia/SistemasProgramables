# BikeSafe — Alarma y bloqueo disuasorio portátil para bicicletas

![Estado](https://img.shields.io/badge/estado-entrega%20final-blue)
![Semestre](https://img.shields.io/badge/semestre-ago--dic--2026-blue)
![Materia](https://img.shields.io/badge/materia-Sistemas%20Programables-orange)

> **Semestre:** ago-dic-2026
> **Materia:** Sistemas Programables — ISC TecNM León
> **Equipo:** 13 · Horario 10
> **Integrantes:**

| Nombre | Matrícula | Rol | GitHub |
|--------|-----------|-----|--------|
| Oscar Sandoval Cabrera | 23240457 | 🔧 Firmware ESP32 · 🧠 Servidor Python/IA · ☁️ Firebase/Interfaz | [@Sand027](https://github.com/Sand027) |
| Diego Josué Talamantes Santiago | 23240355 | 🔩 Hardware/Carcasa/Soldadura · 📝 Documentación | [@josuegoku2203-creator](https://github.com/josuegoku2203-creator) |

> 📋 **Revisión del 25 de noviembre:** cada observación de la maestra y lo que se cambió está en [docs/REVISION.md](docs/REVISION.md).

---

## 📌 Descripción General

- **¿A quién ayuda?** A estudiantes y trabajadores que dejan su bicicleta en bici-estacionamientos públicos (escuela, trabajo, centro), donde los robos son frecuentes y los candados comunes se cortan en segundos.
- **¿Qué problema resuelve?** Un candado normal no avisa: el dueño se entera del robo cuando regresa. BikeSafe vigila la bici, distingue un roce de un intento de robo, toma fotos del sospechoso y avisa al celular al instante.
- **¿Qué lo hace diferente?** Es **portátil** (va en la mochila y sirve en cualquier estacionamiento). Se controla desde un **bot de Telegram** o un **dashboard web**, sin llaves. Tiene una **alarma de dos niveles** para no sonar con cada roce. Usa **detección de personas con IA (YOLOv5)** como evidencia extra. **Todas las decisiones se toman en la ESP32**, así que funciona aunque la laptop esté apagada.

### Alcance y límites mecánicos (honestos)

BikeSafe es un **sistema de alarma y bloqueo disuasorio**, no una cadena de alta seguridad:

| Sí hace | No pretende |
|---|---|
| Detectar el intento de robo en segundos (sacudida, inclinación, cerrojo forzado, cable cortado) y avisar con sirena, luz, fotos y Telegram | Resistir una cizalla o un esmeril. El cable de acero de un candado comercial (~8–12 mm) se corta en segundos con herramienta |
| Impedir que se lleven la bici "rodando": el pasador del servo traba el cable de acero alrededor del **tubo del cuadro** y del estacionamiento | Sustituir a un candado en U certificado. Recomendamos usarlo **junto** con uno |
| Disuadir: sirena de 60 s, luz roja y la evidencia fotográfica | Funcionar sin energía. Con una powerbank de 10 000 mAh dura ~10–12 h vigilando |

La sujeción al cuadro es con una **abrazadera sin fin (tipo gusano) de acero inoxidable** con almohadilla de hule, no con la cinta de tela del prototipo anterior. El **sensor magnético (reed switch)** confirma que el cable de verdad está metido en el cerrojo: si no lo está, el candado **no se asegura**, y si lo sacan a la fuerza estando asegurado, es **robo**.

---

## 🏗️ Arquitectura del Sistema

![Arquitectura del sistema](hardware/arquitectura.png)

- **ESP32 normal (el cerebro):** lee los 3 sensores, ejecuta la máquina de estados y la **alarma de 2 niveles**, mueve los 3 actuadores y **decide qué hacer con lo que reporta la IA**. Rechaza cualquier mensaje MQTT que no venga firmado (HMAC-SHA256).
- **Freenove ESP32-WROVER (el fotógrafo):** toma las fotos que le pide la ESP32 por UART y las manda a Telegram y al servidor. También atiende el **bot de Telegram** y le pasa los botones a la ESP32 como `CMD|asegurar`.
- **Servidor Python (laptop):** pasa cada foto por **YOLOv5** (detección de personas) y **solo informa** el resultado firmado a la ESP32. Guarda todo en Firestore y **escucha en tiempo real** los comandos que manda el dashboard.
- **Dashboard web:** inicia sesión con Google, muestra todo en vivo (`onSnapshot`) y tiene botones de control que se escriben en Firestore.

![Máquina de estados](hardware/maquina-estados.png)

### ¿Qué pasa si se apaga la laptop?

Nada grave. La alarma, la sirena, las fotos y el bot de Telegram viven en las **dos placas**. Sin laptop solo se pierde la confirmación de la IA y el historial en Firebase. Si se cae el internet, el candado sigue vigilando y sonando, y las alertas se guardan y se mandan cuando vuelve la conexión.

### Tópicos MQTT

| Tópico | Dirección | Descripción |
|--------|-----------|-------------|
| `bikesafe/sensor/distancia` | ESP32 → Broker | Distancia del HC-SR04 (cm, mediana de 3) |
| `bikesafe/sensor/movimiento` | ESP32 → Broker | Cambio de aceleración del MPU6050 (g) |
| `bikesafe/sensor/inclinacion` | ESP32 → Broker | Inclinación de la bici (°) |
| `bikesafe/sensor/cerrojo` | ESP32 → Broker | Reed switch: `CERRADO` / `ABIERTO` |
| `bikesafe/sensor/lazo` | ESP32 → Broker | Lazo anti-corte: `ENTERO` / `CORTADO` |
| `bikesafe/sensores` | ESP32 → Broker | Todas las lecturas en JSON (cada 2 s), con el color del LED |
| `bikesafe/estado` | ESP32 → Broker | `LIBRE` / `ASEGURADA` / `ALARMA` (retenido) |
| `bikesafe/conexion` | ESP32 → Broker | `online`; `offline` lo publica el broker si la ESP32 se cae (*last will*) |
| `bikesafe/alerta` | ESP32 → Broker | Texto de cada aviso o robo |
| `bikesafe/evento` | ESP32 → Broker | JSON de cada cambio de estado, comando y origen (historial) |
| `bikesafe/cam/info` · `bikesafe/cam/frame` | ESP32-CAM → Broker | Nivel/motivo y foto JPEG 320×240 |
| `bikesafe/ia/resultado` | Servidor → ESP32 | **Firmado.** `{"clase", "conf", "personas"}`: la ESP32 decide |
| `bikesafe/cmd` | Servidor → ESP32 | **Firmado.** `asegurar` · `liberar` · `silenciar` · `foto` · `buscar` |
| `bikesafe/servo/cmd` | Broker → ESP32 | Actuador 1 (firmado): `cerrar` / `abrir` |
| `bikesafe/buzzer/cmd` | Broker → ESP32 | Actuador 2 (firmado): `pitido` / `sirena_off` |
| `bikesafe/led/cmd` | Broker → ESP32 | Actuador 3 (firmado): `alerta` / `normal` / `<color>` |

**¿Por qué firmar?** `broker.hivemq.com` es público, así que cualquiera que adivine el tópico podría publicar `liberar`. Por eso cada mensaje hacia la ESP32 va como `orden|contador|firma`, donde la firma es HMAC-SHA256 con una clave que **nunca viaja por la red** ([firma.py](firmware/esp32/firma.py)). Sin la clave, la firma no sirve. Y como el contador siempre crece y se guarda en la flash, un mensaje grabado y repetido también se rechaza.

---

## 🛠️ Hardware

| # | Componente | Tipo | Cant. | Costo MXN | Origen |
|---|-----------|------|------|-----------|--------|
| 1 | ESP32 DevKit (WROOM-32) | Microcontrolador | 1 | $120 | Kit ESP32 propio |
| 2 | Freenove ESP32-WROVER con cámara GC0308 | Cámara | 1 | $420 | Compra |
| 3 | Acelerómetro MPU6050 | **Sensor 1** | 1 | $60* | Préstamo de la maestra |
| 4 | Ultrasónico HC-SR04 | **Sensor 2** | 1 | $45* | Préstamo de la maestra |
| 5 | Interruptor magnético (reed switch) + imán | **Sensor 3** | 1 | $25 | Compra |
| 6 | Servo SG90 (pasador del cerrojo) | **Actuador 1** | 1 | $50* | Préstamo de la maestra |
| 7 | Buzzer | **Actuador 2** | 1 | $5* | Préstamo de la maestra |
| 8 | LED RGB + 3 resistencias 220 Ω | **Actuador 3** | 1 | $10* | Préstamo de la maestra |
| 9 | Lazo anti-corte (cable que recorre el cable de acero) | Sensor extra | 1 | $15 | Compra |
| 10 | Divisor 1 kΩ/2 kΩ, capacitores 1000 µF, 470 µF y 2 × 104 | Energía | — | $31 | Compra |
| 11 | Placa fenólica perforada, estaño y headers | Estructura | 1 | $25 | Placa regalada por la maestra + headers |
| 12 | Carcasa impresa en 3D (PETG) | Estructura | 1 | $150 | Impresión con Gael |
| 13 | Cable de acero + abrazadera sin fin inoxidable | Sujeción | 1 | $150* | Por comprar |
| 14 | Powerbank USB + cable "Y" | Energía | 1 | $0 | Propia |
| | **Gastado por el equipo** (2, 5, 9, 10, 11, 12) | | | **$666** | |
| | **Costo total del prototipo** (con kit, préstamos y sujeción) | | | **$1,106** | |

\* Precio de referencia en tiendas en línea de México. No lo pagamos: es préstamo o todavía no se compra.
El RFID RC522 ($80) se compró y se descartó (ver Retos), así que no se cuenta.

> **Sobre el límite de $800:** lo que el equipo gastó ($666) entra en el presupuesto. El costo total lo rebasa, sobre todo por la Freenove ($420). La elegimos porque se programa directo por USB-C y trae PSRAM para las fotos; la ESP32-CAM común es más barata, pero necesita una base programadora aparte.

### Diagrama de conexiones y placa soldada

![Placa perforada](hardware/placa-perforada.png)

Lista completa de conexiones y procedimiento de soldadura: **[docs/SOLDADURA.md](docs/SOLDADURA.md)**.

| Más diagramas | |
|---|---|
| [Protoboard (versión anterior, sin RFID)](hardware/protoboard-sin-rfid.png) | [Alimentación y rieles](hardware/energia.png) |
| [Diagrama de bloques](hardware/bloques.png) | [Diagrama de conexiones anterior](hardware/diagrama-sin-rfid.png) |

### Carcasa impresa en 3D

![Carcasa BikeSafe](hardware/carcasa-3d/render_frente.png)

Caja de PETG (181 × 146 × 75 mm armada) diseñada en OpenSCAD y paramétrica. Tiene orificios para el HC-SR04, el LED y el buzzer en la pared frontal, una ventana para la cámara en la tapa, ranuras para el USB, el lazo y el pasador, y la tapa va con 4 tornillos. Archivos en [`hardware/carcasa-3d/`](hardware/carcasa-3d/).

---

## 💻 Software y Firmware

```
equipo-13-bikesafe/
├── firmware/
│   ├── esp32/        ← ESP32 cerebro: main.py, red.py, firma.py, config.example.py, hal/
│   ├── camara/       ← Freenove: main.py, telegram.py (bot), config.example.py
│   └── pruebas/      ← una prueba por pieza (e02_servo.py … e14_cerrojo_reed.py)
├── servidor/         ← mqtt_bridge.py, ia/detector.py (YOLOv5), nube.py, simular_candado.py
├── interfaz/         ← dashboard (index.html), reglas de Firestore y de Realtime DB, bot-telegram.md
├── hardware/         ← arquitectura, estados, placa perforada y carcasa-3d/
├── media/            ← fotos del prototipo y evidencias
├── pruebas_pc/       ← simulación de las placas y prueba de punta a punta (ver LEEME.md)
└── docs/             ← REVISION.md, SOLDADURA.md, DEMO.md, infografía y reporte
```

### Cómo ejecutar el sistema completo

**1. Firmware (Thonny).** Cada placa tiene un `config.example.py`: cópienlo como `config.py` y llénenlo. Los `config.py` reales **no se suben** (están en `.gitignore`).
- **ESP32 normal (COM8):** subir `main.py`, `red.py`, `firma.py`, `config.py` y la carpeta `hal/`. Si sale `MQTT: este firmware no trae umqtt`: `import mip; mip.install("umqtt.simple")`.
- **Freenove (COM7, "SPIRAM"):** MicroPython **con cámara** (`mpy_cam-…-ESP32_GENERIC-SPIRAM`). Subir `main.py`, `telegram.py` y `config.py` (WiFi, token y chat_id del bot).
- **Clave MQTT:** el mismo texto en `MQTT_CLAVE` del `config.py` de la ESP32 y en `servidor/clave_mqtt.txt`.

**2. Servidor + dashboard** (doble clic en `INICIAR_DEMO.bat`, o a mano):
```bash
pip install -r servidor/requirements.txt
cd servidor && python mqtt_bridge.py          # IA + Firebase + escucha de comandos
cd interfaz && python -m http.server 8000     # dashboard en http://localhost:8000
```
Sin placas: `python simular_candado.py ../media/ia-deteccion-persona.jpg`. Con `?demo=1`, el dashboard muestra datos de ejemplo.

### Librerías ESP32 (MicroPython — corren en la placa)

| Librería | Uso |
|---------|-----|
| `umqtt.simple` | MQTT con *last will* (`offline`) y ping cada 15 s |
| `machine` | GPIO, PWM (servo, buzzer), I2C (MPU6050), UART (enlace entre placas), WDT |
| `network` | WiFi con reintentos y escaneo de redes |
| `hashlib` + `binascii` | HMAC-SHA256 escrito a mano en `firma.py` (MicroPython no trae `hmac`) |
| `camera` + `jpeg` | Cámara GC0308 y conversión a JPEG (firmware `micropython-camera-API`) |
| `ssl` + `socket` | Bot de Telegram por HTTPS (`sendMessage`, `sendPhoto`, `getUpdates`) |

### Librerías servidor Python (corren en la PC)

| Librería | Versión | Uso |
|---------|---------|-----|
| paho-mqtt | ≥ 2.0 | Cliente MQTT del servidor |
| opencv-python | ≥ 4.8 (probado en 5.0) | `cv2.dnn` para correr YOLOv5 (ONNX) |
| numpy | ≥ 1.24 | Manejo de la imagen |
| firebase-admin | ≥ 6.0 | Escritura en Firestore y escucha `on_snapshot` |

---

## 🧠 Inteligencia Artificial

- **Modelo:** **YOLOv5s** entrenado en COCO (`servidor/ia/modelos/yolov5s.onnx`, 14 MB), corriendo con `cv2.dnn`, sin PyTorch.
- **Qué detecta:** **personas** (clase 0 de COCO), aunque solo se vea el cuerpo, un brazo o la cabeza de lado. Antes usábamos YuNet, que solo detectaba **caras**: alguien de espaldas o con gorra no salía. La cámara ve hacia arriba por la ventana de la tapa, así que la foto se prueba girada 0°/90°/180°/270° y se aplica **NMS** más un filtro de cajas contenidas, para no contar dos veces a la misma persona.
- **¿Por qué YOLO y no MobileNet-SSD?** OpenCV 5 (el que tenemos en la laptop) **ya no lee modelos Caffe** (`readNetFromCaffe` no existe). YOLOv5 en ONNX funciona igual en OpenCV 4.8 y 5.
- **Cómo toma decisiones:** el servidor **solo informa** `{"clase": "persona", "conf": 0.58, "personas": 1}` firmado. La **ESP32 decide** con su propia regla (`config.py`):

| Situación (bici ASEGURADA) | Decisión de la ESP32 |
|---|---|
| `conf` < 45 % | Se ignora |
| Persona ≥ 45 % | **Aviso:** 3 pitidos, LED morado y Telegram "🤖 la IA confirmó una persona (58 %)" |
| 2ª persona en 2 min **y** la bici se movió | **ROBO:** sirena, LED rojo y ráfaga de fotos |

- **Confianza mínima aceptada:** 45 % (`IA_CONFIANZA_MINIMA` en la ESP32 y `CONFIANZA_MINIMA` en el servidor).
- **Pruebas con 11 fotos reales de nuestra cámara:** 5 se detectaron como persona, entre 51 y 71 %. Una de ellas solo muestra una **mano**, que YuNet no habría detectado. Las 4 sin nadie dieron 0 %. En 2 fotos la cara apenas asoma en una orilla y quedaron debajo del umbral (39 % y 0 %): es la limitación de una cámara de 320×240 que ve hacia arriba. Tarda ~0.6 s por foto con los 4 giros.

![YOLO detectando una persona](media/ia-yolo-persona.jpg)

---

## 🎥 Demostración

**Video demostrativo (YouTube):** _(se sube con la versión soldada)_ · Guion: [docs/DEMO.md](docs/DEMO.md)

| Prototipo (frente) | Interior antes de soldar | En operación | Telegram: cable cortado |
|---|---|---|---|
| ![frontal](media/prototipo-frontal.jpg) | ![interna](media/prototipo-interno-dupont.jpg) | ![operacion](media/sistema-operacion.jpg) | ![telegram](media/telegram-demo-cable-cortado.jpg) |

> La foto del interior muestra el cableado **con Dupont**, que la maestra observó en la revisión. Se está pasando a placa perforada soldada ([docs/SOLDADURA.md](docs/SOLDADURA.md)).

---

## 📋 HAL — Hardware Abstraction Layer

| # | Componente | Pin ESP32 | Tópico MQTT | Unidad | Rango válido |
|---|-----------|-----------|-------------|--------|-------------|
| 1 | MPU6050 (movimiento) | I2C SDA GPIO21 · SCL GPIO22 | `bikesafe/sensor/movimiento` | g | 0 – 2 (toque > 0.18) |
| 1b | MPU6050 (inclinación) | I2C SDA GPIO21 · SCL GPIO22 | `bikesafe/sensor/inclinacion` | ° | 0 – 180 (robo > 25° por 1.2 s) |
| 2 | HC-SR04 (ultrasónico) | TRIG GPIO26 · ECHO GPIO27 (divisor 1 kΩ/2 kΩ) | `bikesafe/sensor/distancia` | cm | 2 – 400 (presencia < 50 por 3 s) |
| 3 | Reed switch (cerrojo) | GPIO18 (pull-up interno) | `bikesafe/sensor/cerrojo` | — | `CERRADO` / `ABIERTO` (robo si abre > 0.5 s asegurada) |
| 3b | Lazo anti-corte (extra) | GPIO14 (pull-up interno) | `bikesafe/sensor/lazo` | — | `ENTERO` / `CORTADO` |
| 3c | PIR HC-SR501 (opcional) | GPIO34 | `bikesafe/sensores` | — | 0 / 1 |
| 4 | Servo SG90 (pasador) | GPIO13 (PWM 50 Hz) | `bikesafe/servo/cmd` | ° | 0 (abierto) – 90 (cerrado) |
| 5 | Buzzer | GPIO25 | `bikesafe/buzzer/cmd` | — | `pitido` / `sirena_off` |
| 6 | LED RGB | R GPIO33 · G GPIO32 · B GPIO19 (220 Ω c/u) | `bikesafe/led/cmd` | color | verde libre · azul asegurada · rojo alarma · amarillo aviso · morado IA · cian presencia · blanco buscar |
| 7 | Freenove ESP32-WROVER | UART: TX2 GPIO17 → GPIO33 · RX2 GPIO16 ← GPIO32 | `bikesafe/cam/frame` | JPEG | 320 × 240 |

### Pines de la Freenove (placa de la cámara)

| Grupo | Pines de la Freenove | Va a | Notas |
|------|----------------------|------|-------|
| **Enlace con la ESP32** (UART 9600) | **GPIO33** = RX · **GPIO32** = TX | TX2 (17) · RX2 (16) de la ESP32 | Cruzados |
| | **GND** | Riel GND | **Obligatorio:** sin GND común no se entienden |
| **Alimentación** | **USB-C** (5 V) | Powerbank (cable "Y") | Tomar 5 V del riel de la ESP32 no alcanza |
| **Cámara** (fijos) | D0–D7: 4, 5, 18, 19, 36, 39, 34, 35 · VSYNC 25 · HREF 23 · PCLK 22 · XCLK 21 · SDA 26 · SCL 27 | Cable plano | No conectar nada más aquí |

---

## 📱 Bot de Telegram

| Botón | Qué hace |
|---|---|
| **Cerrar** | Asegura, solo si el reed confirma que el cable está metido |
| **Abrir** | Pregunta **"¿Seguro?"** (Sí, abrir / No, válido 30 s) y abre |
| **Foto** | Foto en ese momento |
| **Estado** | Estado, cerrojo, cable, distancia, inclinación, última IA, conexión, avisos y robos |
| **Buscar** | Suena 5 s con el LED blanco para encontrar la bici |
| **Silenciar** | Calla la sirena; la bici sigue asegurada |

Solo obedece al `TELEGRAM_CHAT_ID` del dueño, y si un extraño le escribe, **le avisa al dueño**. Si alguien abre desde el dashboard, el dueño recibe "🔓 bici LIBERADA (desde dashboard)". Más detalle en [interfaz/bot-telegram.md](interfaz/bot-telegram.md).

---

## 🔥 Esquema Firebase

Cloud Firestore en **las dos direcciones**:
- **Guarda:** el servidor escribe lecturas, alertas, eventos, decisiones de la IA y el estado actual.
- **Escucha en tiempo real:** el dashboard usa `onSnapshot` en 6 consultas y se actualiza solo. El servidor usa `on_snapshot` sobre `comandos`: cuando alguien pica un botón del dashboard, en menos de 1 s lo firma y se lo manda a la ESP32. Además marca el comando como `enviado`, `caducado` (> 60 s) o `rechazado`, y el dashboard ve ese cambio en vivo.

```
proyectos/bikesafe/
  lecturas/{id}     distancia, movimiento, inclinacion, cerrojo, lazo, luz, estado, ts
  alertas/{id}      texto, estado, ts
  eventos/{id}      tipo (estado|comando|conexion|cerrojo), detalle, origen, estado, ts
  eventos_ia/{id}   deteccion, confianza, personas, modelo, giro, nivel, motivo, imagen (JPEG base64), ts
  comandos/{id}     cmd, uid, nombre, creado  ← lo crea el dashboard
                    estado: pendiente → enviado / caducado / rechazado, nota, procesado  ← lo marca el servidor
  estado/actual     estado, conexion (LWT), servidor, cerrojo, lazo, luz, distancia, ultima_ia, ultima_alerta, actualizado
```

**Reglas (nada público)** — [`interfaz/firestore.rules`](interfaz/firestore.rules), publicadas en la consola el 25/nov:
- **Leer:** solo los UID de Oscar y Diego, con sesión de Google.
- **Escribir desde el navegador:** solo **crear** un comando de la lista permitida, con su propio `uid`, estado `pendiente`, hora del servidor y sin campos extra. No se puede editar ni borrar nada.
- **Todo lo demás lo escribe solo el servidor** (llave de servicio). Cualquier otra ruta está cerrada.
- **Realtime Database:** el proyecto **no la usa ni la tiene creada** (no existe ningún `".read": true`). Si algún día se crea, [`interfaz/database.rules.json`](interfaz/database.rules.json) la deja cerrada.

![Reglas publicadas](media/firestore-reglas-publicadas.jpg)

![Dashboard v2](media/dashboard-v2-demo.png)

---

## ⚠️ Retos técnicos encontrados

1. **La cámara GC0308 no genera JPEG por hardware** (`ESP_ERR_NOT_SUPPORTED`). Se captura en RGB565 y se convierte con el módulo `jpeg` (`RGB565_BE`, reloj de 10 MHz).
2. **El servo no se movía:** un **jumper roto por dentro** (0.1–0.5 V en vez de 5 V). Por eso, y por la vibración de la bici, el circuito final va **soldado**.
3. **El buzzer no sonaba con el 2N2222:** se conectó directo a D25.
4. **Las pruebas corrían en la placa equivocada:** Thonny estaba en la Freenove (`SPIRAM`) y no en la ESP32 (COM8).
5. **El lector RFID RC522 nunca respondió.** Primero fue un corto de 3.3 V a GND por un puente de soldadura; ya corregido, seguía regresando `0x00`/`0xFF`. Se reemplazó por el bot de Telegram.
6. **`Wifi Internal State Error`:** se arregló con `disconnect()` y apagar/prender el WiFi antes de conectar, más 3 reintentos.
7. **Broker público = cualquiera puede publicar.** Solución: mensajes firmados con HMAC-SHA256 y contador anti-repetición.
8. **OpenCV 5 ya no lee Caffe:** por eso MobileNet-SSD no corría y elegimos YOLOv5 en ONNX.
9. **YuNet solo veía caras:** se cambió a detección de **personas** (YOLOv5, COCO), que también detecta cuerpos y manos.
10. **El broker cortaba a la cámara por inactividad** y se perdía la siguiente foto. Solución: ping cada 30 s y reintento con reconexión.
11. **La powerbank tiene una sola salida:** cable USB "Y" para alimentar las dos placas.

### Cómo lo probamos

Antes de cargarlo a las placas, el firmware se probó en una **simulación** con módulos `machine`, `network` y `umqtt` de mentira y un reloj virtual: **50 pruebas** de la ESP32 y 17 de la Freenove. Después hubo una prueba **de punta a punta** con un broker MQTT real: ESP32 simulada ↔ UART ↔ Freenove simulada → broker → servidor con YOLO → resultado firmado → la ESP32 decide → Telegram. Fueron 18 pruebas, incluidos los comandos del dashboard, la firma, la repetición y la caducidad.

---

## 🗓️ Avance por sprint

| Sprint | Entregable | Estado |
|--------|-----------|--------|
| 1 · HAL + MQTT | 3 sensores y 3 actuadores, tópicos, Tabla HAL | ✅ Código · 🟡 falta montar el reed y el LED RGB |
| 2 · CAM + IA | Cámara publica frames, IA de personas, la ESP32 decide | ✅ YOLOv5 probado con fotos reales |
| 3 · Firebase + carcasa | Firestore en las 2 direcciones, dashboard con control, carcasa | ✅ Firebase y dashboard · ✅ carcasa impresa · 🟡 soldadura |
| 4 · Final | Video, reporte PDF, fotos con la versión soldada | 🟡 En proceso (entrega 2 de diciembre) |

---

*Sistemas Programables · ISC TecNM León · ago-dic-2026*
