from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from easyocr import Reader
import os
import shutil
from starlette.requests import Request
import docx
import pandas as pd

app = FastAPI()

# Ensure the uploads directory exists
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)

# Mount the static and uploads directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize EasyOCR Reader
reader = Reader(['en', 'es', 'fr', 'de', 'it'], gpu=False)

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_image(request: Request,
                       file: UploadFile = File(...),
                       language: str = Form(...),
                       output_format: str = Form(...)):
    # Save the uploaded file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Perform OCR
    try:
        extracted_text = reader.readtext(file_path, detail=0, paragraph=True)
    except Exception as e:
        print(f"Error processing file: {e}")
        return {"detail": "Internal Server Error"}

    # Save the output in the requested format
    output_file_path = None
    if output_format == "docx":
        output_file_path = file_path.replace(".jpg", ".docx").replace(".png", ".docx")
        doc = docx.Document()
        doc.add_paragraph("\n".join(extracted_text))
        doc.save(output_file_path)
    elif output_format == "txt":
        output_file_path = file_path.replace(".jpg", ".txt").replace(".png", ".txt")
        with open(output_file_path, "w") as text_file:
            text_file.write("\n".join(extracted_text))
    elif output_format == "xlsx":
        output_file_path = file_path.replace(".jpg", ".xlsx").replace(".png", ".xlsx")
        df = pd.DataFrame({"Extracted Text": extracted_text})
        df.to_excel(output_file_path, index=False)

    # Make sure the image path is correct
    image_path = f"/uploads/{file.filename}"

    return templates.TemplateResponse("result.html", {
        "request": request,
        "extracted_text": "\n".join(extracted_text),
        "image_path": image_path,
        "output_file_path": f"/uploads/{os.path.basename(output_file_path)}"
    })

@app.get("/download/{file_path:path}", response_class=FileResponse)
async def download_file(file_path: str):
    return FileResponse(path=f"uploads/{file_path}", filename=file_path, media_type='application/octet-stream')

# Add this part for running with Uvicorn 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
#   cd "OCR Dashboard\Dashboard"