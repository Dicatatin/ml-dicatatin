# 📚 DICATAT.IN - Machine Learning Service (ml-dicatatin)

**ml-dicatatin** adalah service *core AI engine* untuk platform **DICATAT.IN**. Service ini bertugas untuk mengubah foto catatan tulisan tangan yang berantakan menjadi materi belajar interaktif dan terstruktur (dalam bentuk workspace React Flow) serta flashcard untuk *active recall* dalam waktu kurang dari 30 detik.

## 🚀 Fitur Utama

- **Pipeline OCR Canggih**: Mengekstrak teks dari catatan tulisan tangan.
  - *Engine Utama*: OpenAI Vision API (gpt-4o) untuk akurasi tinggi.
  - *Engine Fallback*: PaddleOCR Lokal untuk keandalan jika API gagal.
- **Sanitasi Teks AI**: Otomatis memperbaiki *typo* (salah ketik) dan memperluas singkatan bahasa Indonesia.
- **7 Metode Belajar yang Didukung**:
  1. Mind Map
  2. Cornell Notes
  3. Boxing Method
  4. Charting
  5. Zettelkasten
  6. Sketchnoting
  7. Feynman Technique
- **Pembuatan Flashcard Cerdas**: Menghasilkan flashcard dengan algoritma *spaced-repetition* (SM-2) dari catatan untuk mendukung pembelajaran aktif.
- **FastAPI Backend**: Endpoint API yang cepat, asinkronus, dan tangguh khusus untuk komunikasi internal dengan *main backend* (Laravel).

## 🏗 Arsitektur & Alur Kerja

Service ini **tidak berkomunikasi langsung dengan frontend**. Service ini dirancang untuk dipanggil secara internal oleh backend utama (Laravel).

**Alur Pipeline Utama (`/process`)**:
1. **Input**: File Gambar (JPG/PNG) & Pemilihan Metode
2. **Preprocessing**: OpenCV (Resize, Denoise, Deskew, Sharpen)
3. **Ekstraksi (OCR)**: Vision API / PaddleOCR -> Teks Mentah (*Raw Text*)
4. **Sanitasi**: LLM -> Teks Bersih (*Clean Text*)
5. **Transformasi**: LLM + Instructor -> JSON Terstruktur (React Flow *Nodes & Edges*)
6. **Flashcard**: LLM -> Pasangan Tanya & Jawab (*Q&A*)
7. **Output**: Objek Workspace Lengkap ke Backend

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **AI & Transformasi**: OpenAI API, Instructor (untuk validasi output Pydantic)
- **Computer Vision & OCR**: PaddleOCR, OpenCV, Pillow
- **Pemrosesan Data**: NumPy, Pydantic

## 💻 Panduan Instalasi & Setup

**Prasyarat:**
- **Python 3.11** (Syarat ketat. **JANGAN** gunakan versi 3.12 atau 3.13 karena masalah kompatibilitas dengan PaddleOCR).

**1. Buat dan Aktifkan Virtual Environment**
```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# Linux/Mac
python3.11 -m venv venv
source venv/bin/activate
```

**2. Instalasi Dependensi**
> **PENTING:** Anda harus menginstal `numpy` dan `paddlepaddle` dengan urutan yang tepat di bawah ini **sebelum** menginstal sisa kebutuhan (*requirements*) lainnya. Jangan upgrade numpy ke 2.x!

```bash
pip install --upgrade pip
pip install numpy==1.26.4
pip install paddlepaddle==2.6.1
pip install -r requirements.txt
```

**3. Konfigurasi Environment Variables**
Salin file `.env.example` menjadi `.env` dan isi dengan kunci API Anda (misalnya: `OPENAI_API_KEY`).
```bash
cp .env.example .env
```

## 🚀 Menjalankan Service

**Pengembangan Lokal (Local Development):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Melalui Docker:**
Service ini juga telah dikonfigurasi untuk berjalan menggunakan `docker-compose` sebagai bagian dari ekosistem DICATAT.IN secara keseluruhan.

## 📡 Endpoint API

- `POST /process`: Pipeline utama. Menerima form-data berupa `file` gambar dan `method`. Mengembalikan data workspace React Flow dan flashcard yang telah diproses.
- `POST /transform`: Mengubah metode pencatatan menggunakan teks yang sudah dibersihkan sebelumnya (tanpa perlu unggah ulang).
- `GET /health`: Endpoint *health check* untuk Docker dan routing internal.

## 📁 Struktur Proyek
- `/core`: Konfigurasi aplikasi (Pydantic Settings) dan *custom exceptions*.
- `/ocr`: Logika preprocessing gambar, ekstraksi (LLM/Paddle), dan sanitasi teks.
- `/transform`: File prompt `.txt`, skema validasi Pydantic, dan logika transformasi LLM untuk setiap metode belajar.
- `/flashcard`: Ekstraksi flashcard dan algoritma *spaced repetition* (SuperMemo-2).
- `/utils`: Fungsi *helper* utilitas (pemrosesan gambar, encoding base64, dll).