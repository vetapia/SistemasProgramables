# ============================================
# Proyecto:  SafeDrop
# Archivo:   main.py
# Objetivo:  Recibir fotogramas RGB565 y decodificar QR con OpenCV y pyzbar.
# Equipo:    09
# Integrantes:
#   Alan Medina Rivas - 23240436
#   Victor Hugo Ojeda Cabrera - 23240390
# Materia:   Sistemas Programables - ISC TecNM Leon
# Semestre:  ago-dic-2026
# ============================================

import socket
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import struct

HOST = '0.0.0.0' 
PORT = 5000

print(f"Servidor SafeDrop IA iniciado. Escuchando en el puerto {PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    
    while True:
        print("\nEsperando datos RAW desde la ESP32-S3...")
        conn, addr = s.accept()
        with conn:
            print(f"¡Conexión entrante desde {addr}!")
            
            # 1. Recibir los primeros 8 bytes (Ancho y Alto)
            header_data = conn.recv(8)
            if len(header_data) < 8:
                print("Error: Cabecera incompleta.")
                continue
                
            ancho, alto = struct.unpack("<II", header_data)
            print(f"Dimensiones de la imagen entrante: {ancho} x {alto}")
            
            # 2. Calcular los bytes a recibir (2 bytes por píxel en RGB565)
            bytes_esperados = ancho * alto * 2
            data = bytearray()
            
            # 3. Recibir el flujo de datos completo
            while len(data) < bytes_esperados:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data.extend(chunk)

            print(f"Recibidos {len(data)} / {bytes_esperados} bytes.")

            if len(data) == bytes_esperados:
                # 4. Magia Senior: Corregir colores (Endianness Byte Swap)
                # Volteamos los bytes (de Little a Big Endian o viceversa)
                img_array_16 = np.frombuffer(data, dtype=np.uint16).byteswap()
                
                # Reconstruimos la matriz de 8 bits para OpenCV
                img_array_8 = img_array_16.view(np.uint8).reshape((alto, ancho, 2))
                
                # Convertimos usando la constante BGR565 que sí existe en OpenCV
                img = cv2.cvtColor(img_array_8, cv2.COLOR_BGR5652BGR)

                # 4.5. Ampliar la imagen mediante software (Interpolación)
                # Como el módulo de tu cámara quedó en 160x120, la ampliamos artificialmente a 640x480
                img_grande = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LINEAR)

                # Guardamos la imagen procesada
                nombre_archivo = "vista_safedrop_corregida.jpg"
                cv2.imwrite(nombre_archivo, img_grande)
                
                # 5. Escaneo del QR en la imagen ampliada
                print("Procesando IA para buscar Código QR...")
                qrs_detectados = decode(img_grande)
                
                if qrs_detectados:
                    for qr in qrs_detectados:
                        codigo = qr.data.decode('utf-8')
                        print(f"✅ ¡ÉXITO! Código QR detectado: {codigo}")
                        
                        # Dibujar rectángulo verde alrededor del QR detectado
                        pts = np.array([qr.polygon], np.int32).reshape((-1, 1, 2))
                        cv2.polylines(img_grande, [pts], True, (0, 255, 0), 3)
                else:
                    print("❌ No se detectó código QR en esta imagen.")

                # Mostrar resultado en pantalla (Presiona cualquier tecla para cerrar la foto)
                cv2.imshow("Ojo del SafeDrop", img_grande)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print("Error: Los bytes recibidos no coinciden con la resolución.")