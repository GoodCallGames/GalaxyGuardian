extends Area3D
class_name Enemy

signal died

@onready var model: Node3D = $Model

@export var speed: float = 100.0
@export var tumble_speed := 1.6

var _phase := randf() * TAU
var _age := 0.0
var _dead := false

func _ready() -> void:
	# The model sways in _process, so it opts out of physics interpolation.
	model.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF

func _process(delta: float) -> void:
	# Slow wobble so the 3D model catches the light from different angles.
	_age += delta
	model.rotation.x = sin(_age * tumble_speed + _phase) * 0.28
	model.rotation.y = cos(_age * tumble_speed * 0.7 + _phase) * 0.07
	model.rotation.z = sin(_age * tumble_speed * 0.5 + _phase) * 0.04

func _physics_process(delta: float) -> void:
	global_position.x -= speed * delta

func die() -> void:
	if _dead:
		return
	_dead = true
	died.emit()
	Explosion.spawn(get_parent(), global_position, 1.0)
	queue_free()


func _on_body_entered(body: Node3D) -> void:
	if body is Player:
		die()
		body.die()
