extends Area3D
class_name Enemy

signal died

@onready var animation_player: AnimationPlayer = $AnimationPlayer

@export var speed: float = 100.0

func _physics_process(delta: float) -> void:
	global_position.x -= speed * delta

func die() -> void:
	died.emit()
	animation_player.play("explode")


func _on_body_entered(body: Node3D) -> void:
	if body is Player:
		die()
		body.die()
