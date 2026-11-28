/// @description Iniciar Servidor UDP

puerto_udp = 6510;
// network_socket_udp indica que es UDP. El "20" es el máximo de conexiones simultáneas.
servidor = network_create_server(network_socket_udp, puerto_udp, 20);

if (servidor < 0) {
    show_debug_message("ERROR: No se pudo abrir el puerto " + string(puerto_udp));
} else {
    show_debug_message("ÉXITO: Servidor UDP escuchando en el puerto " + string(puerto_udp));
}

// Esta variable la usarás en tu juego para saber si el botón está presionado o no
global.giroX = 0;
global.flex1 = 0;