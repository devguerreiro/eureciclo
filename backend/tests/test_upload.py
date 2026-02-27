import pytest
import io
import zipfile

from fastapi.testclient import TestClient
from unittest.mock import patch

from src import main

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Limpa a variável global antes de cada teste."""
    main.extracted_data.clear()


# --- TESTES DO ENDPOINT DE UPLOAD ---
def test_upload_valid_zip():
    """Testa se o upload extrai os dados corretamente para a memória."""
    # Cria um ZIP fake com os bytes que causavam erro (BOM + XML)
    xml_content = b"""\xef\xbb\xbf<xml>
    <article>
        <body>
            <Identifica>foo</Identifica>
            <Data>bar</Data>
            <Ementa>foobar</Ementa>
            <Titulo>fizz</Titulo>
            <SubTitulo>buzz</SubTitulo>
            <Texto>fizzbuzz</Texto>
        </body>
    </article>
    </xml>
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a") as z:
        z.writestr("oficio.xml", xml_content)
        # Adiciona lixo do macOS para testar o filtro de resiliência
        z.writestr("__MACOSX/._oficio.xml", b"lixo")

    zip_buffer.seek(0)

    response = client.post(
        "/upload", files={"file": ("test.zip", zip_buffer, "application/zip")}
    )

    assert response.status_code == 200
    assert len(main.extracted_data) == 1
    assert main.extracted_data[0].identifica == "foo"
    assert main.extracted_data[0].data == "bar"
    assert main.extracted_data[0].ementa == "foobar"
    assert main.extracted_data[0].titulo == "fizz"
    assert main.extracted_data[0].subtitulo == "buzz"
    assert main.extracted_data[0].texto == "fizzbuzz"


def test_upload_invalid_extension():
    """Testa se o sistema rejeita arquivos que não são .zip."""
    response = client.post(
        "/upload", files={"file": ("test.txt", b"conteudo", "text/plain")}
    )
    assert response.status_code == 400
    assert "Must be a .zip file" in response.json()["detail"]


# --- TESTES DO ENDPOINT DE LISTAGEM E PUBLICAÇÃO ---
@patch("src.services.amqp.AMQPPublisher.publish_batch")
def test_get_extracted_data_and_publish(mock_publish):
    """
    Testa o endpoint GET e verifica se a função de publicação
    no AMQP foi agendada corretamente.
    """
    # 1. Simula dados já existentes na memória
    mock_data = {
        "identifica": "foo",
        "data": "",
        "ementa": "",
        "titulo": "",
        "subtitulo": "",
        "texto": "",
    }
    main.extracted_data.append(mock_data)

    # 2. Chama o endpoint GET
    response = client.get("/extracted-data")

    # 3. Verificações
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["identifica"] == "foo"

    # Verifica se o publisher foi chamado (via BackgroundTask)
    # Nota: No TestClient, background tasks rodam de forma síncrona ao final
    mock_publish.assert_called_once_with(main.extracted_data)


def test_get_extracted_data_empty():
    """Testa o comportamento quando não há dados na memória."""
    response = client.get("/extracted-data")
    assert response.status_code == 200
    data = response.json()
    assert data == []
