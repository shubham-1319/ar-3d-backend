from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import subprocess
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_PATH = os.path.join(BASE_DIR, "filters", "round123.glb")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/apply-filter")
async def apply_filter(file: UploadFile = File(...)):
    # 1. Save the uploaded image
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Define the output path
    output_filename = f"filtered_{file.filename}"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # 3. Call Blender with ABSOLUTE paths
    try:
        subprocess.run([
            "blender", "--background", "--python", os.path.join(BASE_DIR, "blender_scripts", "apply_filter.py"),
            "--", os.path.abspath(input_path), MODEL_PATH, os.path.abspath(output_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        return {"error": "Blender processing failed", "details": str(e)}

    # 4. Return the processed image
    if not os.path.exists(output_path):
        return {"error": "Output file was not generated"}
    
    return FileResponse(output_path, media_type="image/jpeg", filename=output_filename)
