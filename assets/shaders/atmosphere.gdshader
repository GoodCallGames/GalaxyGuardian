shader_type spatial;
render_mode blend_add, unshaded, cull_back, depth_draw_never;

// Soft rim glow for a slightly oversized shell around a planet.
uniform vec4 glow_color : source_color = vec4(0.4, 0.7, 1.0, 1.0);
uniform float rim_power : hint_range(0.5, 8.0) = 3.0;
uniform float intensity : hint_range(0.0, 6.0) = 1.6;

void fragment() {
	float rim = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0), rim_power);
	ALBEDO = glow_color.rgb * intensity;
	ALPHA = rim;
}
