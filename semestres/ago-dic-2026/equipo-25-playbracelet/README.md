# SistemasProgramables
Segundo intento de creación de repositorio para el proyecto final de la materia de Sistemas Programables 12:10 - 1:50

# PlayBracelete

El PlayBracelete abre un abanico amplio de posibilidades al transformar ejercicios terapéuticos repetitivos en dinámicas de juego interactivo (gamificación) y evaluación médica.

Juegos:
En "El Recolector de Manzanas" (Flexión e inclinación), el jugador inclina el brazo para mover una canasta y flexiona la muñeca para atrapar las frutas que caen, activando la vibración y el sonido del buzzer al lograr el movimiento correcto. 
En "Nave Espacial" (Resistencia y postura), el usuario controla la altura de una nave manteniendo el brazo extendido; mover la nave correctamente acumula puntos que activan un escudo protector impulsado por servomotores y mueve un medidor físico de progreso en el escritorio. El Minijuego con Detección de Dolor (IA futura) utiliza la cámara ESP32-CAM para analizar el rostro del paciente; si detecta gestos de dolor o fatiga, el juego se pausa automáticamente para evitar lesiones.

Componentes:
El Acelerómetro y Giroscopio (MPU6050) mide la inclinación, la orientación y la velocidad de movimiento del brazo en tiempo real. 
El Sensor Flex es una cinta flexible que detecta los grados de flexión de la muñeca o articulación. 
El Mini motor vibrador DC ofrece retroalimentación háptica (vibración) para indicarle al paciente cuando realiza el movimiento con la amplitud correcta. 
El Buzzer pasivo emite tonos de sonido (efectos de recompensa/monedas) al cumplir los objetivos. 
El Pushbutton (Botón) permite al usuario pausar o iniciar la sesión del minijuego fácilmente. 
El Microcontrolador (ESP32) procesa la señal de los sensores y la transmite para controlar el juego y registrar los datos de movilidad.



(Nota: mi cuenta institucional de Github fue baneada, por lo que tuve que usar una cuenta secundaria en su lugar)
