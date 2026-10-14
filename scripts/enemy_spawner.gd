extends Node3D

signal enemy_spawned(instance: Node)

const enemy_scene: PackedScene = preload("res://scenes/enemy.tscn")

@export var difficulty_increase := 0.25
@export var minimum_difficulty := 0.25

@onready var spawn_positions: Node3D = $SpawnPositions
@onready var spawn_timer: Timer = $SpawnTimer

func _on_spawn_timer_timeout() -> void:
	spawn_enemy()


func spawn_enemy() -> void:
	var enemy_instance := enemy_scene.instantiate()
	var spawn_point: Marker3D = spawn_positions.get_children().pick_random()

	# Not in the tree yet, so set the local position; Game sits at the origin.
	enemy_instance.position = spawn_point.global_position
	enemy_spawned.emit(enemy_instance)


func _on_difficulty_timer_timeout() -> void:
	if spawn_timer.wait_time > minimum_difficulty:
		spawn_timer.wait_time -= difficulty_increase
