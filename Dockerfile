# Gunakan Python 3.11 Slim yang ringan namun lengkap
FROM python:3.11-slim

# Set environment variables agar Python tidak membuat file .pyc dan log langsung keluar
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tentukan direktori kerja di dalam kontainer
WORKDIR /app

# Install dependensi sistem operasi (SANGAT PENTING UNTUK OCR & PDF)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements dan install library Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam kontainer
COPY . .

# Buka port 8000
EXPOSE 8000

# Perintah untuk menjalankan FastAPI menggunakan Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]