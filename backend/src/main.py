import io
import xml.etree.ElementTree as ET
import zipfile

from fastapi import FastAPI, UploadFile, HTTPException


app = FastAPI()


@app.post("/upload")
async def upload(file: UploadFile):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="must be a .zip file")

    content = await file.read()
    zip_buffer = io.BytesIO(content)

    extracted_data = []
    try:
        with zipfile.ZipFile(zip_buffer) as z:
            for filename in z.namelist():
                if not filename.endswith(".xml"):
                    continue
                with z.open(filename) as xml_file:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    body = root.find(".//body")
                    if body is not None:
                        data = {
                            "identifica": body.findtext("Identifica"),
                            "data": body.findtext("Data"),
                            "ementa": body.findtext("Ementa"),
                            "titulo": body.findtext("Titulo"),
                            "subtitulo": body.findtext("Subtitulo"),
                            "texto": body.findtext("Texto"),
                        }
                        extracted_data.append(data)

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="invalid or corrupted zip file")

    return extracted_data
