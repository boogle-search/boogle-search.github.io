extends Button


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	DisplayServer # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _pressed():
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
