extends CharacterBody3D
class_name Player

signal shoot_projectile
signal died

@onready var main_ap: AnimationPlayer = $Main_AP
@onready var flash_ap: AnimationPlayer = $Flash_AP
@onready var muzzle: Marker3D = $Muzzle
@onready var player_ship: Sprite3D = $PlayerShip
@onready var player_ship_collision: CollisionShape3D = $PlayerShipCollision
@onready var invincibility_timer: Timer = $InvincibilityTimer
@onready var laser_sound: AudioStreamPlayer = $LaserSound

const laser_sounds := [preload("res://assets/audio/shot 1.wav"), preload("res://assets/audio/shot 2.wav")]

@export var speed := 120.0
## Fallback bounds, used only if there is no camera to clamp against.
@export var play_area := Rect2(0.0, 0.0, 320.0, 180.0)
## Keeps the whole ship on screen: roughly half the sprite size.
@export var edge_margin := Vector2(20.0, 15.0)
@export var bank_angle := 0.4
@export var bank_smoothing := 8.0
var is_alive: bool = true
var is_invincible: bool = false

func _process(_delta: float) -> void:
	if !is_alive:
		return

	if Input.is_action_just_pressed("shoot"):
		flash_ap.play("shoot_laser")

func _physics_process(delta: float) -> void:
	if !is_alive:
		return

	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	# Screen-space input: up is -y, but world up is +y.
	velocity = Vector3(direction.x, -direction.y, 0.0) * speed
	move_and_slide()

	var camera := get_viewport().get_camera_3d()
	if camera and camera.has_method("clamp_to_screen"):
		global_position = camera.clamp_to_screen(global_position, edge_margin)
	else:
		global_position.x = clampf(global_position.x, play_area.position.x, play_area.end.x)
		global_position.y = clampf(global_position.y, play_area.position.y, play_area.end.y)
	global_position.z = 0.0

	# Pitch, roll and yaw the 3D ship model into the movement.
	var weight := 1.0 - exp(-bank_smoothing * delta)
	player_ship.rotation.z = lerpf(player_ship.rotation.z, -direction.y * bank_angle * 0.75, weight)
	player_ship.rotation.x = lerpf(player_ship.rotation.x, -direction.y * bank_angle * 1.5, weight)
	player_ship.rotation.y = lerpf(player_ship.rotation.y, -direction.x * bank_angle, weight)

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

func respawn(spawn_position: Vector3) -> void:
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
