import os
from typing import List

from fastapi import FastAPI, UploadFile, HTTPException, Depends, BackgroundTasks

from src.services.amqp import AMQPPublisher
from src.services.xml_processor import ExtractedData, XMLStreamProcessor

app = FastAPI()

# Configurações AMQP
AMQP_CONFIG = {
    "url": os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/"),
    "queue": "xml_extracted_data",
}

DATA_STORAGE: List[ExtractedData] = []


# DESIGN PATTERN: Dependency Injection.
# Facilita testes unitários, permitindo trocar o processador real por um "mock".
def get_processor():
    return XMLStreamProcessor()


@app.post("/upload")
def upload(file: UploadFile, processor: XMLStreamProcessor = Depends(get_processor)):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Must be a .zip file")

    # PERFORMANCE: 'file.file' é o segredo. O FastAPI/Starlette salva arquivos grandes
    # em um arquivo temporário no DISCO (SpooledTemporaryFile).
    # Se usasse 'await file.read()', o servidor tentaria colocar tudo na RAM e poderia quebrar.
    # Ao passar 'file.file', é passado apenas a referência para abrir o arquivo do disco.
    try:
        global DATA_STORAGE
        # PERFORMANCE: Transforma o gerador em lista apenas para o retorno JSON.
        # Se precisasse salvar num banco, faria: for item in processor.process_zip_stream(...):
        # e nunca usaria list(), mantendo o uso de RAM próximo de zero.
        DATA_STORAGE = list(processor.process_zip_stream(file.file))
        return DATA_STORAGE

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@app.get("/extracted-data", response_model=List[ExtractedData])
def get_extracted_data(background_tasks: BackgroundTasks) -> List[ExtractedData]:
    # SEGURANÇA: Verifica se a variável global tem dados antes de agir.
    if not DATA_STORAGE:
        return []

    # INSTANCIAÇÃO: Cria o serviço que sabe falar com o RabbitMQ.
    publisher = AMQPPublisher(AMQP_CONFIG["url"], AMQP_CONFIG["queue"])

    # --- O PONTO CHAVE DA PERFORMANCE ---
    # DESIGN PATTERN: Worker Thread / Background Task.
    # Em vez de chamar publisher.publish_batch(DATA_STORAGE) diretamente,
    # é feito o agendamento utilizando o próprio FastAPI.
    background_tasks.add_task(publisher.publish_batch, DATA_STORAGE)

    # O comando acima diz: "FastAPI, assim que você enviar a resposta HTTP
    # pro usuário, execute esta função aqui no fundo sem travar nada".

    # RETORNO IMEDIATO: O usuário recebe o JSON na hora.
    # Ele não precisa esperar o loop das mensagens terminar.
    return DATA_STORAGE
