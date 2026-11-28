var _in = global.inputs;
var _c = sprite_width/2;

x += (_in.right - _in.left)*walksp;
y += (_in.down - _in.up)*walksp;

x = clamp(x,_c+32*6,room_width-_c-32*5);
y = clamp(y,_c,room_height-_c-64);

y -= global.flex1;
if(global.flex1 == 0) y += 1;
y += 0.2;
x += _in.angle*walksp;


var _aimbot = collision_rectangle(x-8,y,x+8,0,enemy_father,0,1);
if(_aimbot != noone){
	if(stm <= 0){
		var _blt = instance_create_layer(x,y,"Instances",obj_bullet);
		stm = stm_rch;
	}
}
if(stm > 0) stm--;