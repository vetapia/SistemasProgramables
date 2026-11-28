# Esquema de Datos y Almacenamiento en la Nube — PinkGuard

## 1. Arquitectura General de Persistencia
PinkGuard utiliza una arquitectura híbrida en la nube.
* **Firebase Realtime Database (RTDB):** Almacena el historial cronológico de eventos, telemetría de sensores, estado de actuadores y metadatos de inferencia en formato JSON en tiempo real.
* **Cloudinary (Almacenamiento de Medios):** Aloja las capturas fotográficas procesadas por el modelo de visión artificial (YOLOv8 Nano) y entrega enlaces HTTPS (`secure_url`) que son referenciados dentro de Firebase RTDB.

---

## 2. Almacenamiento de Evidencias Visuales (Cloudinary)

### Parámetros de Configuración y Organización
* **Carpeta destino en la nube:** `pinkguard_intrusos/`
* **Formato de archivo:** JPEG (`.jpg`)
* **Resolución de almacenamiento:** `320 x 240 px` (escalada desde la captura cruda QQVGA `160 x 120 px` de la ESP32-CAM tras la inferencia).
* **Política de subida:** Incondicional tras cada disparo de cámara (tanto si se detecta presencia humana como si el área está despejada).

### Convención de Nomenclatura Local / Origen
Antes de subirse a Cloudinary, `detector.py` genera un respaldo temporal en `capturas_test/` con el siguiente patrón:
* **Con detección de persona (`conf >= 0.4`, clase `0`):** `intruso_YYYYMMDD_HHMMSS.jpg` *(incluye bounding boxes dibujados por YOLOv8)*.
* **Sin detección de persona:** `captura_YYYYMMDD_HHMMSS.jpg` *(imagen original escalada)*.

### Ejemplo de Respuesta de Cloudinary Consumida por el Sistema
```json
{
  "asset_id": "a1b2c3d4e5f6g7h8i9j0",
  "public_id": "pinkguard_intrusos/intruso_20261122_214510",
  "format": "jpg",
  "width": 320,
  "height": 240,
  "secure_url": "[https://res.cloudinary.com/](https://res.cloudinary.com/)<cloud_name>/image/upload/v1732333510/pinkguard_intrusos/intruso_20261122_214510.jpg"
}

Diseño del nodo Modelo:

sistemas-programables-pinkg-default-rtdb
└── Modelo
    ├── -OCx89aBcDeFgHiJkLm1   <-- Registro de Telemetría (mqtt_bridge.py)
    │   ├── sensores
    │   │   ├── Trig: "PIR_DETECCION"
    │   │   ├── PIR: 1
    │   │   ├── LDR: 2890
    │   │   ├── RF: 0
    │   │   ├── Rele: true
    │   │   └── Servo: 90
    │   └── timestamp: 1732333508120
    │
    └── -OCx89aBcDeFgHiJkLm2   <-- Registro de Visión Artificial (detector.py)
        ├── evento: "INTRUSION_DETECTADA"
        ├── humano_detectado: true
        ├── imagen_url: "[https://res.cloudinary.com/.../intruso_20261122_214510.jpg](https://res.cloudinary.com/.../intruso_20261122_214510.jpg)"
        └── timestamp: 1732333510450


Diccionario de datos:

Campo,Ruta JSON,Tipo,Valores / Rango,Descripción
Push ID,/Modelo/{id},string,Clave Firebase,Identificador único generado por el servidor.
Disparador,sensores.Trig,string,"""PIR_DETECCION"", ""RF_CANCEL""",Evento que originó el envío de telemetría.
Sensor PIR,sensores.PIR,integer,0 o 1,1 = Movimiento detectado; 0 = Sin movimiento.
Sensor LDR,sensores.LDR,integer,0 – 4095,Lectura ADC de 12 bits (lógica invertida: > 2500 indica oscuridad).
Control RF,sensores.RF,integer,0 o 1,Estado digital del receptor de radiofrecuencia (GPIO 14).
Relevador,sensores.Rele,boolean,true / false,Estado del foco disuasivo (true solo si LDR > 2500).
Servomotor,sensores.Servo,integer,"0, 45, 90, 135, 180",Ángulo en grados del radar al momento de la captura.
Marca de Tiempo,timestamp,integer,Epoch ms (UTC),Asignada por el servidor mediante {'.sv': 'timestamp'}.


Ejemplo JSON:

{
  "-OCx89aBcDeFgHiJkLm1": {
    "sensores": {
      "Trig": "PIR_DETECCION",
      "PIR": 1,
      "LDR": 2890,
      "RF": 0,
      "Rele": true,
      "Servo": 90
    },
    "timestamp": 1732333508120
  }
}

Diccionario de datos para evento de deteccion humana con IA:

Campo,Ruta JSON,Tipo,Valores / Rango,Descripción
Push ID,/Modelo/{id},string,Clave Firebase,Identificador único generado por el servidor.
Tipo de Evento,evento,string,"""INTRUSION_DETECTADA"", ""MONITOREO_GENERAL""",Clasificación resultante de la inferencia de personas.
Presencia Humana,humano_detectado,boolean,true / false,"true si YOLOv8 detecta al menos 1 persona (clase 0, conf >= 0.4)."
URL de Evidencia,imagen_url,string,URL HTTPS válida,Enlace directo a la imagen alojada en Cloudinary (320x240 px).
Marca de Tiempo,timestamp,integer,Epoch ms (UTC),Asignada por el servidor mediante {'.sv': 'timestamp'}.

{
  "-OCx89aBcDeFgHiJkLm2": {
    "evento": "INTRUSION_DETECTADA",
    "humano_detectado": true,
    "imagen_url": "[https://res.cloudinary.com/](https://res.cloudinary.com/)<cloud_name>/image/upload/v1732333510/pinkguard_intrusos/intruso_20261122_214510.jpg",
    "timestamp": 1732333510450
  }
}