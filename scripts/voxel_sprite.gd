class_name VoxelSprite
extends Sprite3D
## Replaces the flat billboard with an extruded 3D model of the current texture.
## The sprite itself stays in the scene (so AnimationPlayer texture/visible tracks
## keep working) but is hidden from the camera.

@export var depth := 8.0

var _model := MeshInstance3D.new()
var _shown_texture: Texture2D

func _ready() -> void:
	layers = 0
	add_child(_model)

func _process(_delta: float) -> void:
	if texture != _shown_texture:
		_shown_texture = texture
		_model.mesh = VoxelMesher.get_mesh(texture, depth) if texture else null
