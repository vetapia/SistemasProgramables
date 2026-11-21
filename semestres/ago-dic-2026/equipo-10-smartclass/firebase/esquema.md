# Esquema Firebase — SmartClass

Base de datos: **Cloud Firestore** (proyecto `smartclass`).

El servidor Python (`servidor/firebase_opcional.py`) escribe en Firestore desde un hilo aparte, para no frenar el reconocimiento facial. El dashboard lee de ahí el histórico. Si no existe la llave `serviceAccountKey.json`, el sistema funciona igual pero sin guardar en la nube.

## Colecciones

### `lecturas/{timestamp}`
Histórico de sensores (una lectura por minuto, ajustable con `INTERVALO_LECTURAS_S`).

| Campo            | Tipo      | Ejemplo               | Descripción                       |
|------------------|-----------|-----------------------|-----------------------------------|
| `temperatura`    | number    | `23`                  | Temperatura en °C (DHT11)         |
| `humedad`        | number    | `74`                  | Humedad relativa en % (DHT11)     |
| `distancia_cm`   | number    | `51.5`                | Distancia en cm (ultrasónico)     |
| `ir_puerta`      | number    | `0`                   | Sensor infrarrojo de la puerta    |
| `ir_dispensador` | number    | `1`                   | Sensor infrarrojo del dispensador |
| `timestamp`      | string    | `2026-11-14T01:59:33` | Fecha y hora de la lectura        |
| `creado`         | timestamp | —                     | Marca de tiempo de Firestore      |

### `eventos_ia/{timestamp}`
Una decisión de la IA por cada reconocimiento (los desconocidos se guardan como máximo cada 5 segundos).

| Campo               | Tipo      | Ejemplo                                         | Descripción                         |
|---------------------|-----------|-------------------------------------------------|-------------------------------------|
| `deteccion`         | string    | `8203786e` / `desconocido`                      | `alumno_id` del alumno reconocido, o `desconocido` |
| `confianza`         | number    | `0.852`                                         | Similitud del rostro (0 a 1)        |
| `accion`            | string    | `anillo_verde+buzzer_corto+pantalla_bienvenida` | Respuesta de los actuadores         |
| `alumno_id`         | string    | `8203786e`                                      | Identificador del alumno (no se guarda el nombre) |
| `asistencia_nueva`  | boolean   | `true`                                          | Si se registró una asistencia nueva |
| `fecha` / `hora`    | string    | `2026-11-14` / `01:57:32`                       | Fecha y hora del evento             |
| `timestamp`         | string    | `2026-11-14T01:57:32`                           | Fecha y hora completas              |
| `creado`            | timestamp | —                                               | Marca de tiempo de Firestore        |

Cuando el rostro no coincide con ningún alumno, `deteccion` es `desconocido`, la confianza es baja y la acción es `anillo_rojo+buzzer_largo`.

### `asistencias/{timestamp}`
Primera llegada de cada alumno en el día.

| Campo       | Tipo      | Ejemplo               | Descripción                  |
|-------------|-----------|-----------------------|------------------------------|
| `alumno_id` | string    | `8203786e`            | Identificador del alumno (no se guarda el nombre) |
| `fecha`     | string    | `2026-11-14`          | Fecha de la asistencia       |
| `hora`      | string    | `02:00:03`            | Hora de llegada              |
| `timestamp` | string    | `2026-11-14T02:00:03` | Fecha y hora completas       |
| `creado`    | timestamp | —                     | Marca de tiempo de Firestore |

### `estado_actual/actual`
Un solo documento con el último estado del sistema, que se actualiza cada vez que cambia un actuador y cada 15 segundos.

| Campo                       | Tipo    | Ejemplo | Descripción                           |
|-----------------------------|---------|---------|---------------------------------------|
| `temperatura`, `humedad`    | number  | `23`    | Últimas lecturas del DHT11            |
| `distancia_cm`              | number  | `51.5`  | Última distancia                      |
| `ir_puerta`, `ir_dispensador` | number | `0`    | Último estado de los sensores IR      |
| `bomba`                     | string  | `OFF`   | Estado de la bomba de gel             |
| `ventilador`                | string  | `ON`    | Estado del ventilador                 |
| `nodo_puerta_en_linea`      | boolean | `true`  | El nodo puerta respondió hace menos de 30 s |
| `nodo_dispensador_en_linea` | boolean | `true`  | El nodo dispensador respondió hace menos de 30 s |

### `decisiones/{id}`
Colección del Sprint 2, con la primera versión del servidor: guardaba una decisión por cada frame (`clase`: `persona` o `sin_rostro`, `rostros`, `actuador`, `origen`). En la versión final las decisiones se guardan en `eventos_ia`.

## Estructura resumida

```
/lecturas/{timestamp}        → temperatura, humedad, distancia_cm, ir_puerta, ir_dispensador
/eventos_ia/{timestamp}      → deteccion (alumno_id), confianza, accion, alumno_id, asistencia_nueva
/asistencias/{timestamp}     → alumno_id, fecha, hora
/estado_actual/actual        → último estado de sensores, actuadores y nodos
```

## Privacidad

Por ser reconocimiento facial, Firebase guarda solo `alumno_id`, un código aleatorio de 8 caracteres, y nunca el nombre del alumno. La relación id-nombre está únicamente en la laptop del servidor (`servidor/datos/alumnos.json`), que no se sube al repositorio. Tampoco se guardan fotos en Firebase.

## Reglas de seguridad

Las reglas de Firestore (`reglas.json`) bloquean toda lectura y escritura desde clientes (`allow read, write: if false`). Solo el servidor puede leer y escribir, porque usa la llave de servicio de Firebase Admin (`serviceAccountKey.json`), que no se sube al repositorio, y los datos se consultan en la consola de Firebase únicamente con las cuentas de Google del equipo que tienen acceso al proyecto.
