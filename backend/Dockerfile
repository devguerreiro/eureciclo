FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema necessárias para o lxml
RUN apt-get update && apt-get install -y \
    libxml2-dev libxslt-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]