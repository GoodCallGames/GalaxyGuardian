extends Camera3D
## Chase-style camera held at an angle to the play plane, drifting with the player
## so near and far objects shift at different rates (the 2.5D parallax effect).

@export var look_target := Vector3(165.0, 85.0, 0.0)
@export var position_follow := 0.02
@export var look_follow := 0.03
@export var smoothing := 5.0
@export var play_center := Vector2(160.0, 90.0)

@onready var target: Node3D = get_node_or_null("../Player")
@onready var base_position := position
var _offset := Vector2.ZERO

func _ready() -> void:
	look_at_from_position(base_position, look_target)

func _process(delta: float) -> void:
	if target == null:
		return

	var wanted := Vector2(target.global_position.x, target.global_position.y) - play_center
	_offset = _offset.lerp(wanted, 1.0 - exp(-smoothing * delta))

	var cam_pos := base_position + Vector3(_offset.x, _offset.y, 0.0) * position_follow
	var cam_look := look_target + Vector3(_offset.x, _offset.y, 0.0) * look_follow
	look_at_from_position(cam_pos, cam_look)

## Pulls a point on the z=0 play plane back inside the screen. `margin` is half the
## sprite size in world units, so the whole sprite stays visible. Done in screen space,
## so it is exact for any camera angle, however skewed the visible area is.
func clamp_to_screen(world_pos: Vector3, margin := Vector2.ZERO) -> Vector3:
	var size := get_viewport().get_visible_rect().size
	var distance := global_position.distance_to(world_pos)
	var pixels_per_unit := size.y / (2.0 * distance * tan(deg_to_rad(fov * 0.5)))
	var inset := margin * pixels_per_unit
	var on_screen := unproject_position(world_pos)
	var clamped := Vector2(
		clampf(on_screen.x, inset.x, size.x - inset.x),
		clampf(on_screen.y, inset.y, size.y - inset.y))
	if clamped.is_equal_approx(on_screen):
		return world_pos
	var hit: Variant = Plane(Vector3.BACK, 0.0).intersects_ray(
		project_ray_origin(clamped), project_ray_normal(clamped))
	return world_pos if hit == null else hit

## The point on the z=0 play plane under a screen position given as a fraction of the
## viewport (0..1 spans the screen; values outside it are off-screen).
func screen_to_plane(fraction: Vector2) -> Vector3:
	var point := fraction * get_viewport().get_visible_rect().size
	var hit: Variant = Plane(Vector3.BACK, 0.0).intersects_ray(
		project_ray_origin(point), project_ray_normal(point))
	return Vector3.ZERO if hit == null else hit

## Where the screen edges meet the play plane with the camera at rest. Used to place
## enemy spawn and despawn lines; `margin` shrinks the area.
func get_play_bounds(margin := Vector2.ZERO) -> Rect2:
	var rect := _visible_rect_for(Vector2.ZERO)
	return Rect2(rect.position + margin, rect.size - margin * 2.0)

## Largest on-screen rectangle on the z=0 plane for a camera that has drifted by `offset`.
func _visible_rect_for(offset: Vector2) -> Rect2:
	var shift := Vector3(offset.x, offset.y, 0.0)
	var cam_pos := base_position + shift * position_follow
	var cam_look := look_target + shift * look_follow
	var xform := Transform3D(Basis(), cam_pos).looking_at(cam_look, Vector3.UP)
	var size := get_viewport().get_visible_rect().size
	var half_tan := tan(deg_to_rad(fov * 0.5))
	var left := -INF
	var right := INF
	var bottom := -INF
	var top := INF
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			var dir := xform.basis * Vector3(sx * half_tan * size.x / size.y, sy * half_tan, -1.0)
			var hit: Variant = Plane(Vector3.BACK, 0.0).intersects_ray(cam_pos, dir.normalized())
			if hit == null:
				continue
			var point: Vector3 = hit
			if sx < 0.0:
				left = maxf(left, point.x)
			else:
				right = minf(right, point.x)
			if sy < 0.0:
				bottom = maxf(bottom, point.y)
			else:
				top = minf(top, point.y)
	return Rect2(left, bottom, right - left, top - bottom)
