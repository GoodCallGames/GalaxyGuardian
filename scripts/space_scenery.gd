extends Node3D
## Planets, an orbiting moon, asteroids and drifting space debris placed at real
## depths behind the play plane. Planets are dark bodies with a bright atmosphere
## rim, like the game's original 2D backdrop; everything is lit by the scene's sun.

const ATMOSPHERE := preload("res://assets/shaders/atmosphere.gdshader")
const MOON := preload("res://assets/models/moon.glb")
const ROCKS := [
	preload("res://assets/models/asteroid_a.glb"),
	preload("res://assets/models/asteroid_b.glb"),
	preload("res://assets/models/asteroid_c.glb"),
]
const DEBRIS := [
	preload("res://assets/models/debris_satellite.glb"),
	preload("res://assets/models/debris_panel.glb"),
	preload("res://assets/models/debris_pod.glb"),
	preload("res://assets/models/debris_crate.glb"),
	preload("res://assets/models/debris_hull.glb"),
	preload("res://assets/models/debris_shards.glb"),
]

## Each planet: model, radius, atmosphere color, depth, start position, drift speed,
## whether it spins (the ringed planet's tilt must not rotate).
const PLANETS := [
	{"scene": preload("res://assets/models/planet_gas.glb"), "radius": 100.0, "glow": Color(0.62, 0.42, 1.0), "z": -800.0, "pos": Vector2(330.0, 40.0), "speed": 3.0, "spin": true},
	{"scene": preload("res://assets/models/planet_ice.glb"), "radius": 60.0, "glow": Color(0.3, 0.78, 1.0), "z": -450.0, "pos": Vector2(40.0, 165.0), "speed": 4.0, "spin": true},
	{"scene": preload("res://assets/models/planet_ringed.glb"), "radius": 70.0, "glow": Color(0.95, 0.72, 0.42), "z": -1000.0, "pos": Vector2(640.0, 20.0), "speed": 2.5, "spin": false},
	{"scene": preload("res://assets/models/planet_lava.glb"), "radius": 45.0, "glow": Color(1.0, 0.5, 0.18), "z": -600.0, "pos": Vector2(820.0, 150.0), "speed": 5.0, "spin": true},
	{"scene": preload("res://assets/models/planet_green.glb"), "radius": 35.0, "glow": Color(0.35, 0.95, 0.7), "z": -350.0, "pos": Vector2(1000.0, 60.0), "speed": 6.0, "spin": true},
]

@export var camera_distance := 330.0
@export var camera_fov := 30.0
@export var play_center := Vector2(165.0, 88.0)
@export var asteroid_count := 12
@export var debris_count := 12
@export var field_x := Vector2(-140.0, 480.0)
@export var field_y := Vector2(-30.0, 220.0)
@export var field_z := Vector2(-230.0, -30.0)

var _painted_material: StandardMaterial3D
var _planet_material: StandardMaterial3D
var _planets: Array[Node3D] = []
var _moon: Node3D
var _moon_angle := 0.0
var _drifters: Array[Node3D] = []
var _drift_speed: Array[float] = []
var _drift_spin: Array[Vector3] = []
var _rng := RandomNumberGenerator.new()

func _ready() -> void:
	# Everything here moves in _process; interpolation would make it judder.
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	_rng.randomize()
	# Rocks and planets carry per-vertex colors; make the material actually show them.
	_painted_material = StandardMaterial3D.new()
	_painted_material.vertex_color_use_as_albedo = true
	_painted_material.roughness = 0.9
	# Planets are dark bodies; the bright part is the atmosphere rim.
	_planet_material = _painted_material.duplicate()
	_planet_material.albedo_color = Color(0.5, 0.5, 0.56)

	for config in PLANETS:
		_add_planet(config)
	_moon = MOON.instantiate()
	_paint(_moon, _planet_material)
	add_child(_moon)

	for i in asteroid_count:
		_add_drifter(ROCKS.pick_random(), true, _rng.randf_range(0.8, 2.0), 1.0)
	for i in debris_count:
		_add_drifter(DEBRIS.pick_random(), false, _rng.randf_range(0.8, 1.4), 0.35)

func _paint(node: Node, material: StandardMaterial3D = null) -> void:
	if node is MeshInstance3D:
		node.material_override = material if material else _painted_material
	for child in node.get_children():
		_paint(child, material)

func _add_planet(config: Dictionary) -> void:
	var radius: float = config["radius"]
	var planet: Node3D = config["scene"].instantiate()
	planet.position = Vector3(config["pos"].x, config["pos"].y, config["z"])
	planet.set_meta("config", config)
	_paint(planet, _planet_material)
	add_child(planet)

	var shell := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = radius * 1.05
	sphere.height = radius * 2.1
	sphere.radial_segments = 48
	sphere.rings = 24
	var material := ShaderMaterial.new()
	material.shader = ATMOSPHERE
	material.set_shader_parameter("glow_color", config["glow"])
	material.set_shader_parameter("rim_power", 2.4)
	material.set_shader_parameter("intensity", 1.9)
	sphere.material = material
	shell.mesh = sphere
	shell.top_level = true
	shell.set_meta("follows", planet)
	planet.add_child(shell)
	shell.global_position = planet.global_position
	_planets.append(planet)

## Visible half-width of the screen at a given depth behind the play plane.
func _half_width_at(z: float) -> float:
	var distance := camera_distance - z
	return distance * tan(deg_to_rad(camera_fov * 0.5)) * (16.0 / 9.0)

func _add_drifter(scene: PackedScene, painted: bool, scale_factor: float, spin_scale: float) -> void:
	var node: Node3D = scene.instantiate()
	if painted:
		_paint(node)
	add_child(node)
	_place_drifter(node, true)
	node.rotation = Vector3(_rng.randf() * TAU, _rng.randf() * TAU, _rng.randf() * TAU)
	node.scale = Vector3.ONE * scale_factor
	_drifters.append(node)
	_drift_speed.append(_rng.randf_range(10.0, 34.0))
	_drift_spin.append(Vector3(_rng.randf_range(-1.0, 1.0), _rng.randf_range(-1.0, 1.0), _rng.randf_range(-1.0, 1.0)) * spin_scale)

func _place_drifter(node: Node3D, anywhere: bool) -> void:
	var x := _rng.randf_range(field_x.x, field_x.y) if anywhere else field_x.y
	node.position = Vector3(x, _rng.randf_range(field_y.x, field_y.y), _rng.randf_range(field_z.x, field_z.y))

func _process(delta: float) -> void:
	for planet in _planets:
		var config: Dictionary = planet.get_meta("config")
		var radius: float = config["radius"]
		planet.position.x -= float(config["speed"]) * delta
		if config["spin"]:
			planet.rotation.y += 0.03 * delta
		var half_width := _half_width_at(config["z"])
		if planet.position.x < play_center.x - half_width - radius * 2.6:
			planet.position.x = play_center.x + half_width + radius * 2.2 + _rng.randf_range(0.0, 200.0)
			planet.position.y = _rng.randf_range(-20.0, 180.0)
		for child in planet.get_children():
			if child.has_meta("follows"):
				child.global_position = planet.global_position

	# The moon circles the ice planet (the second entry).
	_moon_angle += 0.18 * delta
	var home := _planets[1]
	_moon.position = home.position + Vector3(cos(_moon_angle) * 95.0, sin(_moon_angle * 0.7) * 20.0, sin(_moon_angle) * 95.0)
	_moon.rotation.y += 0.1 * delta

	for i in _drifters.size():
		var node := _drifters[i]
		node.position.x -= _drift_speed[i] * delta
		node.rotation += _drift_spin[i] * delta
		if node.position.x < field_x.x:
			_place_drifter(node, false)
