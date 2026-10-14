extends Control

@onready var score_label: Label = $Score
@onready var lives_left: Label = $LivesLeft

func _set_score_label(new_score: int) -> void:
	score_label.text = "SCORE: %d" % new_score
	
func _set_lives_left_label(lives: int) -> void:
	lives_left.text = str(lives)
