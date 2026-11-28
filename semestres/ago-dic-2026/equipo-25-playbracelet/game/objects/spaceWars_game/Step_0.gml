switch(state){
	case 0:
		if(gm_cont <= 0){
			state = 1;	
		}else gm_cont--;
	break;
	case 1:
		if(!audio_is_playing(snd_cityDefend_main)) audio_play_sound(snd_cityDefend_main,1,true);
		if(gm_cont <= 0){
			var _rand = irandom(100);
			var _sp;
	
			if (_rand <= 60) _sp = obj_alien;
			else if(_rand <= 70) _sp = obj_alien_reverse; 
			else if(_rand <= 75)_sp = obj_alien_speedie;
			else if(_rand <= 85)_sp = obj_waver;
			else _sp = obj_alien_shooter;
	
			var _y = _sp == obj_alien_reverse ? room_height + 32: -32;
			repeat(irandom_range(1,int64(sp_repeat))){
				instance_create_layer(irandom_range(48 + 32*6,room_width-(48 + 32*5)),_y,"Instances",_sp);
				if(_sp == obj_alien_speedie) break;
			}
			gm_cont = sp_delay;
			if(sp_delay > 120) sp_delay -= 5;
			if(int64(sp_repeat) < 4) sp_repeat += 0.2;
		}else gm_cont--;
	break;
	default: break;
}

city_hp = clamp(city_hp,0,city_hp_max);