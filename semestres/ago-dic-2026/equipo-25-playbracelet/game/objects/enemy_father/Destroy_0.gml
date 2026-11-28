if(defeated){
	grant_points(points);
}
var _cen = instance_get_center(id);
instance_create_layer(_cen.cx,_cen.cy,"Instances",obj_explosion);