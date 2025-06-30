from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import subprocess
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
MODEL_PATH = "filters/round.glb"  # or any default model

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/apply-filter")
async def apply_filter(file: UploadFile = File(...)):
    # 1. Save the uploaded image
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Define the output path
    output_path = os.path.join(OUTPUT_DIR, f"filtered_{file.filename}")

    # 3. Call Blender to process the image using the filter
    try:
        subprocess.run([
            "blender", "--background", "--python", "blender_scripts/apply_filter.py",
            "--", input_path, MODEL_PATH, output_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        return {"error": "Blender processing failed", "details": str(e)}

    # 4. Return the processed image
    return FileResponse(output_path, media_type="image/jpeg", filename=os.path.basename(output_path))
