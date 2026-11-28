var _cen = instance_get_center(id);
instance_create_layer(_cen.cx,_cen.cy,"Instances",obj_explosion);

var _txt = layer_text_get_id("UIBoard","txt_death");
var _n = int64(layer_text_get_text(_txt)) + 1;

layer_text_text(_txt,_n);