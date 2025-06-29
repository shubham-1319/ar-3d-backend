from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import uuid
import os
import subprocess

app = FastAPI()

@app.post("/process-3d/")
async def process_3d(file: UploadFile = File(...), filter_type: str = Form(...)):
    # Save incoming image
    img_id = uuid.uuid4().hex
    input_path = f"uploads/{img_id}.jpg"
    output_path = f"outputs/{img_id}_out.jpg"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Map filter name to .glb model
    filter_model = f"filters/{filter_type}.glb"

    # Run Blender in background
    blender_path = "C:/Program Files/Blender Foundation/Blender/blender.exe"  # adjust for your system
    blender_script = "blender_scripts/apply_filter.py"
    subprocess.run([
        blender_path,
        "--background",
        "--python", blender_script,
        "--", input_path, filter_model, output_path
    ])

    return FileResponse(output_path, media_type="image/jpeg")
