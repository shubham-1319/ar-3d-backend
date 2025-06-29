# blender_scripts/apply_filter.py
import bpy # type: ignore
import sys
import os

# Args from CLI
image_path = sys.argv[-3]
model_path = sys.argv[-2]
output_path = sys.argv[-1]

# Clean up existing scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Set up background image
bpy.ops.import_image.to_plane(files=[{"name": os.path.basename(image_path)}], directory=os.path.dirname(image_path))
bg = bpy.context.selected_objects[0]
bg.scale = (4, 4, 4)  # adjust as needed

# Import 3D model
bpy.ops.import_scene.gltf(filepath=model_path)
model = bpy.context.selected_objects[0]
model.location = (0, 0, 0.1)

# Adjust camera/light if needed...

# Set render settings
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.image_settings.file_format = 'JPEG'

bpy.ops.render.render(write_still=True)
