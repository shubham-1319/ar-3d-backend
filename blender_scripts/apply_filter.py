# blender_scripts/apply_filter.py
import bpy # type: ignore
import sys
import os
import math # For math.radians

# --- Argument Parsing ---
# It's safer to parse arguments explicitly rather than relying on fixed indices.
# When Blender runs a script with `blender -b --python script.py -- [args]`,
# the custom arguments come after the `--`.
try:
    # Arguments passed after '--' in the command line
    # Example: blender -b --python apply_filter.py -- image.jpg model.gltf output.jpg
    # sys.argv will look something like: ['blender', '-b', '--python', 'apply_filter.py', '--', 'image.jpg', 'model.gltf', 'output.jpg']
    # We need to find the index of '--'
    args_start_index = sys.argv.index("--") + 1
    image_path = os.path.abspath(sys.argv[args_start_index])
    model_path = os.path.abspath(sys.argv[args_start_index + 1])
    output_path = os.path.abspath(sys.argv[args_start_index + 2])
except (ValueError, IndexError):
    print("Error: Incorrect number of arguments or arguments not properly passed after '--'.")
    print("Usage: blender -b --python apply_filter.py -- <image_path> <model_path> <output_path>")
    sys.exit(1)

# Safety check
if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image not found: {image_path}")
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model not found: {model_path}")

# Ensure output directory exists
output_dir = os.path.dirname(output_path)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Clear the scene
# This removes all objects, meshes, materials, etc., ensuring a clean slate.
bpy.ops.wm.read_factory_settings(use_empty=True)

# Set render engine
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.device = 'CPU' # Or 'GPU' if available and preferred
# You might want to set other Cycles settings for quality/speed (e.g., samples, denoiser)
bpy.context.scene.cycles.samples = 128 # A reasonable default for many cases
bpy.context.scene.cycles.use_denoising = True # Enable denoising

# --- Load the background image ---
img = bpy.data.images.load(image_path)
image_width = img.size[0]
image_height = img.size[1]

# Set render resolution to match image
bpy.context.scene.render.resolution_x = image_width
bpy.context.scene.render.resolution_y = image_height
bpy.context.scene.render.resolution_percentage = 100

# Calculate aspect ratio
aspect_ratio = image_width / image_height

# --- Add a plane and map the image as a material ---
# Create a plane that perfectly fits the camera view based on image aspect ratio
# We'll size it such that the camera's ortho_scale can directly map to it.
plane_size_x = 2.0 # Arbitrary base size for width, will adjust ortho_scale
plane_size_y = plane_size_x / aspect_ratio

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0)) # Start with size 1.0, then scale
plane = bpy.context.active_object
plane.scale = (plane_size_x / 2, plane_size_y / 2, 1) # Adjust scale to get desired dimensions
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True) # Apply scale to actual dimensions

# Create a material with the image
mat = bpy.data.materials.new(name="ImageMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
for node in nodes:
    nodes.remove(node)

# Add nodes for PBR material (more robust than just diffuse)
# Principled BSDF is generally preferred for Cycles
tex_image = nodes.new(type="ShaderNodeTexImage")
tex_image.image = img
tex_image.interpolation = 'Closest' # For pixel art or sharp images, 'Linear' for photos

principled_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
output = nodes.new(type="ShaderNodeOutputMaterial")

# Link image -> principled BSDF -> output
links.new(tex_image.outputs["Color"], principled_bsdf.inputs["Base Color"])
links.new(principled_bsdf.outputs["BSDF"], output.inputs["Surface"])

# Assign to plane
if plane.data.materials:
    plane.data.materials[0] = mat
else:
    plane.data.materials.append(mat)

# --- Import the 3D hair model ---
# Keep track of objects before import to easily find the new ones
initial_objects = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=model_path)
imported_objects = [obj for obj in bpy.context.scene.objects if obj not in initial_objects]

# Assuming the main model object is the parent or root of the imported group
# This might need adjustment based on your GLTF structure
model = None
if imported_objects:
    # Try to find the root object if there's a hierarchy, otherwise just take the first
    for obj in imported_objects:
        if obj.parent is None: # Assuming the main model object is a top-level parent
            model = obj
            break
    if model is None: # If no parent found, just take the first imported object
        model = imported_objects[0]
else:
    print(f"Warning: No objects imported from {model_path}. Check model file.")
    sys.exit(1)

# Adjust model position and scale
# These values will likely need fine-tuning for your specific hair model and head image.
# You might need to run this script, observe the output, and adjust.
model.location = (0, 0, 0.0) # Start with Z=0, then adjust as needed
model.scale = (1.0, 1.0, 1.0) # Start with 1.0, then adjust as needed (e.g., 0.9, 0.9, 0.9)
model.rotation_euler = (math.radians(90), 0, 0) # Example: Rotate if model is imported incorrectly oriented (e.g., Z-up vs Y-up)

# Make sure the model and plane are visible in render
model.hide_render = False
plane.hide_render = False

# --- Add orthographic camera (aligned like 2D image) ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
# ortho_scale should be the size of the *longest* dimension of the plane
# so that the entire plane (and thus image) fits into view
cam_data.ortho_scale = max(plane.dimensions.x, plane.dimensions.y)

cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam # Set this camera as the active scene camera

# Position camera directly above the plane looking down
# The plane is at Z=0. The camera looks along its -Y axis.
# So, put it on +Y and point it towards the origin.
cam.location = (0, -5, 0) # Position slightly back on Y axis relative to plane
cam.rotation_euler = (math.radians(90), math.radians(0), math.radians(0)) # Rotate 90 deg around X to look down along Y axis

# --- Add soft area light ---
# More robust lighting setup
# Clear default lights if any exist
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'LIGHT':
        obj.select_set(True)
bpy.ops.object.delete()

# Add a key light
light_key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
light_key_data.energy = 500 # Adjust energy as needed
light_key_data.size = 1.0 # Softness of shadows
light_key = bpy.data.objects.new(name="KeyLight", object_data=light_key_data)
bpy.context.collection.objects.link(light_key)
light_key.location = (2, -3, 3) # Example position: slightly to the side, back, and above
# Point light towards the origin (where the head model and plane are)
look_at_target(light_key, bpy.data.objects["Camera"].location) # Or target the model/plane
# light_key.rotation_euler = (math.radians(60), math.radians(-30), math.radians(30)) # Manual rotation

# Add a fill light (optional, for softer shadows and better ambient)
light_fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
light_fill_data.energy = 200
light_fill_data.size = 0.5
light_fill = bpy.data.objects.new(name="FillLight", object_data=light_fill_data)
bpy.context.collection.objects.link(light_fill)
light_fill.location = (-2, -1, 2) # Example position: opposite side of key light

# --- Set render output path ---
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.image_settings.file_format = 'JPEG' # Or 'PNG' for transparency if needed

# --- Render ---
print(f"Rendering scene to: {output_path}")
bpy.ops.render.render(write_still=True)
print("Rendering complete.")

# Optional: Function to make an object look at a target
def look_at_target(obj, target_location):
    direction = target_location - obj.location
    # Quaternions are more robust for rotations
    quat = direction.to_track_quat('-Z', 'Y') # Look along -Z (Blender's default forward), up is Y
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = quat