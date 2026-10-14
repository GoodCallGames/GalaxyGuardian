extends Node3D
## Space backdrop. The nebula and star textures are huge quads far behind the play
## plane; the planets are real world objects at their own depths that drift past.
## Camera numbers must match the game camera.

@export var camera_fov := 45.0
@export var camera_distance := 240.0
@export var play_center := Vector2(160.0, 90.0)
@export var view_height := 180.0
## Far quads are oversized so camera movement never reveals their edges.
@export var oversize := 2.8
@export var width_factor := 2.0 * 16.0 / 9.0

const LAYERS := [
	{"texture": preload("res://assets/textures/background/bg-back.png"), "z": -450.0, "speed": 1.0},
	{"texture": preload("res://assets/textures/background/bg-stars.png"), "z": -380.0, "speed": 4.0},
]

const PLANETS := [
	{"texture": preload("res://assets/textures/background/bg-planet-double.png"), "z": -170.0, "y": 70.0, "scale": 1.1, "speed": 14.0},
	{"texture": preload("res://assets/textures/background/bg-planet.png"), "z": -300.0, "y": 130.0, "scale": 1.5, "speed": 14.0},
]

var _materials: Array[StandardMaterial3D] = []
var _rates: Array[float] = []
var _planet_nodes: Array[MeshInstance3D] = []
var _planet_widths: Array[float] = []

func _ready() -> void:
	var half_tan := tan(deg_to_rad(camera_fov * 0.5))
	for i in LAYERS.size():
		var layer: Dictionary = LAYERS[i]
		var texture: Texture2D = layer["texture"]
		var z: float = layer["z"]
		var aspect := float(texture.get_width()) / float(texture.get_height())
		var quad_h := 2.0 * (camera_distance - z) * half_tan * oversize
		var quad_w := quad_h * width_factor

		var material := _make_material(texture, i - 10)
		material.uv1_scale = Vector3(quad_w / (quad_h * aspect), 1.0, 1.0)
		_add_quad(Vector2(quad_w, quad_h), Vector3(play_center.x, play_center.y, z), material)

		_materials.append(material)
		# Speed is in on-screen pixels/second, like the 2D parallax autoscroll.
		_rates.append(float(layer["speed"]) / (view_height * oversize * aspect))

	for i in PLANETS.size():
		var planet: Dictionary = PLANETS[i]
		var texture: Texture2D = planet["texture"]
		var size := Vector2(texture.get_width(), texture.get_height()) * float(planet["scale"])
		var material := _make_material(texture, i, true)
		# Two copies side by side so the planet strip loops seamlessly.
		for copy in 2:
			var node := _add_quad(size, Vector3(play_center.x + size.x * copy, float(planet["y"]), float(planet["z"])), material)
			node.set_meta("planet", i)
			_planet_nodes.append(node)
		_planet_widths.append(size.x)

func _make_material(texture: Texture2D, priority: int, additive := false) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	material.albedo_texture = texture
	material.render_priority = priority
	if additive:
		# The planet art has an opaque dark backdrop; adding it makes the dark vanish.
		material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	return material

func _add_quad(size: Vector2, at: Vector3, material: Material) -> MeshInstance3D:
	var mesh := QuadMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = material
	instance.position = at
	add_child(instance)
	return instance

func _process(delta: float) -> void:
	for i in _materials.size():
		var offset := _materials[i].uv1_offset
		offset.x = fmod(offset.x + _rates[i] * delta, 1.0)
		_materials[i].uv1_offset = offset

	for node in _planet_nodes:
		var index: int = node.get_meta("planet")
		var width := _planet_widths[index]
		node.position.x -= float(PLANETS[index]["speed"]) * delta
		if node.position.x < play_center.x - width * 1.5:
			node.position.x += width * 2.0
