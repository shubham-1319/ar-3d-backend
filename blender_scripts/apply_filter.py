# blender_scripts/apply_filter.py
import bpy  # type: ignore
import sys
import os

# --- Parse CLI arguments ---
image_path = sys.argv[-3]
model_path = sys.argv[-2]
output_path = sys.argv[-1]

# --- Ensure output folder exists ---
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

# --- Clean default scene ---
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- Enable "Import Images as Planes" add-on ---
try:
    bpy.ops.preferences.addon_enable(module="io_import_images_as_planes")
except Exception as e:
    print(f"⚠️ Could not enable 'io_import_images_as_planes': {e}")

# --- Set render engine ---
bpy.context.scene.render.engine = 'CYCLES'  # or 'BLENDER_EEVEE'

# --- Import background image as plane ---
try:
    bpy.ops.import_image.to_plane(files=[{"name": os.path.basename(image_path)}], directory=os.path.dirname(image_path))
    bg = bpy.context.selected_objects[0]
    bg.scale = (4, 4, 4)
except Exception as e:
    print(f"❌ Failed to import background image: {e}")
    sys.exit(1)

# --- Import 3D filter model ---
try:
    bpy.ops.import_scene.gltf(filepath=model_path)
    model = bpy.context.selected_objects[0]
    model.location = (0, 0, 0.1)
except Exception as e:
    print(f"❌ Failed to import 3D model: {e}")
    sys.exit(1)

# --- Set up camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0, -5, 0)
cam_obj.rotation_euler = (1.5708, 0, 0)

# --- Add lighting ---
light_data = bpy.data.lights.new(name="Light", type='POINT')
light = bpy.data.objects.new(name="Light", object_data=light_data)
light.location = (5, -5, 5)
bpy.context.collection.objects.link(light)

# --- Set render output path and format ---
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.image_settings.file_format = 'JPEG'

# --- Render and save ---
try:
    bpy.ops.render.render(write_still=True)
    print(f"✅ Rendered and saved to: {output_path}")
except Exception as e:
    print(f"❌ Render failed: {e}")
    sys.exit(1)
