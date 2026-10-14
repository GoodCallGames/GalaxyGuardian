extends Area3D

@onready var animated_sprite_3d: AnimatedSprite3D = $AnimatedSprite3D
@onready var collision_shape_3d: CollisionShape3D = $CollisionShape3D
@export var speed := 500.0
@export var max_x := 400.0

@export var spin_speed := 14.0

func _physics_process(delta: float) -> void:
	global_position.x += speed * delta
	if speed > 0.0:
		animated_sprite_3d.rotation.x += spin_speed * delta
	if global_position.x > max_x:
		queue_free()


func _on_area_entered(area: Area3D) -> void:
	if area is Enemy:
		area.die()
		speed = 0.0
		collision_shape_3d.set_deferred("disabled", true)
		animated_sprite_3d.play("hit")


func _on_animated_sprite_3d_animation_finished() -> void:
	if animated_sprite_3d.animation == "hit":
		queue_free()
