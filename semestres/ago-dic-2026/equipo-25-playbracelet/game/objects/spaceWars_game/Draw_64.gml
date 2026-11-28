if(global.debug){
	draw_text(20,100,gm_cont);	
}

draw_set_font(fnt_gui);
draw_set_halign(fa_middle);

var _x = display_get_gui_width()/2;
var _y = display_get_gui_height()/2;

if(!instance_exists(obj_pShip)){
	if(respawn_timer <= 0){
		instance_create_layer(respawn_x,respawn_y,"Instances",obj_pShip);
		respawn_timer = respawn_delay;
	}else{
		draw_text(_x,_y,$"Reapareciendo en...{int64(respawn_timer/60)+1}");
		respawn_timer--;	
	}
}

if(state == 0){
	draw_set_color(c_yellow);
	draw_text_transformed(_x,_y,"CityDefender",3,3,0);
	draw_set_color(c_white);
	draw_text(_x,_y+48,$"La invasión empezará en...{int64(gm_cont/60)+1}");
}