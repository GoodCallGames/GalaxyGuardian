extends WorldEnvironment
## Slowly turns the nebula sky so the backdrop drifts past.

@export var turn_speed := 0.012

func _process(delta: float) -> void:
	var rotation_now := environment.sky_rotation
	rotation_now.y += turn_speed * delta
	environment.sky_rotation = rotation_now
