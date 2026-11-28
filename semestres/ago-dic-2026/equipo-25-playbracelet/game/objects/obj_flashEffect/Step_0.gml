if(bg_timer <= 0){
	var _bg = layer_background_get_id("Background");
	if(bg_on == 0){
		layer_background_blend(_bg,#4D4D4D);
		bg_on = 1;
	}else{
		layer_background_blend(_bg,c_black);
		bg_on = 0;
	}
	bg_timer = bg_delay;
}else bg_timer--;