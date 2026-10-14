extends Node3D

signal enemy_spawned(instance: Node)

const enemy_scene: PackedScene = preload("res://scenes/enemy.tscn")

@export var difficulty_increase := 0.25
@export var minimum_difficulty := 0.25
## Where enemies appear, as fractions of the screen (x > 1 is past the right edge).
@export var spawn_screen_x := 1.07
@export var row_top := 0.1
@export var row_bottom := 0.9

@onready var spawn_positions: Node3D = $SpawnPositions
@onready var spawn_timer: Timer = $SpawnTimer

func _on_spawn_timer_timeout() -> void:
	spawn_enemy()


func spawn_enemy() -> void:
	var enemy_instance := enemy_scene.instantiate()
	var rows := spawn_positions.get_children()
	var row := randi() % rows.size()
	var spawn_point: Vector3 = rows[row].global_position

	# Rows span the screen height, just past its right edge, whatever the camera angle.
	var camera := get_viewport().get_camera_3d()
	if camera and camera.has_method("screen_to_plane"):
		var row_fraction := lerpf(row_top, row_bottom, float(row) / maxf(rows.size() - 1, 1.0))
		spawn_point = camera.screen_to_plane(Vector2(spawn_screen_x, row_fraction))

	# Not in the tree yet, so set the local position; Game sits at the origin.
	enemy_instance.position = spawn_point
	enemy_spawned.emit(enemy_instance)


func _on_difficulty_timer_timeout() -> void:
	if spawn_timer.wait_time > minimum_difficulty:
		spawn_timer.wait_time -= difficulty_increase
