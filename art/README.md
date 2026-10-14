# Art source

Blender 5.x Python scripts that generate the 3D models and textures in `assets/`.
Run any of them headless, e.g.

    blender -b -P art/build_player.py

| Script | Output |
| --- | --- |
| `build_player.py` | `assets/models/player_ship.glb` (from the pink/cyan reference) |
| `build_enemy.py` | `assets/models/enemy.glb` (from the indigo stealth-fighter sheet) |
| `build_laser.py` | `assets/models/laser.glb` (plasma lance; the `Rings` node is spun in Godot) |
| `build_space.py` | planets, moon, asteroids |
| `build_debris.py` | satellite, solar panel, escape pod, cargo container, hull chunk, crystal shards |
| `build_sky.py` | `assets/textures/sky/nebula.jpg` (equirect panorama) |

`blender_common.py` and `detail.py` hold the shared modelling, procedural-material
and texture-baking helpers. Previews and bake caches are written to `art/previews/`
and `art/bake_cache/` (git-ignored).
