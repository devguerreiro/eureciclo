import io
import zipfile

from fastapi import FastAPI, UploadFile, HTTPException


app = FastAPI()


@app.post("/upload")
async def upload(file: UploadFile):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="must be a .zip file")

    content = await file.read()
    zip_buffer = io.BytesIO(content)

    try:
        with zipfile.ZipFile(zip_buffer) as z:
            for filename in z.namelist():
                pass

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="invalid or corrupted zip file")

    return
