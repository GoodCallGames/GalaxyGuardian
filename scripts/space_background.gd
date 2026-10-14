extends Node3D
## Scrolling space backdrop built from textured quads at different depths.
## Must match the game camera: centered on the play area, `camera_distance` from z=0.

@export var camera_fov := 40.0
@export var camera_distance := 247.3
@export var play_center := Vector2(160.0, 90.0)
@export var view_height := 180.0
## Quads are oversized so the camera sway never reveals their edges.
@export var oversize := 1.4
@export var width_factor := 1.5 * 16.0 / 9.0

const LAYERS := [
	{"texture": preload("res://assets/textures/background/bg-back.png"), "z": -400.0, "speed": 1.0},
	{"texture": preload("res://assets/textures/background/bg-stars.png"), "z": -250.0, "speed": 4.0},
	{"texture": preload("res://assets/textures/background/bg-planet-double.png"), "z": -120.0, "speed": 50.0},
]

var _materials: Array[StandardMaterial3D] = []
var _rates: Array[float] = []

func _ready() -> void:
	var half_tan := tan(deg_to_rad(camera_fov * 0.5))
	for i in LAYERS.size():
		var layer: Dictionary = LAYERS[i]
		var texture: Texture2D = layer["texture"]
		var z: float = layer["z"]
		var aspect := float(texture.get_width()) / float(texture.get_height())
		var quad_h := 2.0 * (camera_distance - z) * half_tan * oversize
		var quad_w := quad_h * width_factor

		var material := StandardMaterial3D.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		material.albedo_texture = texture
		material.uv1_scale = Vector3(quad_w / (quad_h * aspect), 1.0, 1.0)
		material.render_priority = i - LAYERS.size()

		var mesh := QuadMesh.new()
		mesh.size = Vector2(quad_w, quad_h)

		var instance := MeshInstance3D.new()
		instance.mesh = mesh
		instance.material_override = material
		instance.position = Vector3(play_center.x, play_center.y, z)
		add_child(instance)

		_materials.append(material)
		# Speed is in on-screen pixels/second, like the 2D parallax autoscroll.
		_rates.append(float(layer["speed"]) / (view_height * oversize * aspect))

func _process(delta: float) -> void:
	for i in _materials.size():
		var offset := _materials[i].uv1_offset
		offset.x = fmod(offset.x + _rates[i] * delta, 1.0)
		_materials[i].uv1_offset = offset
