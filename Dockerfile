FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Gunakan /app untuk instalasi awal
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Salin semua file dari luar ke dalam /app container
COPY . .

# 3. PINDAH FOLDER DI SINI (Tepat sebelum menjalankan CMD)
WORKDIR /app/app

EXPOSE ${PORT:-8000}

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}