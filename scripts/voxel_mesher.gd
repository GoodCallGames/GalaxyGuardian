class_name VoxelMesher
## Extrudes a pixel-art texture into a lit 3D mesh: one box per opaque pixel
## (1 pixel = 1 world unit), centered on the origin like a centered Sprite3D.

static var _mesh_cache := {}
static var _material: StandardMaterial3D

static func get_material() -> StandardMaterial3D:
	if _material == null:
		_material = StandardMaterial3D.new()
		_material.vertex_color_use_as_albedo = true
		_material.vertex_color_is_srgb = true
		_material.roughness = 0.85
		_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	return _material

static func get_mesh(texture: Texture2D, depth: float) -> ArrayMesh:
	var key := [texture.get_rid(), depth]
	if _mesh_cache.has(key):
		return _mesh_cache[key]
	var mesh := _build(texture.get_image(), depth)
	_mesh_cache[key] = mesh
	return mesh

static func _build(image: Image, depth: float) -> ArrayMesh:
	var width := image.get_width()
	var height := image.get_height()
	var z1 := depth * 0.5
	var z0 := -z1
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)

	for py in height:
		for px in width:
			var color := image.get_pixel(px, py)
			if color.a < 0.5:
				continue
			color.a = 1.0
			var x0 := float(px) - width * 0.5
			var x1 := x0 + 1.0
			var y1 := height * 0.5 - float(py)
			var y0 := y1 - 1.0

			# Corners of each face are counter-clockwise seen from outside.
			_quad(st, color, Vector3.BACK,
				Vector3(x0, y0, z1), Vector3(x1, y0, z1), Vector3(x1, y1, z1), Vector3(x0, y1, z1))
			_quad(st, color, Vector3.FORWARD,
				Vector3(x1, y0, z0), Vector3(x0, y0, z0), Vector3(x0, y1, z0), Vector3(x1, y1, z0))
			if _is_empty(image, px + 1, py):
				_quad(st, color, Vector3.RIGHT,
					Vector3(x1, y0, z1), Vector3(x1, y0, z0), Vector3(x1, y1, z0), Vector3(x1, y1, z1))
			if _is_empty(image, px - 1, py):
				_quad(st, color, Vector3.LEFT,
					Vector3(x0, y0, z0), Vector3(x0, y0, z1), Vector3(x0, y1, z1), Vector3(x0, y1, z0))
			if _is_empty(image, px, py - 1):
				_quad(st, color, Vector3.UP,
					Vector3(x0, y1, z1), Vector3(x1, y1, z1), Vector3(x1, y1, z0), Vector3(x0, y1, z0))
			if _is_empty(image, px, py + 1):
				_quad(st, color, Vector3.DOWN,
					Vector3(x0, y0, z0), Vector3(x1, y0, z0), Vector3(x1, y0, z1), Vector3(x0, y0, z1))

	var mesh := st.commit()
	mesh.surface_set_material(0, get_material())
	return mesh

static func _is_empty(image: Image, px: int, py: int) -> bool:
	if px < 0 or py < 0 or px >= image.get_width() or py >= image.get_height():
		return true
	return image.get_pixel(px, py).a < 0.5

static func _quad(st: SurfaceTool, color: Color, normal: Vector3,
		p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3) -> void:
	# Godot treats clockwise triangles as front-facing.
	for p in [p0, p2, p1, p0, p3, p2]:
		st.set_color(color)
		st.set_normal(normal)
		st.add_vertex(p)
