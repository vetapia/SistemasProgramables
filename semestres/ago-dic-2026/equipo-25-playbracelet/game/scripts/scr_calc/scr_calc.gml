///@param {Id.Instance} ins
function instance_get_center(ins){
	if(instance_exists(ins)){
		with(ins){
			var _cenX = bbox_right - ((bbox_right - bbox_left)/2);
			var _cenY = bbox_bottom - ((bbox_bottom - bbox_top)/2);
			
			var _struct = {
				cx: _cenX,
				cy: _cenY
			}
			return _struct;
		}
	}else return -1;
}