import pytest
import zipfile
import io

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a") as z:
        valid_xml = b"\xef\xbb\xbf<xml><body><Identifica>ID1</Identifica></body></xml>"
        z.writestr("data/valid.xml", valid_xml)

        z.writestr("__MACOSX/._valid.xml", b"binario lixo")

        z.writestr("readme.txt", b"hello world")

    zip_buffer.seek(0)
    return zip_buffer


def test_upload_large_file_structure(mock_zip):
    files = {"file": ("test.zip", mock_zip, "application/zip")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["identifica"] == "ID1"


def test_upload_invalid_file_type():
    files = {"file": ("test.txt", b"conteudo", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
