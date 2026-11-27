# 🎤 Guion de la demostración (5 minutos)

## Antes de entrar (checklist)

- [ ] Powerbank cargada y **cable USB "Y"** (o dos cables) para las dos placas
- [ ] WiFi con internet (escuela u hotspot con **"Maximizar compatibilidad"**), el mismo de los dos `config.py`
- [ ] Chat del bot abierto y **proyectado o a la vista** de la maestra
- [ ] Borrar `estado.txt` de la ESP32 para empezar en **LIBRE**
- [ ] Interruptor del lazo en posición **ENTERO** y cable de acero metido en el cerrojo (reed **CERRADO**)
- [ ] Probar una vez **Cerrar → golpecito → Abrir** antes de que les toque
- [ ] Laptop con internet: doble clic en `INICIAR_DEMO.bat` (servidor con IA + dashboard) e iniciar sesión con Google
- [ ] (Opcional) `USAR_WATCHDOG = True` en los dos `config.py` para que se reinicien solas si algo se traba

## Guion

| # | Qué hacen | Qué dicen | Qué se ve |
|---|---|---|---|
| 1 | Conectan la powerbank | "BikeSafe es una alarma con bloqueo que va en la mochila y se sujeta al cuadro con una abrazadera." | LED cian y luego verde parpadeando; llega "BikeSafe encendido" |
| 2 | Tocan **Cerrar** con el cable **fuera** | "El sensor magnético confirma que el cable está metido. Si no, no cierra." | ⛔ "NO cerré…", LED amarillo |
| 3 | Meten el cable y tocan **Cerrar** | "Ahora sí: el servo cierra el pasador." | 🔒 ASEGURADA, LED **azul** |
| 4 | Un golpecito | "Un roce no dispara la sirena: es nivel 1." | 2 pitidos, LED amarillo, ⚠️ foto de AVISO |
| 5 | Se paran frente al candado | "Si alguien se queda junto a la bici, toma foto y la IA busca personas." | 👀 foto de PRESENCIA · 🤖 "la IA confirmó una persona", LED **morado** |
| 6 | Muestran el dashboard | "La IA solo informa; **la ESP32 decide**. Todo queda en Firebase y se ve en vivo." | Foto con recuadro "persona", evento en el historial |
| 7 | Sacan el cable del cerrojo | "Abrir el cerrojo a la fuerza es robo." | 🚨 Sirena, LED **rojo**, ráfaga de 3 fotos |
| 8 | Pican **Silenciar** en el dashboard | "Firebase va en las dos direcciones: el botón se guarda, el servidor lo escucha y se lo manda firmado a la ESP32." | El comando pasa a `enviado` y se calla la sirena |
| 9 | Tocan **Estado** y **Buscar** | "Desde Telegram se revisa todo y se encuentra la bici." | Resumen con cerrojo e IA; suena 5 s con LED blanco |
| 10 | Apagan la laptop y repiten el golpecito | "Sin laptop la alarma sigue funcionando." | Pitidos y foto a Telegram igual |
| 11 | **Abrir → Sí, abrir** | "Abrir siempre pide confirmación." | 🔓 LIBERADA, LED verde |

## Preguntas probables

- **¿Por qué no usaron RFID?** Lo intentamos: el RC522 tuvo un corto por la soldadura y después nunca respondió por SPI. El control desde el celular estaba en nuestro "a futuro" y lo adelantamos. Además es más práctico, porque no hay llavero que perder.
- **¿Y si no hay internet?** El candado sigue vigilando y sonando, porque eso no depende de la red. Las alertas se guardan y se mandan al volver la conexión.
- **¿Y si alguien más le escribe al bot?** Solo obedece el chat del dueño.
- **¿Y si alguien publica "liberar" en el broker público?** Se rechaza: todo lo que entra a la ESP32 va firmado con HMAC-SHA256 y un contador que no se repite.
- **¿Por qué YOLO y no MobileNet-SSD?** OpenCV 5 ya no lee modelos Caffe; YOLOv5 en ONNX corre con `cv2.dnn` en OpenCV 4.8 y 5.
- **¿Es a prueba de cizalla?** No. Es una alarma con bloqueo **disuasorio**: detecta y avisa en segundos. Se recomienda usarla junto con un candado en U.
- **¿Por qué dos placas?** La cámara ocupa casi todos los pines de la Freenove. Así el cerebro tiene pines libres y, si la cámara falla, la alarma sigue funcionando.
