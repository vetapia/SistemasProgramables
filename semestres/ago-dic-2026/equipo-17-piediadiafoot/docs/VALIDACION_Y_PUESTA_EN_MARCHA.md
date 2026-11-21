# Validación y puesta en marcha — lista de control - PIE DIABETICO - DIA FOOD

**Integrantes:**
1. GEOVANNI MORENO GOMEZ       | 23240475 |
2. DANNA VALERIA ANGELES PEREZ | 23240335 |
3. ANDREA LOPEZ ESTRADA        | 23240168 |  

## Fase 0 — Antes de cargar

- [x] Guardar copia de seguridad de los programas funcionales actuales.
- [x] Actualizar SSID/contraseña Wi-Fi en los JSON y WROVER local.
- [x] Rotar credenciales MQTT.
- [x] Confirmar IP de laptop, WROVER y broker.
- [x] Actualizar ACL y reiniciar Mosquitto.

## Fase 1 — DevKit sin potencia de actuadores

- [x] Copiar los archivos DevKit a la raíz de MicroPython.
- [x] Confirmar que LCD 1602 responde.
- [x] Confirmar que OLED responde. 
- [x] Confirmar lectura FSR por ADC34.
- [x] Confirmar HC-SR04; usar divisor/adaptador de nivel en ECHO.
- [x] Confirmar MLX90614 en I2C 0x5A.
- [x] Confirmar buzzer.
- [x] Confirmar servo y ángulos de bandera sin forzar el mecanismo.
- [x] Confirmar que ambos relevadores de motor quedan apagados al iniciar.
- [x] Confirmar conexión Wi-Fi y MQTT.

## Fase 2 — Integración MQTT

- [x] Verificar publicación `proyecto/sensores/lectura`.
- [x] Verificar publicación `proyecto/actuador/estado`.
- [x] Verificar suscripción DevKit a `proyecto/actuador/cmd`.
- [x] Verificar suscripción DevKit a `proyecto/ia/decision`.
- [x] Verificar suscripción DevKit a `proyecto/camara/estado`.
- [x] Ejecutar YOLO y verificar detecciones recibidas por DevKit.
- [ ] Verificar que la pérdida MQTT apague ventilador/LEDs y baje bandera.

## Fase 3 — Banda/motor (no iniciar hasta autorización eléctrica)

- [x] Identificar modelo exacto del motoreductor y corriente nominal.
- [x] Obtener/medir corriente de arranque y corriente de bloqueo mediante procedimiento/equipo adecuado; no bloquear el motor manualmente.
- [x] Dimensionar fuente y etapa de inversión para corriente inductiva real.
- [x] Verificar la capacidad DC inductiva de relevadores/controlador.
- [x] Colocar topes mecánicos resistentes y, preferiblemente, finales de carrera eléctricos.
- [x] Confirmar polaridad y sentido con el motor desacoplado de la banda.
- [x] Calibrar desplazamiento por pulso con regla, mecanismo libre y operador observando.
- [x] Establecer `motor_enabled=true` sólo después de completar los puntos anteriores.
- [x] Establecer `physical_stops_confirmed=true` sólo después de inspeccionar los topes instalados.
- [x] Si se calibra, introducir `cm_per_100ms` en cm por cada 100 ms de activación.

## Fase 4 — Calibración de sensores y lógica

- [ ] FSR sin pie, apoyo normal y presión firme: registrar muestras ADC; ajustar umbrales e histéresis.
- [x] Medir referencia HC-SR04 desde cara de transductores al plano del tope del talón.
- [x] Verificar distancia de sensor a dedos con un objeto patrón y pie de prueba.
- [x] Comprobar línea de visión MLX90614, lecturas ambiente/objeto y estabilidad.
- [ ] Ajustar el criterio térmico; sólo entonces poner `temperature_validation_enabled=true` y establecer `temperature_delta_min_c` si las pruebas lo respaldan.
- [ ] Ajustar ángulos oculto/listo de la bandera.
- [x] Ajustar umbrales de posición y temporización de retiro del pie.

## Fase 5 — Flujo de sesión

- [x] Marcar centro con C mientras el carro está físicamente sobre la marca central.
- [x] Colocar el pie; comprobar FSR y distancia.
- [x] Confirmar talón con A.
- [x] Revisar temperatura y confirmar con T mientras el criterio automático siga deshabilitado.
- [x] Esperar estado de cámara/YOLO.
- [x] Ajustar encuadre manualmente y confirmar con V.
- [ ] Confirmar ventilador/LEDs y bandera LISTO.
- [x] Tomar varias fotografías con P y comprobar original, anotada y JSON.
- [x] Finalizar con N; esperar retiro del pie; comprobar ventilador/LEDs OFF y bandera abajo.
- [x] Regresar MANUALMENTE la cámara a la marca central y pulsar C para confirmar el centro.
- [x] Comprobar emergencia E y rearme R.

