extends CharacterBody3D

# Movement settings
@export var speed: float = 10.0
@export var acceleration: float = 5.0
@export var gravity: float = 25.0
@export var jump_velocity: float = 12.0

# Mobile Touch Look settings (For dragging the screen to look around)
@export var touch_sensitivity: float = 0.005

# Node references
@onready var pivot: Node3D = $CamPivot
@onready var camera: Camera3D = $CamPivot/Camera3D

func _ready() -> void:
	# Keep mouse visible so it works nicely with mobile/touch inputs
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func _unhandled_input(event: InputEvent) -> void:
	# Handle mobile screen drag for looking around
	if event is InputEventScreenDrag:
		# Only look around if dragging on the right half of the screen
		# (This leaves the left half open for the movement joystick)
		if event.position.x > get_viewport().size.x / 2:
			# Rotate character horizontally (Y-axis)
			rotate_y(-event.relative.x * touch_sensitivity)
			# Rotate camera vertically (X-axis)
			pivot.rotate_x(-event.relative.y * touch_sensitivity)
			# Limit camera pitch so player can't look upside down
			pivot.rotation.x = clamp(pivot.rotation.x, deg_to_rad(-80), deg_to_rad(80))

func _physics_process(delta: float) -> void:
	# Apply gravity over time if not on the floor
	if not is_on_floor():
		velocity.y -= gravity * delta

	# Handle Jump using the default UI accept action (usually Spacebar/Enter)
	if Input.is_action_just_pressed("ui_accept") and is_on_floor():
		velocity.y = jump_velocity

	# Get the input direction using Godot's default UI keys (matches your joystick!)
	var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	
	# Calculate move direction based on camera facing direction
	var direction := Vector3(input_dir.x, 0, input_dir.y)

	if direction != Vector3.ZERO:
		direction = direction.normalized()
		direction = transform.basis * direction
	
	# Smooth out horizontal movement using linear interpolation
	if direction != Vector3.ZERO:
		velocity.x = move_toward(velocity.x, direction.x * speed, speed * acceleration * delta)
		velocity.z = move_toward(velocity.z, direction.z * speed, speed * acceleration * delta)
	else:
		velocity.x = move_toward(velocity.x, 0, speed * acceleration * delta)
		velocity.z = move_toward(velocity.z, 0, speed * acceleration * delta)

	# Execute built-in character movement
	move_and_slide()

# You can also trigger this jump function manually from a screen button's signal
func mobile_jump() -> void:
	if is_on_floor():
		velocity.y = jump_velocity
