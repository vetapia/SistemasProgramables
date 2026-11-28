# 🔐 OmniDock
 
### Alcancía inteligente con clasificador de monedas, validador de billetes por visión artificial y seguridad biométrica
 
![Estado](https://img.shields.io/badge/estado-en--desarrollo-yellow)
![Semestre](https://img.shields.io/badge/semestre-ago--dic--2026-blue)
![Materia](https://img.shields.io/badge/materia-Sistemas%20Programables-orange)
![Plataforma](https://img.shields.io/badge/plataforma-ESP32%20%7C%20MicroPython-green)
 

 ![Version](https://img.shields.io/badge/Version%20Documento-V1-green)
 

 <!--Tabla de los integrantes-->

 > **Semestre:** ago-dic-2026
> **Materia:** Sistemas Programables — ISC TecNM León
> **Equipo:** equipo-23-omnidock
> **Integrantes:**
 
| Nombre | Matrícula | Rol | GitHub |
|--------|-----------|-----|--------|
| Israel Dominguez Zendejas | 23240380 | 🔧 Firmware ESP32 y MQTT | [@IsraelDZ3](https://github.com/IsraelDZ3) |
| Jesus Fernandez Olmos | 23240357 | 🧠 Backend Python e IA | [@FFO76-0](https://github.com/FFO76-0) |
| Emilio Uriel Rocha Manzano | 23240356 | 🔩 Diseño de hardware y CAD | [@23240356-Uriel](https://github.com/23240356-Uriel) |
 
---

<!--Indice, talves se modifique en el transcurso-->

## 📑 Contenido
 
1. [Descripción general](#-descripción-general)
2. [Funcionamiento](#-funcionamiento)
3. [Estructura del repositorio](#-estructura-del-repositorio)
4. [Arquitectura del sistema](#️-arquitectura-del-sistema)
5. [Hardware](#️-hardware)
6. [Software y firmware](#-software-y-firmware)
7. [Inteligencia artificial](#-inteligencia-artificial)
8. [Interfaz web](#-interfaz-web)
9. [Demostración](#-demostración)
10. [HAL](#-hal--hardware-abstraction-layer)
11. [Esquema Firebase](#-esquema-firebase)
12. [Retos técnicos](#️-retos-técnicos-encontrados)
---

<!-- En base a documentacion ya echa anteriormente esta es la descripcion-->
## 📌 Descripción General
 
**OmniDock** es una alcancía inteligente pensada para **personas con discapacidad visual, adultos mayores y pequeños comerciantes**, quienes tienen dificultad para identificar billetes y monedas por sí mismos y se exponen a fraudes o al llamado "robo hormiga". El sistema recibe el dinero, **valida los billetes con una cámara y un modelo de IA, clasifica mecánicamente las monedas, anuncia cada ingreso en voz alta** y resguarda todo tras una puerta que **solo se abre con la huella del dueño**.
 
A diferencia de una alcancía común o de un lector de billetes aislado, OmniDock integra en un solo dispositivo **validación, conteo, audio y custodia biométrica**, y permite a un familiar de apoyo **consultar el saldo y bloquear el sistema de forma remota** desde una interfaz web de alto contraste, todo con componentes accesibles y de bajo costo.
 
---

<!--Podria cambiar en el transcurso depende de la complejidad futura-->

## ⚙️ Funcionamiento
 
```
 ① Inserta        ② Procesa         ③ Clasifica        ④ Valida         ⑤ Asegura        ⑥ Retiro
   dinero    ──▶    el ingreso  ──▶   e identifica ──▶  por voz    ──▶  e incrementa ──▶  seguro
```




| Paso | Etapa | Qué sucede |
|:----:|-------|-----------|
| 1 | **Inserta dinero** | El usuario coloca un billete o una moneda en su ranura correspondiente. |
| 2 | **Procesa el ingreso** | Un sensor infrarrojo detecta el billete en la ranura y activa el motorreductor que lo arrastra (las monedas ruedan por la rampa clasificadora). |
| 3 | **Clasifica e identifica** | La **ESP32-CAM** fotografía el billete y el servidor de IA lo analiza; las monedas caen por tamaño y activan su sensor IR respectivo (**$1, $2, $5 y $10**). |
| 4 | **Valida por voz** | El **DFPlayer Mini** anuncia el resultado: _"Billete de cincuenta pesos aceptado"_ / _"Moneda de diez pesos"_. Si el billete es rechazado, el motor gira en reversa, lo devuelve y el sistema avisa _"Billete rechazado"_. |
| 5 | **Asegura e incrementa** | Se suma al saldo total y el dinero se almacena en los compartimentos internos. |
| 6 | **Retiro seguro** | El dueño coloca su huella en el **AS608**; si es válida, el servomotor libera el seguro y los resortes de tensión abren la puerta. Al retirar el dinero, el contador se reinicia. |
 
El **reed switch** vigila en todo momento si la puerta está abierta o cerrada, de modo que cualquier apertura no autorizada puede reportarse al familiar de apoyo.

---

<!--En base a la documentacion de la V.Tapia-->

## 🗂️ Estructura del Repositorio
 
```
equipo-23-omnidock/
├── docs/           ← Reporte PDF, manuales, HAL.md
├── firmware/       ← MicroPython ESP32 y ESP32-CAM
├── servidor/       ← Python: IA + MQTT bridge + requirements.txt
├── interfaz/       ← Dashboard web / Firebase config
├── hardware/       ← Esquemático Fritzing (.fzz) + exportado (.png y .pdf)
├── media/          ← Fotos del prototipo + GIF o link al video
└── README.md       ← Este documento
```
 
> ⚠️ `software/` no existe en este repositorio. El backend de este curso siempre va en `servidor/`.
 
---


<!--Esto aun sigue en duda(pendiente) pero esta es la idea-->


## 🏗️ Arquitectura del Sistema
 
El sistema se organiza en tres capas:
 
| Capa | Responsabilidad |
|------|-----------------|
| **1. Percepción (Edge)** | Clasificación mecánica de monedas con barreras infrarrojas (FC-51) y captura de billetes con la ESP32-CAM S3. |
| **2. Control (Firmware)** | Lógica de acceso biométrico (AS608) y accionamiento electromecánico (servomotor y motor DC). |
| **3. Telemetría (Backend)** | Sincronización asíncrona de transacciones hacia un servidor Python mediante **MQTT** (`broker.hivemq.com`, puerto 1883). |
 
> 🚧 **Pendiente:** insertar el diagrama de arquitectura como imagen (flujo completo ESP32 / ESP32-CAM ↔ Broker MQTT ↔ Servidor IA ↔ Firebase ↔ Interfaz web).
> Guardar en `hardware/` y actualizar la ruta.
 
<!-- ![Arquitectura del sistema](hardware/arquitectura.png) -->
 


 ### Tópicos MQTT
 
Broker público: `broker.hivemq.com:1883`. El servidor se suscribe a `omnivault/#`.
 
| Tópico | Dirección | Descripción | Estado |
|--------|-----------|-------------|--------|
| `omnivault/sensor/moneda` | ESP32 → Broker | Moneda detectada en la rampa (IR) | ✅ Implementado |
| `omnivault/sensor/huella` | ESP32 → Broker | Usuario identificado por el lector de huella | 🚧 En desarrollo |
| `omnivault/cam/frame` | ESP32-CAM → Broker | Frame del billete (Base64 JPEG) | 🚧 En desarrollo |
| `omnivault/actuador/puerta/cmd` | Broker → ESP32 | Abrir / cerrar el seguro de la puerta | ✅ Implementado |
| `omnivault/actuador/audio/cmd` | Broker → ESP32 | Pista de audio a reproducir (DFPlayer) | 🚧 En desarrollo |
 
> ⚠️ **Nota de nomenclatura:** el prefijo de los tópicos en el código es `omnivault/` (nombre anterior del proyecto). Si se renombra a `omnidock/`, hay que cambiarlo a la vez en `firmware/main.py`, `servidor/app.py` y `docs/HAL.md`.
 
---

<!--Anexar lo faltante de presupuesto NOTA-->

## 🛠️ Hardware
 
| # | Componente | Tipo | Cantidad | Costo aprox. MXN |
|---|-----------|------|----------|-----------------|
| 1 | ESP32 DevKit V1 | Microcontrolador | 1 | $130 |
| 2 | ESP32-CAM S3 (OV2640, USB-C) | Cámara | 1 | $330 |
| 3 | Módulo infrarrojo FC-51 | Sensor | 5 (1 ranura de billetes + 4 rampa de monedas) | $125 |
| 4 | Lector de huella óptico AS608 | Sensor · ⭐ componente estrella | 1 | $290 |
| 5 | Sensor magnético Reed Switch MC-38 | Sensor | 1 | $50 |
| 6 | Servomotor MG90S | Actuador (seguro de la puerta) | 1 | $68 |
| 7 | Motorreductor DC 1:48 + llanta de goma | Actuador (tracción de billetes) | 1 | $70 |
| 8 | Módulo puente H L298 | Driver del motor (PWM y sentido de giro) | 1 | $82 |
| 9 | Reproductor MP3 DFPlayer Mini | Actuador (audio) | 1 | $63 |
| 10 | Altavoz pequeño 8 Ω, 2–3 W | Actuador (audio) | 1 | _Pendiente_ |
| 11 | Tarjeta microSD 2–8 GB | Almacenamiento de audios | 1 | _Pendiente_ |
| 12 | Módulo de fuente MB102 para protoboard | Energía | 1 | $135 |
| 13 | Eliminador de corriente 9 V, 1–2 A | Energía | 1 | $140 |
| 14 | Protoboard de 830 puntos | Conectividad | 1 | _Pendiente_ |
| 15 | Cables Dupont surtidos | Conectividad | 1 paquete | _Pendiente_ |
| 16 | Planchas de MDF de 3 mm (o cartón batería en prototipo) | Carcasa | — | _Pendiente_ |
| 17 | Resortes de tensión (expulsión de la puerta) | Carcasa | — | _Pendiente_ |
| **Subtotal actual** | | | | **$1,483 MXN** _(sin partidas pendientes)_ |
 
> 🚧 **Pendiente:** actualizar el total cuando se cotice el resto de las partidas




### Cumplimiento de requisitos de la materia
 
| Requisito | Cumplimiento |
|-----------|--------------|
| Mínimo 3 sensores | ✅ Infrarrojos FC-51 (×5), lector de huella AS608, reed switch MC-38 |
| Mínimo 3 actuadores reales | ✅ Servomotor MG90S, motorreductor DC con puente H, DFPlayer Mini + altavoz |
| Cámara | ✅ ESP32-CAM S3 |
| Componente estrella (no convencional) | ✅ Lector de huella dactilar AS608 |
 




 ### Diagrama de conexiones
 
> 🚧 **Pendiente:** insertar el esquemático de conexiones (Fritzing, `.fzz` + `.png`/`.pdf`) en `hardware/`.
 
<!-- ![Diagrama de conexiones](hardware/diagrama.png) -->
 
---

<!--Esta parte esta en duda-->

## 💻 Software y Firmware
 
### Requisitos del servidor Python
 
```bash
pip install -r servidor/requirements.txt
```


<!--Mas adelante volver a checar para actualizar-->
### Cómo ejecutar el sistema completo
 
**1. Broker MQTT:** el proyecto usa el broker público `broker.hivemq.com`, por lo que no es necesario levantar uno local.
 
**2. Configurar y cargar el firmware en la ESP32:**
Editar en `firmware/main.py` las constantes `WIFI_SSID` y `WIFI_PASS` con la red local. Abrir Thonny → conectar la ESP32 → cargar `main.py` y `dispositivos.py` desde la carpeta `firmware/`.
 
**3. Ejecutar el servidor:**
```
cd servidor
python app.py
```
El servidor se conecta al broker, se suscribe a `omnivault/#` e imprime en consola cada mensaje recibido (JSON o texto).
 

<!--********REVISAR-->

 ### Archivos principales
 
| Archivo | Descripción |
|---------|-------------|
| `firmware/main.py` | Conexión WiFi/MQTT, publicación de monedas y recepción de comandos de la puerta. |
| `firmware/dispositivos.py` | Clases `SensorMoneda` (con anti-rebote de 500 ms) y `ServoPuerta`. |
| `servidor/app.py` | Cliente MQTT que escucha la telemetría del sistema. |
| `docs/HAL.md` | Tabla de pines y tópicos. |



<!--En duda, revisar******-->

### Librerías ESP32 (MicroPython — corren en la placa)
 
| Librería | Uso |
|---------|-----|
| `umqtt.simple` | Cliente MQTT en la ESP32 |
| `machine` | Control de pines GPIO (`Pin`) y PWM del servomotor; UART para AS608 y DFPlayer |
| `network` | Conexión WiFi |
| `ujson` | Serialización de los mensajes JSON |
| `time` | Temporización y anti-rebote del sensor IR |
| _otras según proyecto_ | _Pendiente (driver AS608, control DFPlayer)_ |



<!--Revisar ciertos puntos en el momento indicado-->

## 🧠 Inteligencia Artificial
 
- **Modelo:** _Pendiente (OpenCV / MediaPipe / TensorFlow Lite / otro)_
- **Qué detecta:** clasificación de las imágenes del billete capturadas por la ESP32-CAM para **identificar su denominación y descartar billetes falsos, doblados o dañados**.
- **Cómo toma decisiones:**
  - Billete válido → publica comando de avance al motor + pista de audio con la denominación + suma al saldo.
  - Billete no válido o ilegible → publica comando de **reversa** + audio _"Billete rechazado"_.
- **Confianza mínima aceptada:** _Pendiente (%)_
---





<!--Revisar ciertos puntos en el momento indicado-->

## 🖥️ Interfaz Web
 
Dashboard de **alto contraste y lectura sencilla**, diseñado para el **familiar de apoyo**.
 
| Elemento | Descripción |
|----------|-------------|
| 💰 Saldo total | Monto acumulado dentro de la alcancía |
| 💵 Desglose | Cantidad de billetes y monedas por denominación |
| 🚪 Estado de la puerta | Cerrada (segura) / abierta, según el reed switch |
| 🔴 Bloqueo remoto | Botón de emergencia para bloquear el sistema |
| 📅 Historial | Registro de ingresos y retiros guardado en la nube |
 
> 🚧 **Pendiente:** captura de pantalla y enlace de despliegue (código en `interfaz/`).
 
---




## 🎥 Demostración
 
**Video de avance (YouTube):** [▶️ Canal OmniDock](https://youtube.com/@omnidock_sistemasprogramables?si=SbqNf1KXrRyeVOAZ)





### Fotos del prototipo final
 
> 🚧 **Pendiente:** agregar las fotografías en `media/`.
 
| Vista frontal | Vista interna | Sistema en operación |
|--------------|---------------|----------------------|
| _Pendiente_ | _Pendiente_ | _Pendiente_ |
 
<!-- ![frontal](media/prototipo-frontal.jpg) | ![interna](media/prototipo-interno.jpg) | ![operacion](media/sistema-operacion.jpg) -->
 
---






## 📋 HAL — Hardware Abstraction Layer
 
Documento completo: [`docs/HAL.md`](docs/HAL.md).
 
| # | Componente | Pin ESP32 | E/S | Voltaje | Tópico MQTT | Formato / Unidad |
|---|-----------|-----------|-----|---------|-------------|------------------|
| 1 | Sensor IR FC-51 (monedas) | GPIO 13 | Entrada | 3.3 V | `omnivault/sensor/moneda` | JSON `{"estado": int}` (0 = detectado) |
| 2 | Lector de huella AS608 | GPIO 16 (RX2) | Entrada | 3.3 V | `omnivault/sensor/huella` | JSON `{"id_usuario": int}` (0–127) |
| 3 | Servomotor del seguro (SG90 / MG90S) | GPIO 2 | Salida | 5.0 V | `omnivault/actuador/puerta/cmd` | String `"OPEN"` / `"CLOSE"` |
| 4 | DFPlayer Mini (audio) | GPIO 27 | Salida | 5.0 V | `omnivault/actuador/audio/cmd` | JSON `{"track": int}` (1–10) |
| 5 | Cámara ESP32-CAM S3 | UART 0 | E/S | 5.0 V | `omnivault/cam/frame` | String (Base64 JPEG) |
 
> 🚧 **Pendiente de asignar pin:** los otros 3 sensores IR de la rampa de monedas, el IR de la ranura de billetes, el reed switch de la puerta y el motorreductor con puente H.
 
---


<!--Revisar punto-->

## 🔥 Esquema Firebase
 
> 🚧 **Borrador:** estructura propuesta, sujeta a ajustes durante la integración.
 
```
/omnidock/
  /ingresos/{timestamp}/
      tipo: "billete" | "moneda"
      denominacion: 50
      confianza: 0.92
  /eventos_seguridad/{timestamp}/
      evento: "huella_valida" | "huella_invalida" | "puerta_abierta"
  /estado_actual/
      saldo_total: 150
      puerta: "CERRADA"
      bloqueo_remoto: false
```
 
---


## ⚠️ Retos técnicos encontrados
 
_Problemas conocidos del Sprint 1 (esta sección se completará al finalizar el proyecto y alimenta las conclusiones del reporte):_
 
1. **Emulación de actuadores:** el puente H y el motor DC operan en modo simulación de estados lógicos mientras finaliza el ensamble en el chasis de MDF.
2. **Latencia asíncrona:** el broker MQTT público presenta una latencia variable (150 ms – 600 ms).
3. **Falsos positivos del sensor IR:** se requiere un *debounce* (anti-rebote) por software de 500 ms para evitar conteos dobles.