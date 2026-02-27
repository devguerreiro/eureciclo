import io
import zipfile

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def create_mock_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a") as z:
        z.writestr("file.xml", "<xml></xml>")
    zip_buffer.seek(0)
    return zip_buffer


def test_upload_zip_success():
    zip_data = create_mock_zip()

    files = {"file": ("test.zip", zip_data, "application/zip")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200


def test_upload_invalid_extension():
    files = {"file": ("invalid.txt", io.BytesIO(b"foo"), "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert "must be a .zip file" in response.json()["detail"]
