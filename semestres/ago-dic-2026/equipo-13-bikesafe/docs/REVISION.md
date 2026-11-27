# 📋 Revisión del 25 de noviembre: observaciones y cambios

Respuesta punto por punto al plan de acción de la maestra (PR, equipo 13).

| # | Observación | Qué hicimos | Dónde verlo | Estado |
|---|---|---|---|---|
| 1 | **Soldadura y placa:** no depender de Dupont sueltos (vibración en la bici) | Plan de placa fenólica con headers hembra para la ESP32 y el MPU6050, rieles soldados, conectores para todo lo que sale a la carcasa y revisión con continuidad antes de energizar | [SOLDADURA.md](SOLDADURA.md) · [placa-perforada.png](../hardware/placa-perforada.png) | 🟡 Soldando (Diego) |
| 2 | **3 sensores + 3 actuadores** | **Sensores:** MPU6050, HC-SR04 y **reed switch** del cerrojo (nuevo). **Actuadores:** servo, buzzer y **LED RGB** (nuevo, prestado). El reed impide asegurar si el cable no está metido y dispara ROBO si lo sacan a la fuerza. El RGB muestra el estado con colores | `firmware/esp32/hal/` · pruebas `e13_led_rgb.py` y `e14_cerrojo_reed.py` | ✅ Código · 🟡 montaje |
| 3 | **Sujeción real a la bici** | Abrazadera sin fin inoxidable con hule alrededor del tubo del cuadro, en lugar de la cinta de los tenis. El alcance se redefinió como **sistema de alarma y bloqueo disuasorio**, con sus límites mecánicos explicados | [README › Alcance](../README.md#alcance-y-límites-mecánicos-honestos) | 🟡 Por comprar la abrazadera |
| 4a | **Detección de persona** (MobileNet-SSD / YOLO) en lugar de rostro | YuNet (caras) se reemplazó por **YOLOv5s (COCO, clase "person")** con `cv2.dnn`. MobileNet-SSD no se pudo usar porque OpenCV 5 ya no lee modelos Caffe. Con fotos reales de nuestra cámara detecta cuerpos y hasta una mano | `servidor/ia/detector.py` | ✅ |
| 4b | **La alarma no debe depender de la laptop** | El servidor ya **no** manda órdenes a los actuadores (`alerta_ia` se eliminó): solo publica el resultado firmado. La **ESP32 decide**: con 1 persona da un aviso morado; con 2 personas y la bici movida, ROBO. Sin laptop, la alarma, las fotos y Telegram siguen funcionando | `firmware/esp32/main.py` → `_resultado_ia()` | ✅ |
| 5a | **Firebase no solo para enlazar: guardar y escuchar en tiempo real** | **Guarda:** lecturas, alertas, eventos (historial con origen), eventos_ia y estado. **Escucha:** el dashboard usa `onSnapshot` en 6 consultas y el servidor usa `on_snapshot` sobre `comandos`. Los botones del dashboard → Firestore → servidor → MQTT firmado → ESP32, en menos de 1 s, y el estado del comando se ve en vivo | `servidor/nube.py` · `interfaz/index.html` | ✅ |
| 5b | **Cerrar las reglas de lectura pública (`".read": true`)** | `".read": true` es sintaxis de **Realtime Database**: el proyecto no la tiene creada, lo revisamos en la consola. Aun así dejamos `database.rules.json` con todo en `false`. Las reglas de **Firestore** se publicaron de nuevo el 25/nov: lectura solo para 2 UID, escritura solo para crear comandos validados y cualquier otra ruta cerrada | `interfaz/firestore.rules` · [captura](../media/firestore-reglas-publicadas.jpg) | ✅ |

## Mejoras extra que encontramos al revisar

- **Seguridad MQTT:** `broker.hivemq.com` es público, así que antes cualquiera podía publicar `liberar`. Ahora todo lo que entra a la ESP32 va **firmado con HMAC-SHA256** y lleva un contador anti-repetición guardado en la flash.
- **Conexión en vivo:** con el *last will* de MQTT, el dashboard sabe si la ESP32 se desconectó aunque ya no pueda avisar.
- **Ultrasónico filtrado** con la mediana de 3 lecturas, para que un eco raro no tome fotos falsas.
- **Autodiagnóstico:** si el MPU6050 deja de responder (cable suelto o arrancado), se avisa y se intenta reiniciarlo.
- **Bot:** si alguien ajeno le escribe, se le avisa al dueño. Si se abre desde el dashboard, el dueño recibe un mensaje en Telegram.
- **Cámara:** ping MQTT cada 30 s y reintento, para no perder fotos.
- **Una sola versión del código:** antes había 3 copias distintas (GitHub, OneDrive y las placas). Ahora el repositorio es la única fuente.

## Pruebas antes de cargar a las placas

| Prueba | Resultado |
|---|---|
| Simulación de la ESP32 (máquina de estados, reed, IA, firma, replay, lazo, inclinación, presencia, buscar, LED) | 50 / 50 |
| Simulación de la Freenove (botones, confirmación, extraños, fotos, MQTT con reconexión, sin internet) | 17 / 17 |
| `telegram.py` (peticiones HTTP y lectura de `getUpdates`) | OK |
| Punta a punta con un broker real (placas simuladas + servidor con YOLO + comandos del dashboard) | 18 / 18 |
| Config viejo de la placa (sin los ajustes nuevos) | Arranca y funciona |
