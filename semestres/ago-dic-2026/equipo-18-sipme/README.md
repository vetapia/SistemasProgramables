# Prestamo material electronico

Sistema para el control y registro de prestamos de material y componentes electronicos a estudiantes. Cuenta con una API central, interfaz web administrativa y terminales fisicas basadas en microcontroladores ESP32 para la gestion en sitio.

## Componentes

- **ElectronicLoanSystemBackend**: API REST en .NET con Entity Framework Core y PostgreSQL. Administra autenticacion JWT, inventario de materiales, usuarios y prestamos.
- **ElectronicLoanSystemWebClient**: Interfaz web administrativa desarrollada en Angular, Tailwind CSS y DaisyUI.
- **ElectronicLoanSystemEsp32Client**: Terminal de interaccion en MicroPython. Integra lector NFC PN532 para credenciales, teclado matricial, pantalla ST7735 y buzzer. Realiza peticiones HTTP al backend y publica eventos via MQTT.
- **ElectronicLoansSystemEsp32Client2**: Modulo actuador en MicroPython. Se conecta por MQTT para escuchar comandos de apertura o bloqueo y acciona servomotores para liberar el material.

## Puesta en marcha

### 1. Base de datos
El backend requiere PostgreSQL en ejecucion en el puerto 5432.

Conexion por defecto en ElectronicLoanSystemBackend/ElectronicLoanSystem/appsettings.json:
- Host: localhost:5432
- Base de datos: ElectronicLoanSystem
- Usuario: postgres

Ajusta usuario y contrasena segun tu entorno local.

### 2. Backend en .NET

Requisitos: .NET SDK instalado.

```bash
cd ElectronicLoanSystemBackend/ElectronicLoanSystem

# Aplicar migraciones
dotnet ef database update

# Ejecutar la API
dotnet run
```

### 3. Cliente Web en Angular

Requisitos: Node.js y npm instalados.

```bash
cd ElectronicLoanSystemWebClient

# Instalar dependencias
npm install

# Iniciar servidor local
npm start
```
Disponible por defecto en http://localhost:4200.

### 4. Clientes ESP32 con MicroPython

Requisitos: Placa ESP32 con firmware MicroPython y la herramienta mpremote instalada.

Pasos para la terminal principal ElectronicLoanSystemEsp32Client:
1. Conectar la placa por puerto USB.
2. Configurar credenciales WiFi y broker MQTT en constants.py y network_manager.py dentro de src/.
3. Cargar el codigo al microcontrolador con mpremote:
```bash
cd ElectronicLoanSystemEsp32Client/src
mpremote cp * :
```

Pasos para el modulo actuador ElectronicLoansSystemEsp32Client2:
1. Conectar la placa por puerto USB.
2. Configurar credenciales WiFi y broker MQTT en constants.py y app.py dentro de src/.
3. Cargar el codigo al microcontrolador con mpremote:
```bash
cd ElectronicLoansSystemEsp32Client2/src
mpremote cp * :
```
