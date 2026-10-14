extends Node2D

@onready var player: Player = $Player
@onready var respawn_timer: Timer = $RespawnTimer
@onready var player_spawn: Marker2D = $PlayerSpawn
@onready var hud: Control = $UILayer/HUD
@onready var ui_layer: CanvasLayer = $UILayer
@onready var explosion_sound: AudioStreamPlayer = $ExplosionSound

const projectile_scene: PackedScene = preload("res://scenes/projectile.tscn")
const game_over_screen_scene: PackedScene = preload("res://scenes/game_over_screen.tscn")

@export var game_over_delay: float = 1.5
@export var lives: int = 3
var score: int = 0

func _ready() -> void:
	hud._set_lives_left_label(lives)
	hud._set_score_label(score)
	
	player.shoot_projectile.connect(_on_player_shoot_projectile)
	player.died.connect(_on_player_died)
	
func _on_player_shoot_projectile() -> void:
	var projectile_instance = projectile_scene.instantiate()
	projectile_instance.global_position = player.muzzle.global_position
	
	add_child(projectile_instance)


func _on_enemy_spawner_enemy_spawned(enemy: Enemy) -> void:
	enemy.died.connect(_on_enemy_died)
	add_child(enemy)


func _on_area_2d_area_entered(area: Area2D) -> void:
	if area is Enemy:
		area.queue_free()

func _on_player_died() -> void:
	explosion_sound.play()
	lives -= 1
	hud._set_lives_left_label(lives)
	
	if lives > 0:
		respawn_timer.start()
	else:
		await get_tree().create_timer(game_over_delay).timeout
		
		var game_over_screen = game_over_screen_scene.instantiate()
		ui_layer.add_child(game_over_screen)
		

func _on_enemy_died() -> void:
	explosion_sound.play()
	score += 100
	hud._set_score_label(score)

func _on_respawn_timer_timeout() -> void:
	player.respawn(player_spawn.global_position)
