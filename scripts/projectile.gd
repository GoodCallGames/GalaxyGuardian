extends Area3D

@export var speed := 500.0
@export var ring_spin := 18.0
@onready var rings: Node3D = find_child("Rings", true, false)
@export var max_x := 450.0

func _physics_process(delta: float) -> void:
	global_position.x += speed * delta
	if rings:
		rings.rotation.x += ring_spin * delta
	if global_position.x > max_x:
		queue_free()


func _on_area_entered(area: Area3D) -> void:
	if area is Enemy:
		area.die()
		Explosion.spawn(get_parent(), global_position, 0.35)
		queue_free()
