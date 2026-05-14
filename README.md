# 📚 DICATAT.IN — Machine Learning Service (ml-dicatatin)

**ml-dicatatin** adalah service *core AI engine* untuk platform **DICATAT.IN**. Service ini mengubah foto catatan tulisan tangan menjadi materi belajar interaktif dan terstruktur (workspace React Flow) serta flashcard untuk *active recall* — sepenuhnya melalui OpenAI API.

## 🚀 Fitur Utama

- **OCR via Vision API**: Mengekstrak teks dari gambar catatan tulisan tangan menggunakan OpenAI Vision API (`gpt-4o-mini`).
- **Sanitasi Teks AI**: Otomatis memperbaiki *typo* dan memperluas singkatan bahasa Indonesia.
- **7 Metode Belajar yang Didukung**:
  1. Mind Map
  2. Cornell Notes
  3. Boxing Method
  4. Charting
  5. Zettelkasten
  6. Sketchnoting
  7. Feynman Technique
- **Pembuatan Flashcard Cerdas**: Menghasilkan flashcard dengan algoritma *spaced-repetition* (SM-2) untuk pembelajaran aktif.
- **FastAPI Backend**: Endpoint API yang cepat, asinkronus, dan tangguh untuk komunikasi internal dengan *main backend* (Laravel).

## 🏗 Arsitektur & Alur Kerja

Service ini **tidak berkomunikasi langsung dengan frontend**. Service ini dirancang untuk dipanggil secara internal oleh backend utama (Laravel).

**Alur Pipeline (`/process`)**:

```
Gambar (JPG/PNG) + Metode
        │
        ▼
 ┌──────────────┐
 │  Vision API  │ ──► Teks Mentah (Raw Text)
 │  (OCR)       │
 └──────────────┘
        │
        ▼
 ┌──────────────┐
 │  Sanitizer   │ ──► Teks Bersih (Clean Text)
 └──────────────┘
        │
        ├──────────────────────┐
        ▼                      ▼
 ┌──────────────┐      ┌──────────────┐
 │  Transformer │      │  Flashcard   │
 │  (OpenAI)    │      │  Generator   │
 └──────────────┘      └──────────────┘
        │                      │
        ▼                      ▼
  React Flow JSON        Q&A Flashcards
  (Nodes & Edges)         (SM-2 Ready)
        │                      │
        └──────────┬───────────┘
                   ▼
           JSON Response
          ke Backend Laravel
```

1. **Input**: File Gambar (JPG/PNG) & Pemilihan Metode
2. **Ekstraksi (OCR)**: OpenAI Vision API → Teks Mentah (*Raw Text*)
3. **Sanitasi**: Pembersihan teks → Teks Bersih (*Clean Text*)
4. **Transformasi**: OpenAI + Instructor → JSON Terstruktur (React Flow *Nodes & Edges*)
5. **Flashcard**: OpenAI → Pasangan Tanya & Jawab (*Q&A*) dengan parameter SM-2
6. **Output**: Objek Workspace Lengkap ke Backend

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **AI Engine**: OpenAI API (`gpt-4o-mini`) — satu API key untuk semua stage
- **Structured Output**: Instructor (validasi output Pydantic)
- **Konfigurasi**: Pydantic Settings

## 💻 Panduan Instalasi & Setup

**Prasyarat:**
- Python 3.11+

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
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**3. Konfigurasi Environment Variables**

Salin file `.env.example` menjadi `.env` dan isi dengan API key OpenAI Anda.

```bash
cp .env.example .env
```

| Variable | Deskripsi | Default |
|---|---|---|
| `OPENAI_API_KEY` | API key OpenAI **(wajib)** | — |
| `MODEL_OCR` | Model untuk Vision OCR | `gpt-4o-mini` |
| `MODEL_TRANSFORM` | Model untuk transformasi metode | `gpt-4o-mini` |
| `MODEL_FLASHCARD` | Model untuk generate flashcard | `gpt-4o-mini` |

## 🚀 Menjalankan Service

**Pengembangan Lokal:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Melalui Docker:**
```bash
docker compose up --build
```

## 📡 Endpoint API

| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/process` | Pipeline utama. Menerima `file` (gambar) dan `method` (form-data). Mengembalikan workspace React Flow + flashcard. |
| `POST` | `/transform` | Mengubah metode pencatatan menggunakan teks yang sudah dibersihkan (tanpa upload ulang). |
| `POST` | `/flashcard` | Membuat ulang flashcard (regenerate) menggunakan teks yang sudah dibersihkan. |
| `GET` | `/health` | Health check untuk Docker dan routing internal. |

## 📁 Struktur Proyek

```
ml-dicatatin/
├── app/                  # Semua kode Python hidup di sini
│   ├── api/              # HTTP Layer: routes & schemas (tanpa business logic)
│   ├── core/             # Konfigurasi, exceptions, logger, API clients
│   ├── ocr/              # Ekstraksi teks via Vision API & sanitasi
│   ├── transform/        # Prompt, skema validasi, & logika transformasi LLM
│   ├── flashcard/        # Generator flashcard & algoritma SM-2
│   ├── services/         # Service layer: orchestrasi pipeline
│   └── main.py           # Entry point FastAPI & app factory
├── tests/                # Unit test (SM-2, Schemas, Pipeline)
├── Dockerfile            # Container image (lightweight, API-only)
├── docker-compose.yml
├── requirements.txt
└── .env.example
```