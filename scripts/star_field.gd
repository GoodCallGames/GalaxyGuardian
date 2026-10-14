extends MultiMeshInstance3D
## Stars drifting past at many depths. Near stars sweep by faster on screen than
## far ones, which is what sells the perspective.

@export var count := 220
@export var speed := 60.0
@export var x_range := Vector2(-140.0, 480.0)
@export var y_range := Vector2(-80.0, 260.0)
@export var z_range := Vector2(-320.0, 110.0)

var _positions := PackedVector3Array()
var _speeds := PackedFloat32Array()

func _ready() -> void:
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 1.0)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	material.vertex_color_use_as_albedo = true
	quad.material = material

	multimesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	multimesh.mesh = quad
	multimesh.instance_count = count

	var rng := RandomNumberGenerator.new()
	rng.randomize()
	for i in count:
		_positions.append(Vector3(
			rng.randf_range(x_range.x, x_range.y),
			rng.randf_range(y_range.x, y_range.y),
			rng.randf_range(z_range.x, z_range.y)))
		_speeds.append(speed * rng.randf_range(0.8, 1.2))
		var tint := rng.randf()
		multimesh.set_instance_color(i, Color(0.75, 0.6, 1.0).lerp(Color.WHITE, tint))
		var star_size := rng.randf_range(0.8, 2.2)
		multimesh.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ONE * star_size), _positions[i]))

func _process(delta: float) -> void:
	var span := x_range.y - x_range.x
	for i in count:
		var p := _positions[i]
		p.x -= _speeds[i] * delta
		if p.x < x_range.x:
			p.x += span
		_positions[i] = p
		var t := multimesh.get_instance_transform(i)
		t.origin = p
		multimesh.set_instance_transform(i, t)
