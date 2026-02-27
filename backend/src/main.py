from typing import List

from fastapi import FastAPI, UploadFile, HTTPException, Depends

from src.services.xml_processor import ExtractedData, XMLStreamProcessor

app = FastAPI()

extracted_data: List[ExtractedData] = []


# DESIGN PATTERN: Dependency Injection.
# Facilita testes unitários, permitindo trocar o processador real por um "mock".
def get_processor():
    return XMLStreamProcessor()


@app.post("/upload")
async def upload(
    file: UploadFile, processor: XMLStreamProcessor = Depends(get_processor)
):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Must be a .zip file")

    # PERFORMANCE: 'file.file' é o segredo. O FastAPI/Starlette salva arquivos grandes
    # em um arquivo temporário no DISCO (SpooledTemporaryFile).
    # Se usasse 'await file.read()', o servidor tentaria colocar tudo na RAM e poderia quebrar.
    # Ao passar 'file.file', é passado apenas a referência para abrir o arquivo do disco.
    try:
        global extracted_data
        # PERFORMANCE: Transforma o gerador em lista apenas para o retorno JSON.
        # Se precisasse salvar num banco, faria: for item in processor.process_zip_stream(...):
        # e nunca usaria list(), mantendo o uso de RAM próximo de zero.
        extracted_data = list(processor.process_zip_stream(file.file))
        return extracted_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@app.get("/extracted-data", response_model=List[ExtractedData])
def get_extracted_data() -> List[ExtractedData]:
    return extracted_data
