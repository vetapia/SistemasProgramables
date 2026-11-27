# 🧪 Pruebas en la computadora (sin placas)

El firmware de MicroPython se prueba en Python normal con **módulos de mentira** (`fakes/`: `machine`, `network`, `umqtt`; `fakes_cam/`: `camera`, `telegram`) y un **reloj virtual** (`reloj.py`). Así una prueba de 60 s de alarma tarda menos de 1 s.

| Archivo | Qué prueba | Resultado |
|---|---|---|
| `test_esp32.py` | Máquina de estados, reed, IA, firma HMAC, repetición, lazo, inclinación, presencia, Buscar, LED RGB, reinicio | 50 / 50 |
| `test_cam.py` | Bot (botones, confirmación, extraños), fotos, MQTT con reconexión, alertas sin internet | 17 / 17 |
| `test_telegram.py` | Peticiones HTTP a Telegram y lectura de `getUpdates` | OK |
| `test_e2e.py` | **Punta a punta con un broker MQTT real**: ESP32 ↔ UART ↔ Freenove → broker → servidor con YOLO → resultado firmado → la ESP32 decide; también los comandos del dashboard | 18 / 18 |

```bash
cd pruebas_pc
python test_esp32.py
python test_cam.py
python test_telegram.py
# punta a punta: necesita un broker local
pip install amqtt paho-mqtt opencv-python
amqtt &            # broker en localhost:1883
python test_e2e.py
```
