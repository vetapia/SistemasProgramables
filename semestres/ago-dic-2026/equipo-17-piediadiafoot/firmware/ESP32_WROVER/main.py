"""
============================================
 Proyecto:  PIE DIABETICO - DIA FOOD
 Archivo:   main.py
 Objetivo:  ESP32-WROVER con firmware MicroPython Camera API
 Equipo:
    GEOVANNI MORENO GOMEZ       | 23240475 |
    DANNA VALERIA ANGELES PEREZ | 23240335 |
    ANDREA LOPEZ ESTRADA        | 23240168 |
 Materia:   Sistemas Programables — ISC TecNM León
 Semestre:  ago-dic-2026
============================================
"""

import network
import socket
import time
import gc
from camera import Camera, FrameSize, PixelFormat

ssid = 'REEMPLAZAR_WIFI_SSID'
password = 'REEMPLAZAR_WIFI_PASSWORD'

station = network.WLAN(network.STA_IF)
if station.active():
    station.active(False)
    time.sleep(1)
station.active(True)
time.sleep(0.5)
if not station.isconnected():
    print('Conectando a la red', ssid, '...')
    station.connect(ssid, password)
    intentos = 0
    while not station.isconnected() and intentos < 25:
        time.sleep(0.5)
        intentos += 1
if station.isconnected():
    ip = station.ifconfig()[0]
    print('Wi-Fi OK. Abre: http://{}'.format(ip))
else:
    print('Error: no se pudo conectar al Wi-Fi. Reiniciando...')
    time.sleep(2)
    import machine
    machine.reset()

cam = Camera(
    frame_size=FrameSize.QVGA,
    pixel_format=PixelFormat.RGB565,
    xclk_freq=20000000,
    init=True
)

#Interfaz web que decodifica RGB565 en el navegador.
html = r'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vision Dia Foot - Camara</title>
<style>
body{font-family:Arial,sans-serif;background:#f0f2f5;color:#222;text-align:center;margin:20px}
canvas{max-width:100%;height:auto;border:2px solid #ccc;background:#000;image-rendering:pixelated}
#status{margin:10px;font-size:15px}
</style></head><body><h2>Vision Dia Foot - ESP32-WROVER</h2>
<canvas id="videoCanvas" width="320" height="240"></canvas><div id="status">Conectando...</div>
<script>
const canvas=document.getElementById('videoCanvas'),ctx=canvas.getContext('2d'),statusDiv=document.getElementById('status');
function rgb565ToRgba(raw){
 const swapped=new Uint8Array(raw.length);
 for(let i=0;i+1<raw.length;i+=2){swapped[i]=raw[i+1];swapped[i+1]=raw[i];}
 const p=new Uint16Array(swapped.buffer),rgba=new Uint8ClampedArray(p.length*4);
 for(let i=0;i<p.length;i++){
  const c=p[i],r=((c>>11)&31)*255/31,g=((c>>5)&63)*255/63,b=(c&31)*255/31,j=i*4;
  rgba[j]=r;rgba[j+1]=g;rgba[j+2]=b;rgba[j+3]=255;
 }
 return {rgba,pixels:p.length};
}
async function nextFrame(){
 try{
  const response=await fetch('/frame?ts='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw new Error('HTTP '+response.status);
  const raw=await response.arrayBuffer();
  if(!raw.byteLength)throw new Error('Fotograma vacio');
  const converted=rgb565ToRgba(new Uint8Array(raw));
  let w=320,h=240;
  if(converted.pixels!==w*h){
   if(converted.pixels===160*120){w=160;h=120;}
   else if(converted.pixels===640*480){w=640;h=480;}
   else throw new Error('Tamano de fotograma inesperado: '+converted.pixels);
  }
  if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  ctx.putImageData(new ImageData(converted.rgba,w,h),0,0);
  statusDiv.textContent='Camara activa: '+w+'x'+h;
  setTimeout(nextFrame,100);
 }catch(e){statusDiv.textContent='Error de conexion: '+e.message;setTimeout(nextFrame,1000);}
}
nextFrame();
</script></body></html>'''

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(2)
print('Servidor HTTP de camara listo en:', addr)
print('Pagina: http://{}/'.format(station.ifconfig()[0]))
print('Fotogramas RGB565: http://{}/frame'.format(station.ifconfig()[0]))

def handle_client(client):
    try:
        client.settimeout(3)
        request = client.recv(1024).decode('utf-8', 'ignore')
        first_line = request.split('\r\n', 1)[0] if request else ''
        parts = first_line.split(' ')
        path = parts[1] if len(parts) >= 2 else '/'
        if path.startswith('/frame'):
            frame = cam.capture()
            if not frame:
                client.sendall(b'HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
                return
            header = (
                'HTTP/1.1 200 OK\r\n'
                'Content-Type: application/octet-stream\r\n'
                'Content-Length: {}\r\n'.format(len(frame)) +
                'Cache-Control: no-store\r\n'
                'Access-Control-Allow-Origin: *\r\n'
                'Connection: close\r\n\r\n'
            )
            client.sendall(header.encode('utf-8'))
            client.sendall(frame)
        else:
            body = html.encode('utf-8')
            header = (
                'HTTP/1.1 200 OK\r\n'
                'Content-Type: text/html; charset=utf-8\r\n'
                'Content-Length: {}\r\n'.format(len(body)) +
                'Cache-Control: no-store\r\n'
                'Connection: close\r\n\r\n'
            )
            client.sendall(header.encode('utf-8'))
            client.sendall(body)
    except Exception as e:
        print('Error atendiendo cliente HTTP:', e)
    finally:
        try:
            client.close()
        except Exception:
            pass
        gc.collect()

print('Servidor listo; esperando solicitudes HTTP...')
try:
    while True:
        try:
            client, remote = s.accept()
            print('Solicitud HTTP desde:', remote)
        except KeyboardInterrupt:
            print('Programa detenido por el usuario.')
            break
        except Exception as e:
            print('Error al aceptar conexion:', repr(e))
            time.sleep(0.2)
            continue
        handle_client(client)
finally:
    try:
        cam.deinit()
    except Exception:
        pass
    try:
        s.close()
    except Exception:
        pass
    try:
        station.active(False)
    except Exception:
        pass
