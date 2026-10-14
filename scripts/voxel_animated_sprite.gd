class_name VoxelAnimatedSprite
extends AnimatedSprite3D
## AnimatedSprite3D variant of VoxelSprite: extrudes whichever frame is showing.

@export var depth := 4.0

var _model := MeshInstance3D.new()
var _shown_texture: Texture2D

func _ready() -> void:
	layers = 0
	add_child(_model)

func _process(_delta: float) -> void:
	var current: Texture2D = null
	if sprite_frames and sprite_frames.has_animation(animation):
		current = sprite_frames.get_frame_texture(animation, frame)
	if current != _shown_texture:
		_shown_texture = current
		_model.mesh = VoxelMesher.get_mesh(current, depth) if current else null
