from machine import Pin, I2C, PWM
import time
import math


# ============================================================
# TREMORCONTROL AI
# MPU-6050 + SERVO Y RAPIDO
#
# MPU:
# SDA -> GPIO32
# SCL -> GPIO33
#
# SERVO X -> GPIO13   DESACTIVADO
# SERVO Y -> GPIO14   ACTIVO
#
# PITCH = X
# ROLL  = Y
# ============================================================


# =========================
# CONFIGURACION
# =========================

MPU_ADDR = 0x68

SERVO_X_PIN = 13
SERVO_Y_PIN = 14

CENTRO_X = 90
CENTRO_Y = 90

MIN_X = 45
MAX_X = 135

MIN_Y = 45
MAX_Y = 135


# ============================================================
# DIRECCION
# ============================================================

SIGNO_X = -1

# Si levantas la cuchara -> servo Y baja
# Si bajas la cuchara -> servo Y sube
SIGNO_Y = 1


# Fuerza de compensacion
GANANCIA_X = 1.0
GANANCIA_Y = 1.0


# ============================================================
# VELOCIDAD
# ============================================================

# Movimiento maximo por ciclo
PASO_MAXIMO = 8.0

# Tiempo entre ciclos
TIEMPO_CICLO = 10


# Ignorar movimientos pequeños
ZONA_MUERTA = 2.0


# Filtro
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
print("==============================")
print("     TREMORCONTROL AI")
print("==============================")
print()
print("MPU-6050 + SERVO Y")
print("SERVO X DESACTIVADO")
print("MODO RAPIDO ACTIVADO")
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

    raise Exception("MPU-6050 no encontrado")


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

time.sleep_ms(200)


# ============================================================
# SERVO X DESACTIVADO
# ============================================================

servo_x_pin = Pin(
    SERVO_X_PIN,
    Pin.OUT
)

servo_x_pin.value(0)


# ============================================================
# SERVO Y ACTIVO
# ============================================================

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
        * 2000
    )


    duty = int(
        pulso
        /
        20000
        *
        65535
    )


    servo.duty_u16(duty)


# ============================================================
# MOVIMIENTO RAPIDO
# ============================================================

def movimiento_suave(
    actual,
    objetivo
):

    diferencia = (
        objetivo
        -
        actual
    )


    if diferencia > PASO_MAXIMO:
        return actual + PASO_MAXIMO


    if diferencia < -PASO_MAXIMO:
        return actual - PASO_MAXIMO


    return objetivo


# ============================================================
# CONVERTIR 16 BITS
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
# CALIBRACION MPU
# ============================================================

print("==============================")
print("       CALIBRACION")
print("==============================")
print()

print("DEJA LA CUCHARA QUIETA")
print("Y NIVELADA")
print()

print("Servo X = DESACTIVADO")
print()


suma_roll = 0
suma_pitch = 0

MUESTRAS = 100


for i in range(MUESTRAS):

    ax, ay, az, gx, gy, gz = leer_mpu()


    roll, pitch = calcular_angulos(
        ax,
        ay,
        az
    )


    suma_roll += roll
    suma_pitch += pitch


    time.sleep_ms(20)


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
# CENTRAR SERVO Y
# ============================================================

print("Centrando Servo Y...")


mover_servo(
    servo_y,
    CENTRO_Y,
    MIN_Y,
    MAX_Y
)


posicion_y_actual = CENTRO_Y


time.sleep(2)


print()
print("Servo X = OFF")
print("Servo Y = 90 grados")
print()


# ============================================================
# FILTRO
# ============================================================

roll_filtrado = ROLL_BASE
pitch_filtrado = PITCH_BASE


# ============================================================
# ESTABILIZACION
# ============================================================

print("==============================")
print("   ESTABILIZACION ACTIVADA")
print("==============================")
print()

print("Movimiento lateral X")
print("-> Servo Y NO debe moverse")
print()

print("Movimiento arriba/abajo Y")
print("-> Servo Y SI debe compensar")
print()

print("SUBES cuchara -> SERVO BAJA")
print("BAJAS cuchara -> SERVO SUBE")
print()

print("VELOCIDAD: RAPIDA")
print()

print("Ctrl+C para detener")
print()


try:

    while True:


        # ====================================================
        # LEER MPU
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

        if abs(error_x) < ZONA_MUERTA:
            error_x = 0


        if abs(error_y) < ZONA_MUERTA:
            error_y = 0


        # ====================================================
        # CALCULAR POSICION Y
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
        # LIMITES
        # ====================================================

        if posicion_y_objetivo < MIN_Y:
            posicion_y_objetivo = MIN_Y


        if posicion_y_objetivo > MAX_Y:
            posicion_y_objetivo = MAX_Y


        # ====================================================
        # MOVIMIENTO RAPIDO
        # ====================================================

        posicion_y_actual = movimiento_suave(
            posicion_y_actual,
            posicion_y_objetivo
        )


        # ====================================================
        # MOVER SERVO
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
            round(error_x, 1),

            "| Y:",
            round(error_y, 1),

            "| Servo X: OFF",

            "| Servo Y:",
            round(
                posicion_y_actual,
                1
            ),

            "| Roll:",
            round(
                roll_filtrado,
                1
            ),

            "| Pitch:",
            round(
                pitch_filtrado,
                1
            )
        )


        # ====================================================
        # CICLO MAS RAPIDO
        # ====================================================

        time.sleep_ms(
            TIEMPO_CICLO
        )


# ============================================================
# DETENER
# ============================================================

except KeyboardInterrupt:

    print()
    print("==============================")
    print("     PRUEBA DETENIDA")
    print("==============================")
    print()


    print(
        "Regresando Servo Y al centro..."
    )


    while (
        abs(
            posicion_y_actual
            -
            CENTRO_Y
        ) > 0.1
    ):


        posicion_y_actual = movimiento_suave(
            posicion_y_actual,
            CENTRO_Y
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


    time.sleep(1)


    servo_y.deinit()


    servo_x_pin.value(0)


    print()
    print("Servo X: OFF")
    print("Servo Y: OFF")
    print("FIN")
