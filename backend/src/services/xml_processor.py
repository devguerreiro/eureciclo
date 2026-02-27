import zipfile

from typing import Generator, Dict, Any, Optional

from lxml import etree


class XMLStreamProcessor:
    def __init__(self, parser_recover: bool = True):
        # PERFORMANCE: Instanciar o parser uma única vez no __init__ evita o overhead
        # de criar um novo objeto parser para cada um dos milhares de arquivos dentro do ZIP.
        self.parser = etree.XMLParser(
            recover=parser_recover,  # Resolve erros de caracteres inválidos (ex: o 0xb0)
            encoding="utf-8",  # Define o padrão, mas o lxml detecta o BOM sozinho
            remove_blank_text=True,  # PERFORMANCE: Economiza memória removendo espaços inúteis entre tags
        )

    def _parse_xml_content(self, xml_data: bytes) -> Optional[Dict[str, Any]]:
        try:
            # PERFORMANCE: etree.fromstring() em bytes é mais rápido que etree.parse() em arquivos
            # para o lxml, pois ele processa o bloco de memória diretamente em C.
            root = etree.fromstring(xml_data, parser=self.parser)
            body = root.find(".//body")

            if body is None:
                return None

            # CLEAN CODE: Uso de dicionário tipado.
            # O .findtext() é mais seguro que .find().text pois não quebra se a tag faltar.
            return {
                "identifica": (body.findtext("Identifica") or "").strip(),
                "data": (body.findtext("Data") or "").strip(),
                "ementa": (body.findtext("Ementa") or "").strip(),
                "titulo": (body.findtext("Titulo") or "").strip(),
                "subtitulo": (body.findtext("SubTitulo") or "").strip(),
                "texto": (body.findtext("Texto") or "").strip(),
            }
        except Exception:
            return None  # Fail-safe: Se um XML estiver podre, o sistema ignora e segue o próximo.

    def process_zip_stream(self, file_stream) -> Generator[Dict[str, Any], None, None]:
        # PERFORMANCE: 'with' para garantir que o ponteiro do arquivo seja fechado após o uso.
        with zipfile.ZipFile(file_stream) as z:
            for filename in z.namelist():

                # CLEAN CODE & RESILIÊNCIA: Filtro explícito para ignorar lixo do macOS/Linux.
                # '._' e '__MACOSX' são os maiores causadores de erro de "Document is empty".
                if (
                    not filename.lower().endswith(".xml")
                    or "/." in filename
                    or filename.startswith(".")
                ):
                    continue

                # PERFORMANCE: z.open() abre um "file-like object" (stream).
                # Só lê os bytes daquele arquivo específico (.read()) no momento do parse.
                with z.open(filename) as xml_file:
                    data = self._parse_xml_content(xml_file.read())
                    if data:
                        # DESIGN PATTERN (Iterator): O 'yield' transforma o método num gerador.
                        # Em vez de criar uma lista de 1 milhão de itens na RAM,
                        # ele entrega um por um para quem chamou.
                        yield data
