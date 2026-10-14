extends Camera3D
## Chase-style camera held at an angle to the play plane, drifting with the player
## so near and far objects shift at different rates (the 2.5D parallax effect).

@export var look_target := Vector3(165.0, 85.0, 0.0)
@export var position_follow := 0.12
@export var look_follow := 0.35
@export var smoothing := 5.0
@export var play_center := Vector2(160.0, 90.0)

@onready var target: Node3D = get_node_or_null("../Player")
@onready var base_position := position
var _offset := Vector2.ZERO

func _ready() -> void:
	look_at_from_position(base_position, look_target)

func _process(delta: float) -> void:
	if target == null:
		return

	var wanted := Vector2(target.global_position.x, target.global_position.y) - play_center
	_offset = _offset.lerp(wanted, 1.0 - exp(-smoothing * delta))

	var cam_pos := base_position + Vector3(_offset.x, _offset.y, 0.0) * position_follow
	var cam_look := look_target + Vector3(_offset.x, _offset.y, 0.0) * look_follow
	look_at_from_position(cam_pos, cam_look)
