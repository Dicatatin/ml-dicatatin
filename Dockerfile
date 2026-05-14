FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Posisikan terminal di /app
WORKDIR /app

# Install dependencies terlebih dahulu (best practice Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh file (termasuk folder 'app' dan isinya) ke dalam /app
COPY . .

# Ekspos port
EXPOSE ${PORT:-8000}

# Jalankan Uvicorn dengan menunjuk ke folder 'app' dan file 'main.py'
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
