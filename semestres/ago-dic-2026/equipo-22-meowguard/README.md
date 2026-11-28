# 🐱 MEOWGUARD — Sistema Robótico Autónomo de Detección y Control de Plagas

![Estado](https://img.shields.io/badge/estado-en--desarrollo-yellow)
![Semestre](https://img.shields.io/badge/semestre-ago--dic--2026-blue)
![Materia](https://img.shields.io/badge/materia-Sistemas%20Programables-orange)

> **Semestre:** ago-dic-2026  
> **Materia:** Sistemas Programables — ISC TecNM León  
> **Integrantes:**

| Nombre | Matrícula | Rol | GitHub |
|--------|-----------|-----|--------|
| Mónica Moreno Torres | 23241119 | 🧠 Servidor Python/IA • ☁️ Firebase/Interfaz • 📝 Documentación | @momots-bit |
| Leonardo Gael Niño Cabrera | 23240382 | 🔧 Firmware ESP32 • 🔩 Hardware/Carcasa | @usuario_leonardo |

---

## 📌 Descripción General

**MEOWGUARD** ayuda a encargados de almacenes de alimentos, cocinas industriales y hogares a mantener espacios libres de plagas sin exposición continua a químicos tóxicos ni supervisión manual constante. Resuelve el problema de la detección tardía y fumigación indiscriminada mediante un robot patrullero autónomo 4WD con estética felina que identifica plagas (cucarachas y roedores) en tiempo real y aplica micro-atomización localizada únicamente cuando no hay personas presentes, registrando mapas de calor y telemetría en la nube.

---

## 🏗️ Arquitectura del Sistema

![Arquitectura del sistema](hardware/arquitectura.png)

### Tópicos MQTT (`broker.hivemq.com`)

| Tópico | Dirección | Descripción |
|--------|-----------|-------------|
| `meowguard/sensores/ultrasonico` | ESP32 → Broker | Distancia frontal para evasión de obstáculos (HC-SR04) |
| `meowguard/sensores/ir_izq` | ESP32 → Broker | Detección de borde/obstáculo lateral izquierdo (HW-201) |
| `meowguard/sensores/ir_der` | ESP32 → Broker | Detección de borde/obstáculo lateral derecho (HW-201) |
| `http://<IP_ESP32_CAM>:81/stream` | ESP32-CAM → Servidor IA | Flujo de video MJPEG en tiempo real hacia OpenCV/YOLOv8 |
| `tecnm/leon/meowguard/alertas` | Servidor IA → Broker / ESP32 | Alerta JSON de plaga detectada, coordenadas $(X, Y)$ y orden de atomización |
| `meowguard/actuadores/motores` | Broker → ESP32 | Comandos de tracción 4WD (adelante / detenido / giro) |
| `meowguard/actuadores/atomizador` | Broker → ESP32 | Activación controlada del módulo fogger ultrasónico (ON / OFF) |

---

## 🛠️ Hardware

| # | Componente | Tipo | Cantidad | Costo aprox. MXN |
|---|-----------|------|----------|-----------------|
| 1 | ESP32 DevKit V1 | Microcontrolador principal | 1 | $140 |
| 2 | ESP32-CAM (OV2640) | Cámara Wi-Fi | 1 | $150 |
| 3 | Sensor Ultrasónico HC-SR04 | Sensor de distancia | 1 | $35 |
| 4 | Sensor Infrarrojo HW-201 (Izq/Der) | Sensores de proximidad | 2 | $50 |
| 5 | Puente H L298N + 4 Motores DC (Chasis 4WD) | Actuador de tracción | 1 | $220 |
| 6 | Módulo Relé 5V + Atomizador Fogger Ultrasónico (300 mL) | Actuador de control | 1 | $120 |
| 7 | Giroscopio/Acelerómetro MPU-6050 (GY-521) | Componente estrella (orientación 2D) | 1 | $65 |
| **Total** | | | | **< $800 MXN** |

### Diagrama de conexiones

![Diagrama de conexiones](hardware/diagrama.png)

---

## 💻 Software y Firmware

### Requisitos del servidor Python

```bash
pip install -r servidor/requirements.txt
