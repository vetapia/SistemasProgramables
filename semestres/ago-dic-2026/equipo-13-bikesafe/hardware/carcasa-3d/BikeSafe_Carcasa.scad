// BikeSafe · Carcasa de prueba v0.4 · Unidades: mm
// v0.4: + orificios de LED verde/rojo y rejilla de buzzer en la pared frontal (solo cambia la BASE)
// v0.3: hecha para el montaje real de las fotos:
//   - 1 protoboard de 830 puntos (165 x 55) con ESP32 DevKit, LEDs y buzzer (al frente)
//   - 1 mini protoboard de 400 puntos (82 x 55) con Freenove WROVER + MPU6050 (atrás a la derecha)
//   - servo SG90 atrás a la izquierda
//   - más altura para los jumpers (69 mm libres por dentro)
//   - ventana de cámara en la tapa (la cámara apunta hacia arriba)
// Cambios respecto a v0.1 (desde v0.2):
//  - Ultrasónico y (opcional) cámara pasan a la PARED FRONTAL (antes en la tapa, apuntaban al techo)
//  - Ranura en la pared izquierda para la varilla/brazo del servo (pestillo)
//  - Ranuras de ventilación en la pared trasera
//  - Tapa con ceja interior para que encaje y no se deslice
//  - Esquinas: postes de tornillo en lugar de columnas macizas de 15x15 (menos plástico)
//  - Orificios de tornillo redondos
// Selecciona una pieza, pulsa F6 y exporta STL.

/* [Pieza] */
pieza = "base"; // [base,tapa,probeta,conjunto]

/* [Dimensiones de la caja: AJUSTAR con la protoboard real] */
largo = 181;     // X exterior
ancho = 146;     // Y exterior
alto_base = 72;  // Z exterior de la base (sin tapa) -> 69 mm libres por dentro
pared = 3;
piso = 3;
grosor_tapa = 3;

/* [Tornillos] */
centro_tornillo = 8.5;   // distancia del centro del tornillo a cada borde
poste_diametro = 9;
piloto = 2.5;            // cambiar según el resultado de la probeta (2.3 / 2.5 / 2.7)
profundidad_piloto = 12;
paso_tapa = 3.4;         // orificio pasante en la tapa para tornillo de 3 mm

/* [Ceja de la tapa] */
ceja = true;
ceja_alto = 4;
ceja_grosor = 1.6;
holgura = 0.3;           // juego entre ceja y pared interior

/* [Pasos de cables en el borde superior] */
usb = true;
usb_x = 76;   usb_ancho = 26;  usb_bajada = 12;   // pared trasera
lazo = true;
lazo_y = 67;  lazo_ancho = 12; lazo_bajada = 10;  // pared derecha (cable de acero / lazo)

/* [Pared FRONTAL (Y = 0): sensores] */
// Coordenadas: x desde la esquina izquierda, z desde la base del piso.
abrir_ultrasonico = true;          // HC-SR04: dos "ojos" de ~16 mm a 26 mm entre centros
ultrasonico_x = 90.5;
ultrasonico_z = 42;            // alto para que los pines y jumpers del sensor queden arriba de la protoboard
ultrasonico_entre_centros = 26;
ultrasonico_diametro = 17;         // ojo de 16 mm + 1 mm de juego

abrir_camara_frente = false;       // activar cuando sepan dónde queda la lente
camara_x = 145;
camara_z = 30;
camara_ventana = [14, 14];

/* [Pared FRONTAL: LEDs y buzzer] */
abrir_leds_frente = true;          // LED de 5 mm: se pasan con jumpers hembra desde la protoboard
leds_frente_x = [138, 152];        // verde, rojo
leds_frente_z = 42;
led_frente_diametro = 5.3;
abrir_buzzer_frente = true;        // rejilla de 3x3 orificios frente al buzzer
buzzer_frente_x = 40;
buzzer_frente_z = 42;

/* [Pared IZQUIERDA (X = 0): servo / pestillo] */
abrir_servo = true;
servo_y = 95;            // centro de la ranura (servo atrás a la izquierda)
servo_z = 35;
servo_ranura = [10, 22]; // [ancho en Y, alto en Z]

/* [Pared TRASERA (Y = ancho): ventilación] */
ventilacion = true;
vent_ancho = 2.5;
vent_alto = 18;
vent_z = 10;
vent_paso = 7;
vent_cantidad = 5;       // por cada lado de la ranura USB

/* [Tapa: aberturas opcionales] */
abrir_camara_tapa = true;     // ventana grande: pegar la mini protoboard con la lente debajo
camara_tapa_xy = [140, 105];
camara_tapa_ventana = [36, 30];
abrir_leds = false;
led_verde_xy = [40, 30];
led_rojo_xy = [54, 30];
led_diametro = 5.2;
abrir_buzzer = false;
buzzer_xy = [75, 30];
buzzer_diametro = 2.4;

/* [Hidden] */
$fn = 48;
eps = 0.05;

assert(alto_base > piso + max(profundidad_piloto, usb_bajada, lazo_bajada));
assert(paso_tapa > piloto);

module tornillos() {
    for (x = [centro_tornillo, largo-centro_tornillo],
         y = [centro_tornillo, ancho-centro_tornillo])
        translate([x, y, 0]) children();
}

// Poste unido a la esquina (forma de gota, sin columna maciza)
module poste(cx, cy, esq_x, esq_y) {
    hull() {
        translate([cx, cy, 0]) cylinder(d=poste_diametro, h=alto_base);
        translate([esq_x, esq_y, 0]) cube([pared, pared, alto_base]);
    }
}

module agujero_pared_y(x, z, dims, y0) { // agujero rectangular a través de pared frontal/trasera
    translate([x - dims[0]/2, y0 - eps, z - dims[1]/2]) cube([dims[0], pared + 2*eps, dims[1]]);
}

module base() {
    difference() {
        union() {
            difference() {
                cube([largo, ancho, alto_base]);
                translate([pared, pared, piso])
                    cube([largo-2*pared, ancho-2*pared, alto_base]);
            }
            poste(centro_tornillo, centro_tornillo, 0, 0);
            poste(largo-centro_tornillo, centro_tornillo, largo-pared, 0);
            poste(centro_tornillo, ancho-centro_tornillo, 0, ancho-pared);
            poste(largo-centro_tornillo, ancho-centro_tornillo, largo-pared, ancho-pared);
        }
        // pilotos
        tornillos() translate([0, 0, alto_base-profundidad_piloto])
            cylinder(d=piloto, h=profundidad_piloto+eps);
        // USB (trasera) y lazo (derecha)
        if (usb) translate([usb_x, ancho-pared-eps, alto_base-usb_bajada])
            cube([usb_ancho, pared+2*eps, usb_bajada+eps]);
        if (lazo) translate([largo-pared-eps, lazo_y, alto_base-lazo_bajada])
            cube([pared+2*eps, lazo_ancho, lazo_bajada+eps]);
        // Ultrasónico en pared frontal
        if (abrir_ultrasonico)
            for (dx = [-ultrasonico_entre_centros/2, ultrasonico_entre_centros/2])
                translate([ultrasonico_x+dx, -eps, ultrasonico_z])
                    rotate([-90, 0, 0]) cylinder(d=ultrasonico_diametro, h=pared+2*eps);
        // LEDs y buzzer en pared frontal
        if (abrir_leds_frente)
            for (x = leds_frente_x)
                translate([x, -eps, leds_frente_z]) rotate([-90,0,0]) cylinder(d=led_frente_diametro, h=pared+2*eps);
        if (abrir_buzzer_frente)
            for (dx = [-4, 0, 4], dz = [-4, 0, 4])
                translate([buzzer_frente_x+dx, -eps, buzzer_frente_z+dz]) rotate([-90,0,0]) cylinder(d=2.4, h=pared+2*eps);
        // Cámara en pared frontal
        if (abrir_camara_frente) agujero_pared_y(camara_x, camara_z, camara_ventana, 0);
        // Servo en pared izquierda
        if (abrir_servo)
            translate([-eps, servo_y - servo_ranura[0]/2, servo_z - servo_ranura[1]/2])
                cube([pared+2*eps, servo_ranura[0], servo_ranura[1]]);
        // Ventilación en pared trasera, a ambos lados del USB
        if (ventilacion)
            for (i = [0:vent_cantidad-1]) {
                agujero_pared_y(usb_x - 10 - i*vent_paso, vent_z + vent_alto/2, [vent_ancho, vent_alto], ancho-pared);
                agujero_pared_y(usb_x + usb_ancho + 10 + i*vent_paso, vent_z + vent_alto/2, [vent_ancho, vent_alto], ancho-pared);
            }
    }
}

// La tapa se modela en posición de impresión: cara exterior sobre la cama, ceja hacia arriba.
// En "conjunto" se voltea.
module tapa() {
    difference() {
        union() {
            cube([largo, ancho, grosor_tapa]);
            if (ceja) difference() {
                o = pared + holgura;
                translate([o, o, grosor_tapa - eps])
                    cube([largo-2*o, ancho-2*o, ceja_alto+eps]);
                translate([o+ceja_grosor, o+ceja_grosor, grosor_tapa - 2*eps])
                    cube([largo-2*(o+ceja_grosor), ancho-2*(o+ceja_grosor), ceja_alto+4*eps]);
                // libra los postes de las esquinas
                tornillos() translate([0, 0, grosor_tapa-1])
                    cylinder(d=poste_diametro + 2*holgura + 2*ceja_grosor + 4, h=ceja_alto+2);
            }
        }
        tornillos() translate([0, 0, -eps]) cylinder(d=paso_tapa, h=grosor_tapa+ceja_alto+1);
        // Aberturas opcionales (coordenadas en vista superior de la caja armada:
        // al voltear la tapa X se refleja, por eso se usa largo - x)
        if (abrir_camara_tapa)
            translate([largo-camara_tapa_xy[0]-camara_tapa_ventana[0]/2, camara_tapa_xy[1]-camara_tapa_ventana[1]/2, -eps]) cube([camara_tapa_ventana[0], camara_tapa_ventana[1], grosor_tapa+2*eps]);
        if (abrir_leds)
            for (p = [led_verde_xy, led_rojo_xy])
                translate([largo-p[0], p[1], -eps]) cylinder(d=led_diametro, h=grosor_tapa+2*eps);
        if (abrir_buzzer)
            for (dx = [-3.8, 0, 3.8], dy = [-3.8, 0, 3.8])
                translate([largo-buzzer_xy[0]+dx, buzzer_xy[1]+dy, -eps])
                    cylinder(d=buzzer_diametro, h=grosor_tapa+2*eps);
    }
}

module probeta() {
    difference() {
        cube([48, 20, 15]);
        for (i = [0:2])
            translate([8+16*i, 6, 15-12]) cylinder(d=[2.3, 2.5, 2.7][i], h=12+eps);
        translate([24, 15, -eps]) cylinder(d=paso_tapa, h=15+2*eps);
    }
}

module maqueta() { // solo para visualizar, NO se imprime
    color("white") translate([8,18,piso]) cube([165,55,8.5]);
    color("#1b1b1b") translate([60,31,piso+8.5]) cube([52,28,10]);
    color("white") translate([93,77,piso]) cube([82,55,8.5]);
    color("#1b1b1b") translate([105,90,piso+8.5]) cube([58,28,10]);
    color("#cfcfcf") translate([140,105,piso+18.5]) cylinder(d=8,h=5);
    color("#2c4fa8") translate([97,80,piso+8.5]) cube([20,16,3]);
    color("#2a5ad6") translate([12,85,piso]) cube([23,12.2,29]);
    color("#2a5ad6") translate([ultrasonico_x-22.5,pared,ultrasonico_z-10]) cube([45,1.6,20]);
    for(dx=[-13,13]) color("silver") translate([ultrasonico_x+dx,pared+1.6,ultrasonico_z]) rotate([90,0,0]) cylinder(d=16,h=pared+1.6);
}
if (pieza == "base") base();
else if (pieza == "maqueta") { base(); maqueta(); }
else if (pieza == "maqueta_tapa") { base(); maqueta(); color("#e67c39",0.35) translate([largo,0,alto_base+grosor_tapa]) rotate([0,180,0]) tapa(); }
else if (pieza == "tapa") tapa();
else if (pieza == "probeta") probeta();
else if (pieza == "conjunto") {
    color("#263745") base();
    color("#e67c39", 0.6)
        translate([largo, 0, alto_base + grosor_tapa]) rotate([0, 180, 0]) tapa();
}
