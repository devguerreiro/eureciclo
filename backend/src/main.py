from typing import List

from fastapi import FastAPI, UploadFile, HTTPException, Depends

from src.services.xml_processor import XMLStreamProcessor

app = FastAPI()


# DESIGN PATTERN: Dependency Injection.
# Facilita testes unitários, permitindo trocar o processador real por um "mock".
def get_processor():
    return XMLStreamProcessor()


@app.post("/upload", response_model=List[dict])
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
        # PERFORMANCE: Transforma o gerador em lista apenas para o retorno JSON.
        # Se precisasse salvar num banco, faria: for item in processor.process_zip_stream(...):
        # e nunca usaria list(), mantendo o uso de RAM próximo de zero.
        results = list(processor.process_zip_stream(file.file))
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
