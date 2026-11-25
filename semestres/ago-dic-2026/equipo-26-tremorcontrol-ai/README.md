# TremorControl AI — Cubierto estabilizador para Parkinson

![Estado](https://img.shields.io/badge/estado-en--desarrollo-yellow)
![Semestre](https://img.shields.io/badge/semestre-ago--dic--2026-blue)
![Materia](https://img.shields.io/badge/materia-Sistemas%20Programables-orange)

> **Semestre:** ago-dic-2026  
> **Materia:** Sistemas Programables — ISC TecNM León

| Nombre | Matrícula | Rol | GitHub |
|--------|-----------|-----|--------|
| Jorge Juan Antonio Flores Rodríguez | 23241113 | Firmware, integración y hardware | @Jorge843 |
| Brandon Imanol Ramírez López | 23241111 | Desarrollo e integración del proyecto | Pendiente |

---

## 📌 Descripción General

TremorControl AI es un cubierto mecatrónico asistivo orientado a personas con Parkinson o temblor esencial. El prototipo detecta la inclinación y el movimiento de la cuchara mediante un MPU-6050 y utiliza servomotores SG90 para generar una compensación mecánica que ayude a mantener el utensilio estable durante la alimentación.

---

## 🏗️ Arquitectura del Sistema

**Sprint 1:** se implementa la capa básica de hardware y firmware formada por ESP32-WROVER, MPU-6050 y dos servomotores SG90.

La arquitectura gráfica definitiva se agregará en un sprint posterior dentro de `hardware/`.

### Tópicos MQTT

MQTT todavía no se implementa en el Sprint 1.

---

## 🛠️ Hardware

| # | Componente | Tipo | Cantidad | Estado |
|---|------------|------|----------|--------|
| 1 | ESP32-WROVER | Microcontrolador | 1 | En uso |
| 2 | MPU-6050 | Sensor inercial | 1 | Probado |
| 3 | Servo SG90 Eje X | Actuador | 1 | En calibración mecánica |
| 4 | Servo SG90 Eje Y | Actuador | 1 | Probado |
| 5 | ESP32-CAM | Cámara | 1 | Pendiente de integración |
| 6 | HC-SR04 | Sensor ultrasónico | 1 | Pendiente |
| 7 | Motor vibrador | Actuador háptico | 1 | Pendiente |

### Diagrama de conexiones

La documentación gráfica definitiva se agregará en `hardware/`.

---

## 💻 Software y Firmware

### Firmware del Sprint 1

Archivo principal:

[📄 Ver `prueba_estabilizacion_xy.py`](firmware/prueba_estabilizacion_xy.py)

La prueba implementa:

- detección del MPU-6050 por I2C;
- lectura de acelerómetro y giroscopio;
- cálculo de `roll` y `pitch`;
- calibración inicial con 100 muestras;
- filtro de lectura;
- zona muerta para movimientos pequeños;
- prueba de compensación para los ejes X y Y;
- límites de seguridad de los servos;
- control PWM de los SG90.

### Estado de la prueba X/Y

- **Eje Y:** responde a la inclinación vertical y realiza compensación en sentido contrario.
- **Eje X:** el firmware de prueba está implementado, pero el servo aún requiere ajuste de centro mecánico porque al activarse tiende a desplazarse hacia la izquierda.

---

## 🧠 Inteligencia Artificial

La integración de IA no forma parte del Sprint 1. Se incorporará en un sprint posterior con la cámara.

---

## 🎥 Demostración

El video final se agregará en el Sprint 4.

Las fotografías finales del prototipo se almacenarán en `media/`.

---

## 📋 HAL — Hardware Abstraction Layer

| # | Componente | Señal | Pin ESP32 | Tipo | Rango / configuración |
|---|------------|-------|-----------|------|-----------------------|
| 1 | MPU-6050 | SDA | GPIO32 | I2C | 400 kHz |
| 2 | MPU-6050 | SCL | GPIO33 | I2C | 400 kHz |
| 3 | Servo SG90 Eje X | Señal | GPIO13 | PWM | 50 Hz; 45°–135° |
| 4 | Servo SG90 Eje Y | Señal | GPIO14 | PWM | 50 Hz; 45°–135° |

### Parámetros actuales del firmware

| Parámetro | Valor |
|-----------|-------|
| `CENTRO_X` | 90° |
| `CENTRO_Y` | 90° |
| `PASO_MAXIMO` | 8.0 |
| `TIEMPO_CICLO` | 10 ms |
| `ZONA_MUERTA` | 2.0 |
| `ALPHA` | 0.15 |

---

## 🔥 Esquema Firebase

Firebase no se integra todavía en este Sprint 1.

---

## ⚠️ Retos técnicos encontrados

1. El servo del eje X requiere ajuste del centro mecánico para evitar el desplazamiento hacia la izquierda al activarse.
2. Fue necesario adaptar los ejes del MPU al montaje físico: `PITCH = X` y `ROLL = Y`.
3. Se ajustó la dirección del eje Y para que la compensación sea contraria a la inclinación de la cuchara.

---

## ✅ Sprint 1 — HAL + firmware básico

- [x] Tabla HAL definida con pines reales.
- [x] MPU-6050 detectado y leído correctamente.
- [x] Cálculo de roll y pitch.
- [x] Calibración inicial.
- [x] Prueba básica del Servo X.
- [x] Prueba funcional del Servo Y.
- [x] Firmware de prueba conjunta X/Y.
- [ ] Ajuste mecánico definitivo del Servo X.

---

*Sistemas Programables · ISC TecNM León · ago-dic-2026*
