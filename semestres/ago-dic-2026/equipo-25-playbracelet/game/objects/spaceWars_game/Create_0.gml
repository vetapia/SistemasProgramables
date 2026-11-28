randomise();
sp_delay = 60*6;
sp_repeat = 1.1;
pos_x = 0;
gm_cont = 0;

respawn_timer = 4*60;
respawn_delay = 4*60;
respawn_x = instance_exists(obj_pShip) ? obj_pShip.xstart: 300;
respawn_y = instance_exists(obj_pShip) ? obj_pShip.ystart: 300;

city_hp = 100;
city_hp_max = city_hp;

/*
	0 - Intro
	1 - Main
	2 - Game Over
	3 - Boss
*/

state = 0;
gm_cont = 60*2;