# TremorControl AI — Cubierto estabilizador Parkinson

## Integrantes

- Jorge Juan Antonio Flores Rodríguez
- Brandon Imanol Ramírez López

## Descripción del proyecto

TremorControl AI es un proyecto desarrollado para la materia de Sistemas Programables, consiste en un cubierto mecatrónico asistivo que busca ayudar a reducir el movimiento involuntario de la mano durante la alimentación

El sistema utilizará una ESP32-WROVER Board A3B0 como controlador principal, un MPU-6050 para detectar aceleración, inclinación y movimiento de la mano, además de dos servomotores SG90 que realizarán una compensación en los ejes X y Y para tratar de mantener la cuchara lo más estable posible

También se integrará un sensor FSR para detectar cuando el usuario está sujetando el cubierto, un HC-SR04 para medir distancia, un motor vibrador háptico para generar una alerta física, comunicación MQTT para monitoreo y control remoto, Firebase para almacenar información y una ESP32-CAM para apoyar posteriormente con la detección visual del rostro y la aproximación hacia la boca

## Objetivo general

Diseñar e implementar un prototipo de cubierto asistivo utilizando una ESP32-WROVER Board A3B0 programada con MicroPython, capaz de detectar movimientos de la mano y generar una compensación mecánica mediante dos servomotores, además de integrar sensores adicionales, comunicación MQTT y almacenamiento de información

## Hardware principal

| Componente | Función |
|---|---|
| ESP32-WROVER Board A3B0 | Controlador principal del sistema |
| MPU-6050 | Detecta aceleración, inclinación y movimiento |
| HC-SR04 | Mide la distancia aproximada hacia el usuario |
| FSR | Detecta la presión de agarre sobre el mango |
| Servo SG90 Eje X | Compensación del movimiento horizontal |
| Servo SG90 Eje Y | Compensación del movimiento vertical |
| Motor vibrador háptico | Retroalimentación mediante vibración |
| ESP32-CAM | Apoyo para detección visual de rostro y boca |

## Tabla HAL inicial

| Dispositivo | Señal | Pin ESP32 | Tipo |
|---|---|---|---|
| MPU-6050 | SDA | GPIO21 | I2C |
| MPU-6050 | SCL | GPIO22 | I2C |
| HC-SR04 | TRIG | GPIO27 | Salida digital |
| HC-SR04 | ECHO | GPIO26 | Entrada digital |
| FSR | Salida | GPIO34 | ADC |
| Servo SG90 Eje X | Señal | GPIO25 | PWM |
| Servo SG90 Eje Y | Señal | GPIO33 | PWM |
| Motor háptico | Control | GPIO32 | Salida / PWM |

La asignación de pines es inicial y podrá modificarse durante las pruebas físicas del proyecto

## Funcionamiento propuesto

Cuando el usuario sujete el cubierto, el sensor FSR detectará la presión de agarre, posteriormente el MPU-6050 realizará lecturas de movimiento e inclinación en tiempo real

Los datos obtenidos serán procesados por la ESP32 y utilizados para calcular una compensación en los dos servomotores, de manera que los motores se muevan en sentido contrario al movimiento detectado

El HC-SR04 servirá como referencia para conocer la distancia aproximada del cubierto hacia el usuario y el motor háptico podrá generar una pequeña vibración como forma de aviso

En etapas posteriores se integrará comunicación MQTT para enviar información y modificar parámetros desde un teléfono, además de Firebase para guardar registros del funcionamiento del sistema

## Estado actual

Actualmente el proyecto se encuentra en su etapa inicial de desarrollo

- Definición del proyecto completada
- Selección inicial de componentes completada
- Repositorio GitHub configurado
- Tabla HAL inicial definida
- Preparación de las primeras pruebas de sensores y actuadores

## Próximos pasos

- Probar individualmente el MPU-6050
- Probar los dos servomotores SG90
- Calibrar la posición neutral del sistema
- Realizar la primera compensación de movimiento en dos ejes
- Integrar el sensor FSR
- Integrar el HC-SR04
- Integrar el motor háptico
- Implementar comunicación MQTT
- Realizar el montaje físico del prototipo