# SmartClass

[![Estado](https://img.shields.io/badge/estado-en--desarrollo-yellow)](#) [![Semestre](https://img.shields.io/badge/semestre-ago--dic--2026-blue)](#) [![Materia](https://img.shields.io/badge/materia-Sistemas%20Programables-orange)](#)

> **Semestre:** ago-dic-2026 **Materia:** Sistemas Programables — ISC TecNM León **Integrantes:**

| Nombre                       | Matrícula | Rol                                                      | GitHub      |
|------------------------------|-----------|----------------------------------------------------------|-------------|
| Carrillo Gómez Aldo Emmanuel | 23240343  | 🔧 Código (firmware, servidor, IA, Firebase) ·           |             |
| Torres Uribe Juan Daniel     | 232402326 | 📝 Documentación   🔩 Circuito                          | @danielTU03 |

---

## 📌 Descripción General

SmartClass ayuda a profesores, estudiantes y a la institución a ahorrar tiempo de clase, automatizando el pase de lista con reconocimiento facial (ESP32-CAM + IA) y llevando un registro de entradas y salidas del salón. Resuelve el problema de que pasar lista consume tiempo, de que los alumnos pueden salir sin regresar y de que las condiciones del aula (luz y clima) afectan el aprendizaje. A diferencia del pase de lista tradicional, también calcula retardos con un reloj RTC, cronometra las salidas intermedias, guarda en Firebase las fotos de personas no registradas para que el docente las valide y activa ventilación o luz auxiliar de forma automática.

---

## 🏗️ Arquitectura del Sistema

> 📌 **Inserta aquí tu diagrama de arquitectura como imagen.** No uses texto — coloca una imagen que muestre el flujo completo de tu sistema. Guárdala en `hardware/` y actualiza la ruta abajo.

[![Arquitectura del sistema](hardware/arquitectura.png)](hardware/arquitectura.png)

### Tópicos MQTT

| Tópico                 | Dirección          | Descripción                               |
|------------------------|--------------------|-------------------------------------------|
| `smartclass/s/clima`   | ESP32 → Broker     | Temperatura y humedad (DHT11), en JSON    |
| `smartclass/s/distancia` | ESP32 → Broker   | Distancia en cm (ultrasónico HC-SR04)     |
| `smartclass/s/ir`      | ESP32 → Broker     | Estado del sensor infrarrojo (0 / 1)      |
| `smartclass/cam/frame` | ESP32-CAM → Broker | Frame de cámara (JPEG)                    |
| `smartclass/a/bomba`   | Broker → ESP32     | Comando de la bomba de gel (1 = ON)       |
| `smartclass/a/buzzer`  | Broker → ESP32     | Comando del buzzer (1 = ON)               |
| `smartclass/a/vent`    | Broker → ESP32     | Comando del ventilador (1 = ON)           |

---

## 🛠️ Hardware

> Lista según la propuesta inicial del proyecto; se ajusta conforme avanzan los sprints.

| #         | Componente                  | Tipo             | Cantidad | Costo aprox. MXN |
|-----------|-----------------------------|------------------|----------|------------------|
| 1         | ESP32 DevKit                | Microcontrolador | 1        | $120             |
| 2         | ESP32-S2-CAM                | Cámara           | 1        | $180             |
| 3         | Ultrasónico HC-SR04         | Sensor           | 1        | $35              |
| 4         | Fotorresistencia LDR        | Sensor           | 1        | $15              |
| 5         | DHT11                       | Sensor           | 1        | $40              |
| 6         | Buzzer activo               | Actuador         | 1        | $20              |
| 7         | Micro servomotor SG90       | Actuador         | 1        | $60              |
| 8         | Módulo relevador 1 canal    | Actuador         | 1        | $35              |
| 9         | RTC DS3231                  | No convencional  | 1        | $55              |
| 10        | Pantalla OLED 0.96" I2C     | Apoyo visual     | 1        | $75              |
| 11        | Módulo LED flash            | Apoyo visual     | 1        | $25              |
| **Total** |                             |                  |          | **≈ $660 (< $800 MXN)** |

### Diagrama de conexiones

> Inserta aquí una imagen que muestre cómo están conectados los componentes. Puede ser un diagrama hecho en cualquier herramienta (Fritzing, draw.io, Canva, foto del circuito, etc.). Guarda la imagen en `hardware/` y actualiza la ruta abajo.

[![Diagrama de conexiones](hardware/diagrama.png)](hardware/diagrama.png)

---

## 💻 Software y Firmware

### Requisitos del servidor Python

```
pip install -r servidor/requirements.txt
```

### Cómo ejecutar el sistema completo

**1. Levantar el broker MQTT** (en una terminal aparte):

```
mosquitto
```

**2. Cargar firmware en la ESP32:** Abrir Thonny → conectar la ESP32 → cargar los archivos de `firmware/` desde la interfaz gráfica.

**3. Ejecutar el servidor de IA:**

```
cd servidor
python mqtt_bridge.py
```

### Librerías ESP32 (MicroPython — corren en la placa)

| Librería               | Uso                                  |
|------------------------|--------------------------------------|
| `umqtt.simple`         | Cliente MQTT en la ESP32             |
| `machine`              | Control de pines GPIO                |
| `network`              | Conexión WiFi                        |
| `dht`                  | Lectura del sensor DHT11             |
| `hcsr04`               | Lectura del sensor ultrasónico       |
| `time`                 | Tiempos y retardos                   |
| *otras según proyecto* |                                      |

### Librerías servidor Python (corren en la PC)

| Librería       | Versión | Uso                         |
|----------------|---------|-----------------------------|
| paho-mqtt      | ≥ 1.6   | Cliente MQTT en el servidor |
| opencv-python  | ≥ 4.8   | Procesamiento de imagen     |
| firebase-admin | ≥ 6.0   | Escritura en Firestore      |
| *librería IA*  | x.x     | *modelo usado*              |

---

## 🧠 Inteligencia Artificial

- **Modelo:** *(por definir: OpenCV / MediaPipe / TensorFlow Lite)*
- **Qué detecta:** Reconocimiento facial para distinguir a los alumnos matriculados de rostros no registrados (visitantes o alumnos nuevos).
- **Cómo toma decisiones:** Si reconoce al alumno → valida la hora con el RTC, publica su estado ("A tiempo" o "Retardo") y el buzzer confirma. Si no lo reconoce → toma la captura, la guarda en Firebase con la etiqueta "Pendiente de Registro" y avisa al docente.
- **Confianza mínima aceptada:** *%*

---

## 🎥 Demostración

**Video demostrativo (YouTube):** [▶️ Ver video](https://youtube.com/watch?v=XXXXXXXX)

### Fotos del prototipo final

| Vista frontal | Vista interna | Sistema en operación |
|---------------|---------------|----------------------|
| [![frontal](media/prototipo-frontal.jpg)](media/prototipo-frontal.jpg) | [![interna](media/prototipo-interno.jpg)](media/prototipo-interno.jpg) | [![operacion](media/sistema-operacion.jpg)](media/sistema-operacion.jpg) |

---

## 📋 HAL — Hardware Abstraction Layer

| # | Componente                 | Pin ESP32        | Tópico MQTT            | Unidad  | Rango válido |
|---|----------------------------|------------------|------------------------|---------|--------------|
| 1 | Infrarrojo (IR)            | GPIO 13          | smartclass/s/ir        | Digital | 0-1          |
| 2 | Ultrasónico (HC-SR04)      | Trig: 32, Echo: 35 | smartclass/s/distancia | cm      | 2-400        |
| 3 | DHT11 (ambiental)          | GPIO 33          | smartclass/s/clima     | °C / %  | 0-50 °C      |
| 4 | Bomba de gel (Relevador 1) | GPIO 25          | smartclass/a/bomba     | Digital | 0-1          |
| 5 | Buzzer activo              | GPIO 26          | smartclass/a/buzzer    | Digital | 0-1          |
| 6 | Ventilador (Relevador 2)   | GPIO 27          | smartclass/a/vent      | Digital | 0-1          |
| 7 | Cámara ESP32               | FPC interno      | smartclass/cam/frame   | JPEG    | —            |

---

## 🔥 Esquema Firebase

```
/nombre-proyecto/
  /lecturas/{timestamp}/
      sensor1: valor
      sensor2: valor
      sensor3: valor
  /eventos_ia/{timestamp}/
      deteccion: "clase"
      accion: "actuador_ON"
      confianza: 0.92
  /estado_actual/
      sensor1: ultimo_valor
      actuador1: "ON"
```

---

## ⚠️ Retos técnicos encontrados

*(Llenar al finalizar el proyecto — esta sección alimenta las conclusiones del reporte)*

---

*Sistemas Programables · ISC TecNM León · ago-dic-2026*
