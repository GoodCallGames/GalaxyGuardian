class_name Explosion
extends Node3D
## One-shot fireball, sparks and light flash, built in code. Spawned into the game
## world (not onto the thing that exploded) so it outlives it.

@export var size := 1.0

static func spawn(parent: Node, at: Vector3, explosion_size := 1.0) -> void:
	var explosion := Explosion.new()
	explosion.size = explosion_size
	parent.add_child(explosion)
	explosion.global_position = at

func _ready() -> void:
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	add_child(_make_fireball())
	add_child(_make_sparks())
	add_child(_make_light())
	get_tree().create_timer(1.6).timeout.connect(queue_free)

func _particle_material() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.vertex_color_use_as_albedo = true
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	return material

func _sphere(radius: float) -> SphereMesh:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh.radial_segments = 8
	mesh.rings = 4
	mesh.material = _particle_material()
	return mesh

func _make_fireball() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 26
	p.lifetime = 0.75
	p.one_shot = true
	p.explosiveness = 1.0
	p.emitting = true
	p.local_coords = false
	p.mesh = _sphere(0.5)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 2.0 * size
	p.direction = Vector3.UP
	p.spread = 180.0
	p.gravity = Vector3.ZERO
	p.initial_velocity_min = 8.0 * size
	p.initial_velocity_max = 32.0 * size
	p.damping_min = 25.0
	p.damping_max = 40.0
	p.scale_amount_min = 4.0 * size
	p.scale_amount_max = 8.5 * size
	var scale_curve := Curve.new()
	scale_curve.add_point(Vector2(0.0, 0.35))
	scale_curve.add_point(Vector2(0.25, 1.0))
	scale_curve.add_point(Vector2(1.0, 0.0))
	p.scale_amount_curve = scale_curve
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.25, 0.6, 1.0])
	ramp.colors = PackedColorArray([
		Color(1.0, 0.95, 0.75, 1.0), Color(1.0, 0.6, 0.15, 0.95),
		Color(0.8, 0.2, 0.05, 0.6), Color(0.15, 0.03, 0.02, 0.0)])
	p.color_ramp = ramp
	return p

func _make_sparks() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 22
	p.lifetime = 0.9
	p.one_shot = true
	p.explosiveness = 1.0
	p.emitting = true
	p.local_coords = false
	p.mesh = _sphere(0.5)
	p.direction = Vector3.UP
	p.spread = 180.0
	p.gravity = Vector3.ZERO
	p.initial_velocity_min = 40.0 * size
	p.initial_velocity_max = 110.0 * size
	p.damping_min = 20.0
	p.damping_max = 45.0
	p.scale_amount_min = 0.7 * size
	p.scale_amount_max = 1.5 * size
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
	ramp.colors = PackedColorArray([
		Color(1.0, 1.0, 0.85, 1.0), Color(1.0, 0.65, 0.2, 0.9), Color(0.9, 0.2, 0.05, 0.0)])
	p.color_ramp = ramp
	return p

func _make_light() -> OmniLight3D:
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.65, 0.3)
	light.light_energy = 6.0 * size
	light.omni_range = 70.0 * size
	var tween := create_tween()
	tween.tween_property(light, "light_energy", 0.0, 0.45)
	return light
