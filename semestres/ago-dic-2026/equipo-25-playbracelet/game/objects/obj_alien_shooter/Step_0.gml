event_inherited();

y += espeed;
if(estm <= 0){
	instance_create_layer(x,y,"Instances",obj_ebullet);
	estm = estm_rch;
}else estm--;