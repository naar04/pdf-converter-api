FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "--workers=1", "--threads=1", "--timeout=300", "--bind", "0.0.0.0:10000", "app:app"]
