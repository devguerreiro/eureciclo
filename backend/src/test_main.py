import io
import zipfile

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def create_mock_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a") as z:
        file1_content = """
        <xml>
            <article>
                <body>
                    <Identifica>foo</Identifica>
                    <Data>foo</Data>
                    <Ementa/>
                    <Titulo/>
                    <Subtitulo/>
                    <Texto>foo</Texto>
                </body>
            </article>
        </xml>
        """
        z.writestr("file1.xml", file1_content)

        file2_content = """
        <xml>
            <article>
                <body>
                    <Identifica>foo</Identifica>
                    <Data>foo</Data>
                    <Ementa/>
                    <Titulo/>
                    <Subtitulo/>
                    <Texto>foo</Texto>
                </body>
            </article>
        </xml>
        """
        z.writestr("file2.xml", file2_content)

        z.writestr("ignore.txt", "foobar")
    zip_buffer.seek(0)
    return zip_buffer


def test_upload_zip_success():
    zip_data = create_mock_zip()

    files = {"file": ("test.zip", zip_data, "application/zip")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    for item in data:
        assert item["identifica"] == "foo"
        assert item["data"] == "foo"
        assert item["ementa"] == ""
        assert item["titulo"] == ""
        assert item["subtitulo"] == ""
        assert item["texto"] == "foo"


def test_upload_invalid_extension():
    files = {"file": ("invalid.txt", io.BytesIO(b"foo"), "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    assert "must be a .zip file" in response.json()["detail"]
