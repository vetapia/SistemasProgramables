# Sprint 2 — Lectura MPU-6050 y estabilización inicial

## Objetivo

Leer la inclinación de la cuchara con el MPU-6050 y realizar la primera compensación activa mediante servomotores.

## Configuración probada

| Dispositivo | Señal | GPIO |
|---|---|---:|
| MPU-6050 | SDA | 32 |
| MPU-6050 | SCL | 33 |
| Servo X SG90 | PWM | 13 |
| Servo Y SG90 | PWM | 14 |

## Actividades realizadas

- Detección del MPU-6050 en la dirección I2C 0x68.
- Lectura de acelerómetro y giroscopio.
- Cálculo de ángulos roll y pitch.
- Calibración automática de la posición inicial.
- Aplicación de filtro para reducir ruido.
- Separación lógica de los movimientos X y Y.
- Configuración de PITCH como eje X y ROLL como eje Y según el montaje físico.
- Implementación de zona muerta para evitar movimientos pequeños no deseados.
- Prueba del servo Y con compensación contraria a la inclinación.
- Ajuste de la dirección del eje Y:
  - al levantar la cuchara, el servo compensa hacia abajo;
  - al bajar la cuchara, el servo compensa hacia arriba.
- Aumento de velocidad de respuesta con PASO_MAXIMO = 8.0 y TIEMPO_CICLO = 10 ms.

## Resultado actual

El eje Y se encuentra funcional y responde al movimiento detectado por el MPU-6050. El movimiento lateral X ya puede identificarse sin provocar la corrección del eje Y.

El servo X todavía se encuentra en calibración mecánica porque al habilitarlo tiende a desplazarse hacia la izquierda al recibir su posición inicial. Por este motivo, el firmware estable de este sprint mantiene el eje X desactivado mientras se corrige su centro mecánico.

## Pendiente para el siguiente sprint

- Centrar mecánicamente el servo X.
- Activar la compensación del eje X.
- Probar estabilización simultánea de ambos ejes.
- Documentar el montaje físico definitivo.
- Continuar con los sensores y servicios adicionales del proyecto.

## Estado

Parcialmente completado: eje Y funcional; eje X en calibración.
