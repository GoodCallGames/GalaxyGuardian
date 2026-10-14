extends CharacterBody2D
class_name Player

signal shoot_projectile
signal died

@onready var main_ap: AnimationPlayer = $Main_AP
@onready var flash_ap: AnimationPlayer = $Flash_AP
@onready var muzzle: Marker2D = $Muzzle
@onready var player_ship: Sprite2D = $PlayerShip
@onready var player_ship_collision: CollisionShape2D = $PlayerShipCollision
@onready var invincibility_timer: Timer = $InvincibilityTimer
@onready var laser_sound: AudioStreamPlayer = $LaserSound

const laser_sounds := [preload("res://assets/audio/shot 1.wav"), preload("res://assets/audio/shot 2.wav")]

@export var speed := 120.0
var is_alive: bool = true
var is_invincible: bool = false

func _process(_delta: float) -> void:
	if !is_alive:
		return
	
	if Input.is_action_just_pressed("shoot"):
		flash_ap.play("shoot_laser")

func _physics_process(_delta: float) -> void:
	if !is_alive:
		return
	
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = speed * direction
	move_and_slide()

	var viewport_rect := get_viewport_rect()
	global_position = global_position.clamp(viewport_rect.position, viewport_rect.end)

	if direction.y < 0.0:
		main_ap.play("up")
	elif direction.y > 0.0:
		main_ap.play("down")
	else:
		main_ap.play("default")
		
func shoot() -> void:
	shoot_projectile.emit()
	play_laser_sound()
	
func die() -> void:
	if is_invincible:
		return
	
	died.emit()
	is_alive = false
	main_ap.play("explode")

func respawn(spawn_position: Vector2) -> void:
	global_position = spawn_position
	reset_physics_interpolation()
	is_alive = true
	player_ship.visible = true
	
	is_invincible = true
	invincibility_timer.start()


func _on_invincibility_timer_timeout() -> void:
	player_ship_collision.set_deferred("disabled", false)
	is_invincible = false

func play_laser_sound():
	var sound_to_play = laser_sounds.pick_random()
	laser_sound.stream = sound_to_play
	laser_sound.play()
