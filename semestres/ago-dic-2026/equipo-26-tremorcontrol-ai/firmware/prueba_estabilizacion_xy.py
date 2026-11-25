# ============================================
# Proyecto:  TremorControl AI
# Archivo:   prueba_estabilizacion_xy.py
# Objetivo:  Probar la lectura del MPU-6050 y la compensación básica con servos en los ejes X y Y.
# Equipo:    Jorge Juan Antonio Flores Rodríguez - 23241113
#            Brandon Imanol Ramírez López - 23241111
# Materia:   Sistemas Programables — ISC TecNM León
# Semestre:  ago-dic-2026
# ============================================

from machine import Pin, I2C, PWM
import time
import math


# ============================================================
# TREMORCONTROL AI
# MPU-6050 + SERVO X + SERVO Y
#
# MPU:
# SDA -> GPIO32
# SCL -> GPIO33
#
# SERVO X -> GPIO13
# SERVO Y -> GPIO14
#
# PITCH = X
# ROLL  = Y
# ============================================================


# ============================================================
# CONFIGURACION
# ============================================================

MPU_ADDR = 0x68

SERVO_X_PIN = 13
SERVO_Y_PIN = 14


# Centro de los servos
CENTRO_X = 90
CENTRO_Y = 90


# Limites de movimiento
MIN_X = 45
MAX_X = 135

MIN_Y = 45
MAX_Y = 135


# ============================================================
# DIRECCION
# ============================================================

# X
SIGNO_X = -1

# Y
# Si levantas la cuchara -> servo baja
# Si bajas la cuchara -> servo sube
SIGNO_Y = 1


# ============================================================
# GANANCIA
# ============================================================

GANANCIA_X = 1.0
GANANCIA_Y = 1.0


# ============================================================
# VELOCIDAD
# ============================================================

PASO_MAXIMO = 8.0

TIEMPO_CICLO = 10


# ============================================================
# ZONA MUERTA
# ============================================================

ZONA_MUERTA = 2.0


# ============================================================
# FILTRO
# ============================================================

ALPHA = 0.15


# ============================================================
# I2C
# ============================================================

i2c = I2C(
    0,
    sda=Pin(32),
    scl=Pin(33),
    freq=400000
)


print()
print("================================")
print("       TREMORCONTROL AI")
print("================================")
print()
print("MPU-6050 + SERVO X + SERVO Y")
print()


# ============================================================
# BUSCAR MPU
# ============================================================

print("Buscando MPU-6050...")

dispositivos = i2c.scan()

print("Dispositivos I2C encontrados:")
print(dispositivos)


if MPU_ADDR not in dispositivos:

    print()
    print("ERROR: MPU-6050 NO DETECTADO")
    print()
    print("Revisa:")
    print("VCC -> 3V3")
    print("GND -> GND")
    print("SDA -> GPIO32")
    print("SCL -> GPIO33")

    raise Exception(
        "MPU-6050 no encontrado"
    )


print()
print("MPU-6050 DETECTADO")
print()


# ============================================================
# DESPERTAR MPU
# ============================================================

i2c.writeto_mem(
    MPU_ADDR,
    0x6B,
    b'\x00'
)

time.sleep_ms(
    200
)


# ============================================================
# FUNCION 16 BITS
# ============================================================

def convertir_16bits(
    alto,
    bajo
):

    valor = (
        alto << 8
    ) | bajo


    if valor >= 32768:
        valor -= 65536


    return valor


# ============================================================
# LEER MPU
# ============================================================

def leer_mpu():

    datos = i2c.readfrom_mem(
        MPU_ADDR,
        0x3B,
        14
    )


    ax_raw = convertir_16bits(
        datos[0],
        datos[1]
    )


    ay_raw = convertir_16bits(
        datos[2],
        datos[3]
    )


    az_raw = convertir_16bits(
        datos[4],
        datos[5]
    )


    gx_raw = convertir_16bits(
        datos[8],
        datos[9]
    )


    gy_raw = convertir_16bits(
        datos[10],
        datos[11]
    )


    gz_raw = convertir_16bits(
        datos[12],
        datos[13]
    )


    # Acelerometro

    ax = ax_raw / 16384.0
    ay = ay_raw / 16384.0
    az = az_raw / 16384.0


    # Giroscopio

    gx = gx_raw / 131.0
    gy = gy_raw / 131.0
    gz = gz_raw / 131.0


    return (
        ax,
        ay,
        az,
        gx,
        gy,
        gz
    )


# ============================================================
# CALCULAR ANGULOS
# ============================================================

def calcular_angulos(
    ax,
    ay,
    az
):

    roll = math.degrees(
        math.atan2(
            ay,
            az
        )
    )


    pitch = math.degrees(
        math.atan2(
            -ax,
            math.sqrt(
                ay * ay
                +
                az * az
            )
        )
    )


    return (
        roll,
        pitch
    )


# ============================================================
# CALIBRAR MPU ANTES DE ACTIVAR SERVOS
# ============================================================

print("================================")
print("          CALIBRACION")
print("================================")
print()

print("DEJA LA CUCHARA QUIETA")
print("Y NIVELADA")
print()

print("NO LA MUEVAS...")
print()


suma_roll = 0
suma_pitch = 0

MUESTRAS = 100


for i in range(
    MUESTRAS
):

    ax, ay, az, gx, gy, gz = leer_mpu()


    roll, pitch = calcular_angulos(
        ax,
        ay,
        az
    )


    suma_roll += roll
    suma_pitch += pitch


    time.sleep_ms(
        20
    )


ROLL_BASE = (
    suma_roll
    /
    MUESTRAS
)


PITCH_BASE = (
    suma_pitch
    /
    MUESTRAS
)


print()
print("CALIBRACION TERMINADA")
print()


print(
    "Roll inicial:",
    round(
        ROLL_BASE,
        2
    )
)


print(
    "Pitch inicial:",
    round(
        PITCH_BASE,
        2
    )
)


print()


# ============================================================
# ACTIVAR SERVOS
# ============================================================

servo_x = PWM(
    Pin(SERVO_X_PIN),
    freq=50
)


servo_y = PWM(
    Pin(SERVO_Y_PIN),
    freq=50
)


# ============================================================
# MOVER SERVO
# ============================================================

def mover_servo(
    servo,
    angulo,
    minimo,
    maximo
):

    if angulo < minimo:
        angulo = minimo


    if angulo > maximo:
        angulo = maximo


    pulso = (
        500
        +
        (angulo / 180.0)
        *
        2000
    )


    duty = int(
        pulso
        /
        20000
        *
        65535
    )


    servo.duty_u16(
        duty
    )


# ============================================================
# MOVIMIENTO
# ============================================================

def movimiento_rapido(
    actual,
    objetivo
):

    diferencia = (
        objetivo
        -
        actual
    )


    if diferencia > PASO_MAXIMO:

        return (
            actual
            +
            PASO_MAXIMO
        )


    if diferencia < -PASO_MAXIMO:

        return (
            actual
            -
            PASO_MAXIMO
        )


    return objetivo


# ============================================================
# POSICIONES INICIALES
# ============================================================

posicion_x_actual = CENTRO_X
posicion_y_actual = CENTRO_Y


print("Activando Servo X...")
print("Activando Servo Y...")


mover_servo(
    servo_x,
    CENTRO_X,
    MIN_X,
    MAX_X
)


time.sleep_ms(
    300
)


mover_servo(
    servo_y,
    CENTRO_Y,
    MIN_Y,
    MAX_Y
)


time.sleep(
    1
)


print()
print("Servo X = LISTO")
print("Servo Y = LISTO")
print()


# ============================================================
# FILTRO
# ============================================================

roll_filtrado = ROLL_BASE
pitch_filtrado = PITCH_BASE


# ============================================================
# ESTABILIZACION
# ============================================================

print("================================")
print("    ESTABILIZACION ACTIVADA")
print("================================")
print()

print("IZQUIERDA / DERECHA")
print("-> SERVO X")
print()

print("ARRIBA / ABAJO")
print("-> SERVO Y")
print()

print("Servo X NO debe mover Y")
print("Servo Y NO debe mover X")
print()

print("Ctrl+C para detener")
print()


try:

    while True:


        # ====================================================
        # LEER SENSOR
        # ====================================================

        ax, ay, az, gx, gy, gz = leer_mpu()


        roll, pitch = calcular_angulos(
            ax,
            ay,
            az
        )


        # ====================================================
        # FILTRO
        # ====================================================

        roll_filtrado = (
            roll_filtrado
            *
            (1 - ALPHA)
            +
            roll
            *
            ALPHA
        )


        pitch_filtrado = (
            pitch_filtrado
            *
            (1 - ALPHA)
            +
            pitch
            *
            ALPHA
        )


        # ====================================================
        # EJES
        #
        # PITCH = X
        # ROLL  = Y
        # ====================================================

        error_x = (
            pitch_filtrado
            -
            PITCH_BASE
        )


        error_y = (
            roll_filtrado
            -
            ROLL_BASE
        )


        # ====================================================
        # ZONA MUERTA
        # ====================================================

        if abs(
            error_x
        ) < ZONA_MUERTA:

            error_x = 0


        if abs(
            error_y
        ) < ZONA_MUERTA:

            error_y = 0


        # ====================================================
        # CALCULAR SERVO X
        # ====================================================

        posicion_x_objetivo = (
            CENTRO_X
            +
            SIGNO_X
            *
            error_x
            *
            GANANCIA_X
        )


        # ====================================================
        # CALCULAR SERVO Y
        # ====================================================

        posicion_y_objetivo = (
            CENTRO_Y
            +
            SIGNO_Y
            *
            error_y
            *
            GANANCIA_Y
        )


        # ====================================================
        # LIMITES X
        # ====================================================

        if posicion_x_objetivo < MIN_X:
            posicion_x_objetivo = MIN_X


        if posicion_x_objetivo > MAX_X:
            posicion_x_objetivo = MAX_X


        # ====================================================
        # LIMITES Y
        # ====================================================

        if posicion_y_objetivo < MIN_Y:
            posicion_y_objetivo = MIN_Y


        if posicion_y_objetivo > MAX_Y:
            posicion_y_objetivo = MAX_Y


        # ====================================================
        # MOVIMIENTO X
        # ====================================================

        posicion_x_actual = movimiento_rapido(
            posicion_x_actual,
            posicion_x_objetivo
        )


        # ====================================================
        # MOVIMIENTO Y
        # ====================================================

        posicion_y_actual = movimiento_rapido(
            posicion_y_actual,
            posicion_y_objetivo
        )


        # ====================================================
        # MOVER SERVO X
        # ====================================================

        mover_servo(
            servo_x,
            posicion_x_actual,
            MIN_X,
            MAX_X
        )


        # ====================================================
        # MOVER SERVO Y
        # ====================================================

        mover_servo(
            servo_y,
            posicion_y_actual,
            MIN_Y,
            MAX_Y
        )


        # ====================================================
        # CONSOLA
        # ====================================================

        print(
            "X:",
            round(
                error_x,
                1
            ),

            "| Servo X:",
            round(
                posicion_x_actual,
                1
            ),

            "|| Y:",
            round(
                error_y,
                1
            ),

            "| Servo Y:",
            round(
                posicion_y_actual,
                1
            )
        )


        # ====================================================
        # CICLO
        # ====================================================

        time.sleep_ms(
            TIEMPO_CICLO
        )


# ============================================================
# DETENER
# ============================================================

except KeyboardInterrupt:

    print()
    print("================================")
    print("       PRUEBA DETENIDA")
    print("================================")
    print()


    print(
        "Regresando servos al centro..."
    )


    while (
        abs(
            posicion_x_actual
            -
            CENTRO_X
        ) > 0.1

        or

        abs(
            posicion_y_actual
            -
            CENTRO_Y
        ) > 0.1
    ):


        posicion_x_actual = movimiento_rapido(
            posicion_x_actual,
            CENTRO_X
        )


        posicion_y_actual = movimiento_rapido(
            posicion_y_actual,
            CENTRO_Y
        )


        mover_servo(
            servo_x,
            posicion_x_actual,
            MIN_X,
            MAX_X
        )


        mover_servo(
            servo_y,
            posicion_y_actual,
            MIN_Y,
            MAX_Y
        )


        time.sleep_ms(
            TIEMPO_CICLO
        )


    time.sleep(
        1
    )


    servo_x.deinit()
    servo_y.deinit()


    print()
    print("Servo X = OFF")
    print("Servo Y = OFF")
    print("FIN")	