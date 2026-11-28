if(global.keyboard_debug){
	global.inputs = {
		left: keyboard_check(vk_left),
		right: keyboard_check(vk_right),
		up: keyboard_check(vk_up),
		down: keyboard_check(vk_down),
		
		angle: clamp(mouse_wheel_up()-mouse_wheel_down(),0,359)
	}
}else{
	global.inputs = {
		left: 0,
		right: 0,
		up: keyboard_check(vk_up),
		down: keyboard_check(vk_down),
		
		angle: global.giroX
	}
}