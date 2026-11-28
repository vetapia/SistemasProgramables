# TremorControl AI — Cubierto estabilizador para Parkinson

## Integrantes

- Jorge Juan Antonio Flores Rodríguez
- Brandon Imanol Ramírez López

## Descripción del proyecto

TremorControl AI es un proyecto desarrollado para la materia de Sistemas Programables. Consiste en un cubierto mecatrónico asistivo que busca reducir el efecto de los movimientos involuntarios de la mano durante la alimentación.

El sistema utiliza una ESP32-WROVER como controlador principal, un MPU-6050 para detectar inclinación y movimiento, y dos servomotores SG90 para realizar compensaciones mecánicas en los ejes X y Y.

Además, el proyecto contempla la integración posterior de sensores auxiliares, comunicación con servicios web, almacenamiento de datos y apoyo visual mediante cámara.

## Objetivo general

Diseñar e implementar un prototipo de cubierto asistivo capaz de detectar movimientos de la mano y compensarlos mecánicamente mediante servomotores, con el propósito de mantener la cuchara lo más estable posible durante la alimentación.

## Hardware principal

| Componente | Función |
|---|---|
| ESP32-WROVER | Controlador principal |
| MPU-6050 | Detecta aceleración e inclinación |
| Servo SG90 Eje X | Compensación lateral |
| Servo SG90 Eje Y | Compensación vertical |
| HC-SR04 | Medición de distancia |
| Motor vibrador háptico | Retroalimentación física |
| ESP32-CAM | Apoyo para detección visual |

## Tabla HAL actual

| Dispositivo | Señal | Pin ESP32 | Tipo |
|---|---|---:|---|
| MPU-6050 | SDA | GPIO32 | I2C |
| MPU-6050 | SCL | GPIO33 | I2C |
| Servo SG90 Eje X | Señal | GPIO13 | PWM |
| Servo SG90 Eje Y | Señal | GPIO14 | PWM |

Los demás sensores se integrarán en siguientes etapas del proyecto.

## Funcionamiento actual

El MPU-6050 realiza lecturas de aceleración e inclinación en tiempo real.

Durante el arranque, el sistema calcula una posición base mediante varias muestras del MPU-6050. Posteriormente se aplican filtros y una zona muerta para reducir movimientos no deseados.

De acuerdo con el montaje físico actual:

- PITCH se interpreta como movimiento del eje X.
- ROLL se interpreta como movimiento del eje Y.
- El eje Y realiza compensación en sentido contrario al movimiento detectado.
- Si la cuchara se levanta, el servo Y corrige hacia abajo.
- Si la cuchara baja, el servo Y corrige hacia arriba.

## Configuración actual de respuesta

- PASO_MAXIMO = 8.0
- TIEMPO_CICLO = 10 ms
- ZONA_MUERTA = 2.0
- ALPHA = 0.15

## Estado actual

- Repositorio configurado.
- Estructura del proyecto creada.
- MPU-6050 detectado y probado.
- Lectura de acelerómetro y giroscopio funcional.
- Cálculo de roll y pitch implementado.
- Calibración inicial automática implementada.
- Filtro de lectura implementado.
- Zona muerta implementada.
- Separación de los movimientos X y Y implementada.
- Servo Y funcional.
- Compensación vertical funcionando.
- Velocidad de respuesta ajustada.
- Servo X actualmente en calibración mecánica.

## Firmware

El firmware probado actualmente se encuentra en:

`firmware/estabilizacion_eje_y.py`

En esta versión el servo X se mantiene desactivado para evitar movimientos incorrectos mientras se termina de ajustar su centro mecánico.

## Sprints

La documentación de avances se encuentra en:

- `docs/SPRINT_01.md`
- `docs/SPRINT_02.md`

## Próximos pasos

- Calibrar mecánicamente el servo X.
- Activar la compensación del eje X.
- Probar estabilización simultánea en ambos ejes.
- Documentar el montaje físico definitivo.
- Integrar sensores adicionales.
- Continuar con servicios web, almacenamiento de datos e interfaz.
