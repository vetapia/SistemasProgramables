var _name = object_get_name(id.object_index);
if(_name != "obj_alien_reverse" && instance_exists(spaceWars_game)){
	spaceWars_game.city_hp -= dmg;
	damage_city(dmg);
	instance_destroy();
}