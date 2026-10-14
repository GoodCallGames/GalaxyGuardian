extends Camera3D
## Gently shifts and turns the camera toward the player so the background layers
## move at different rates (the 2.5D parallax effect).

@export var position_follow := 0.08
@export var look_follow := 0.03
@export var smoothing := 5.0
@export var play_center := Vector2(160.0, 90.0)

@onready var target: Node3D = get_node_or_null("../Player")
@onready var base_position := position

func _process(delta: float) -> void:
	if target == null:
		return

	var offset := Vector2(target.global_position.x, target.global_position.y) - play_center
	var weight := 1.0 - exp(-smoothing * delta)

	var wanted_position := base_position + Vector3(offset.x, offset.y, 0.0) * position_follow
	position = position.lerp(wanted_position, weight)

	rotation.y = lerpf(rotation.y, -offset.x / play_center.x * look_follow, weight)
	rotation.x = lerpf(rotation.x, offset.y / play_center.y * look_follow, weight)
