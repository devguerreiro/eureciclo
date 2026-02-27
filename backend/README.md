# XML Pipeline: FastAPI + AMQP

Este projeto é um pipeline de alta performance desenhado para processar arquivos ZIP massivos (na escala de GB/TB) contendo documentos XML, extrair dados específicos utilizando a biblioteca `lxml` e distribuir essas informações em um broker de mensagens AMQP (RabbitMQ).

## 🏗️ Arquitetura e Design Patterns

O projeto segue os princípios **SOLID** e utiliza padrões de design para garantir escalabilidade:

- **Streaming de Dados:** O processamento do ZIP não carrega o arquivo completo em RAM. Ele utiliza geradores (`yield`) e acesso direto ao buffer de disco (`SpooledTemporaryFile`) para manter o consumo de memória baixo e constante.
- **Decoupling (Desacoplamento):** A lógica de parsing, o armazenamento em memória e a mensageria são classes independentes, facilitando a manutenção e testes.
- **Background Tasks:** A publicação no AMQP via endpoint GET é realizada de forma assíncrona (segundo plano) para garantir tempos de resposta de milissegundos ao usuário.
- **Resiliência:** Filtros automáticos ignoram metadados de sistemas operacionais (como arquivos `._` do macOS) e recuperam erros de encoding em XMLs malformados.

## 📁 Estrutura do Projeto

```text
├── app/
│   ├── main.py              # Endpoints FastAPI e Gerenciamento de Estado
│   ├── services/
│   │   ├── xml_processor.py # Motor de extração e parsing (lxml)
│   │   └── amqp.py    # Cliente de integração AMQP (pika)
├── tests/                   # Testes unitários e mocks
├── Dockerfile               # Receita da imagem Python
├── docker-compose.yml       # Orquestração (App + RabbitMQ)
└── requirements.txt         # Dependências do projeto

```

## 🚀 Como Executar

**Pré-requisitos:** Docker e Docker Compose instalados.

1. **Subir o ambiente:**

```bash
docker-compose up --build

```

2. **Acessar a API:**
   A aplicação estará disponível em `http://localhost:8000`.

## 🛠️ Fluxos Principais

### 1. Upload e Extração

- **Endpoint:** `POST /upload`
- **Fluxo:** Recebe um ZIP -> Itera via stream -> Valida arquivos -> Faz o parse dos XMLs -> Salva na variável global `DATA_STORAGE`.

### 2. Consulta e Publicação

- **Endpoint:** `GET /extraidos`
- **Fluxo:** Retorna o JSON com os dados da memória -> Dispara uma **Background Task** -> Abre conexão AMQP -> Publica cada item individualmente como mensagem persistente.

## 📊 Monitoramento e Documentação

- **API Docs:** A documentação interativa (Swagger) com todos os detalhes dos endpoints pode ser acessada em: `http://localhost:8000/docs`
- **RabbitMQ Management:** Acompanhe as filas, o volume de mensagens e a saúde do broker pela interface web: `http://localhost:15672` (Usuário/Senha: `guest`).

## 🧪 Testes

Para rodar a suíte de testes (com mocks de RabbitMQ e simulação de arquivos reais):

```bash
pytest -v

```
