/// @description Procesar datos de Node.js

var socket_id = async_load[? "id"];
var tipo_evento = async_load[? "type"];

if (socket_id == servidor && tipo_evento == network_type_data) {
    var buffer = async_load[? "buffer"];
    buffer_seek(buffer, buffer_seek_start, 0);
    
    // buffer_text es obligatorio porque MicroPython envía UTF-8 sin carácter nulo (\0) al final
    var json_texto = buffer_read(buffer, buffer_text);
    
    try {
        var datos = json_parse(json_texto);
        show_debug_message("\x1b[1A\x1b[2K" + string(datos));
		
        if (variable_struct_exists(datos, "inclinacion")) {
            global.giroX = datos.inclinacion;
        }
        if (variable_struct_exists(datos, "flex1")) {
            global.flex1 = datos.flex1;
        }
    } catch (error) {
        show_debug_message("Paquete corrupto ignorado: " + json_texto);
    }
}