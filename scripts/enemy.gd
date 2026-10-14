extends Area3D
class_name Enemy

signal died

@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var enemy_sprite: Node3D = $EnemySprite

@export var speed: float = 100.0
@export var tumble_speed := 2.0

var _phase := randf() * TAU
var _age := 0.0

func _process(delta: float) -> void:
	# Slow wobble while alive so the extruded model shows its thickness.
	if speed > 0.0:
		_age += delta
		enemy_sprite.rotation.y = sin(_age * tumble_speed + _phase) * 0.7
		enemy_sprite.rotation.x = cos(_age * tumble_speed * 0.7 + _phase) * 0.35
	else:
		enemy_sprite.rotation = Vector3.ZERO

func _physics_process(delta: float) -> void:
	global_position.x -= speed * delta

func die() -> void:
	died.emit()
	animation_player.play("explode")


func _on_body_entered(body: Node3D) -> void:
	if body is Player:
		die()
		body.die()
