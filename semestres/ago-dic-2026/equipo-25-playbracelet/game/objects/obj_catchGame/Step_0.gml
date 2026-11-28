var _centerX = room_width/2;

if(spawn_timer <= 0){
	var _x = irandom_range(_centerX-spawn_width/2,_centerX+spawn_width/2);
	var _app = instance_create_layer(_x,-32,"Instances",obj_apple);
	_app.fall_speed = apple_speed;
	
	spawn_timer = apple_frec;
}else spawn_timer--;