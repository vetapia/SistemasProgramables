@echo off

:: Abre la primera ventana, va a la carpeta de Angel y ejecuta Mosquitto
start "Mosquitto" cmd /k "cd /d C:\Users\angel && mosquitto -v -c mosquitto.conf"

:: Abre la segunda ventana, va a Descargas y ejecuta el script de Python
start "Python Firebase" cmd /k "cd /d C:\Users\angel\Downloads && C:\Users\angel\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe firebase.py"

start "Python Detector" cmd /k "cd /d C:\Users\angel\Downloads && C:\Users\angel\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe detector.py"