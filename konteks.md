# Master Blueprint: DICATAT.IN

> **Untuk:** Vibe Coding AI Assistant (Cursor, Copilot, Claude, dll)
> **Versi:** 3.0 — Competition Ready & API-Aligned
> **Terakhir diperbarui:** Mei 2026
> **Prinsip utama:** Baca dokumen ini PENUH sebelum menulis satu baris kode pun.

---

## Daftar Isi

1. [Visi & Konteks Produk](#1-visi--konteks-produk)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Peran ML Engineer di Tim](#3-peran-ml-engineer-di-tim)
4. [Tech Stack & Dependency](#4-tech-stack--dependency)
5. [Struktur Direktori (Domain-Driven)](#5-struktur-direktori-domain-driven)
6. [Pipeline Inti: OCR & Transformasi](#6-pipeline-inti-ocr--transformasi)
7. [Kontrak API (ML → Backend)](#7-kontrak-api-ml--backend)
8. [Skema Output per Metode Belajar](#8-skema-output-per-metode-belajar)
9. [Node & Edge Spec (React Flow)](#9-node--edge-spec-react-flow)
10. [Modul Flashcard & SM-2](#10-modul-flashcard--sm-2)
11. [Konfigurasi & Environment](#11-konfigurasi--environment)
12. [Error Handling & Response Standard](#12-error-handling--response-standard)
13. [Aturan Kode & Konvensi](#13-aturan-kode--konvensi)
14. [Checklist Sebelum Submit ke Tim](#14-checklist-sebelum-submit-ke-tim)

---

## 1. Visi & Konteks Produk

### Apa itu DICATAT.IN?

Platform produktivitas berbasis AI untuk mahasiswa Indonesia. Mengubah foto catatan tulisan tangan yang berantakan menjadi catatan terstruktur dan flashcard belajar aktif dalam waktu kurang dari 30 detik.

### Masalah yang Diselesaikan

- **Catatan mati:** Mahasiswa mencatat cepat dan berantakan, lalu tidak pernah dibaca ulang.
- **Belajar pasif:** Membaca ulang catatan adalah metode paling tidak efektif.
- **Accessibility gap:** Tidak ada tools belajar digital yang ramah disleksia di Indonesia.

### Alur Pengguna (Happy Path)(bisa berubah flownya nanti)

```
Landing Page → Login (Supabase Auth) → Home/Dashboard
→ Klik "Buat Baru" → Upload Foto Catatan → Pilih Metode
→ AI Processing (<30 detik) → Workspace Editor (React Flow Canvas A4)
→ Export PDF / Mulai Flashcard Session
```

### 7 Metode Belajar yang Didukung

| ID Method (API) | Nama Tampilan     | Karakter Utama                                    |
| --------------- | ----------------- | ------------------------------------------------- |
| `mind_map`      | Mind Map          | Tree hierarkis radial dari center                 |
| `cornell`       | Cornell Notes     | 3 zona: Cues (30%) / Notes (70%) / Summary        |
| `boxing`        | Boxing Method     | Group nodes tematik (parent-child)                |
| `charting`      | Charting          | Grid matrix komparasi                             |
| `zettelkasten`  | Zettelkasten      | Atomic nodes dengan kode ID unik                  |
| `sketchnoting`  | Sketchnoting      | Node variabel ukuran + SVG icon                   |
| `feynman`       | Feynman Technique | 4 node vertikal: Concept → Simple → Gap → Analogy |

---

## 2. Arsitektur Sistem

### Topology Docker Compose

```
┌─────────────────────────────────────────────────────┐
│                 dicatatin-workspace/                │
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐   │
│  │  fe-dicatatin│    │      be-dicatatin        │   │
│  │  React + Vite│◄──►│   Laravel 12 + PHP 8.4   │   │
│  │  Port: 5173  │    │      Port: 8000          │   │
│  └──────────────┘    └────────────┬─────────────┘   │
│                                   │ HTTP Internal   │
│                      ┌────────────▼─────────────┐   │
│                      │      ml-dicatatin        │   │
│                      │   FastAPI + Python 3.11  │   │
│                      │      Port: 8001          │   │
│                      └──────────────────────────┘   │
│                                                     │
│  ┌─────────────┐    ┌──────────────────────────┐    │
│  │ PostgreSQL  │    │        Redis             │    │
│  │ Port: 5432  │    │      Port: 6379          │    │
│  │ (host local)│    │    (session/cache)       │    │
│  └─────────────┘    └──────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Alur Request Lengkap (Saat Upload Foto)

```
Frontend (React)
    │ POST /api/workspaces
    │ multipart/form-data: {file, name, method}
    ▼
Backend (Laravel) ← validasi JWT Supabase
    │ Forward ke ML service
    │ POST http://ml:8001/process
    ▼
ML Service (FastAPI)
    ├── OCR Pipeline
    │   ├── preprocessor.py   (OpenCV: deskew, denoise, resize)
    │   ├── extractor_llm.py  (GPT-4o Vision — jalur utama)
    │   └── extractor.py      (PaddleOCR — fallback lokal)
    ├── Sanitizer
    │   └── sanitizer.py      (LLM: perbaiki singkatan Indo)
    └── Transformer
        ├── transformer.py    (LLM: structured output per method)
        └── schemas.py        (Pydantic: validasi JSON output)
    │
    │ Return: {nodes[], edges[], flashcards[], raw_text}
    ▼
Backend (Laravel)
    │ Simpan ke PostgreSQL (JSONB)
    │
    │ Return: Full workspace object
    ▼
Frontend (React) → Render di React Flow Canvas
```

### Catatan Penting Deployment

- Database PostgreSQL berjalan di **host machine** (bukan di Docker).
- Backend Laravel terhubung ke DB via `host.docker.internal` sebagai `DB_HOST`.
- ML Service tidak punya akses langsung ke database — semua data dilewatkan via Backend.
- ML Service hanya menerima request dari Backend, **bukan dari Frontend secara langsung**.

---

## 3. Peran ML Engineer di Tim

### Ownership Penuh (kamu yang kerjakan)

- Seluruh kode di dalam folder `ml-dicatatin/`
- Desain prompt untuk semua 7 metode di `transform/prompts/*.txt`
- Skema Pydantic untuk validasi output LLM di `transform/schemas.py`
- Algoritma SM-2 di `flashcard/sm2.py`
- Dockerfile dan environment ML service

### Kontrak dengan Backend Engineer

Backend akan memanggil satu endpoint utama dari ML:

```
POST http://ml:8001/process
```

Kamu bertanggung jawab memastikan endpoint ini selalu return format yang konsisten.

### Kontrak dengan Frontend Engineer

Frontend tidak berbicara langsung ke ML. Namun kamu perlu tahu struktur `nodes[]` dan `edges[]` yang akan di-render React Flow, karena **ML yang generate data ini**. Pelajari seksi 8 dan 9 di bawah dengan seksama.

---

## 4. Tech Stack & Dependency

### `requirements.txt` (final, sudah diverifikasi Python 3.11 + Windows/Linux)

```txt
# --- CORE WEB & API ---
fastapi>=0.115.0
uvicorn[standard]>=0.30.6
python-multipart>=0.0.9
httpx>=0.27.2
python-dotenv>=1.0.1
pydantic>=2.8.2
pydantic-settings>=2.0.0

# --- AI ENGINE ---
openai>=1.40.0
instructor>=1.3.0        # Structured output dari LLM ke Pydantic schema

# --- OCR: JALUR UTAMA (Vision API) ---
# Tidak butuh library tambahan — pakai openai client yang sama

# --- OCR: JALUR FALLBACK (Lokal) ---
paddlepaddle==2.6.1      # Pin exact version, jangan pakai >=
paddleocr>=2.8.0
opencv-python-headless>=4.10.0
Pillow>=10.4.0

# --- MATH & TENSORS ---
numpy==1.26.4            # WAJIB pin exact! Cegah konflik C-API dengan Paddle

# --- UTILITY ---
python-bidi>=0.4.2       # Untuk teks RTL jika diperlukan
shapely>=2.0.0           # Geometry utility untuk layout kalkulasi
```

> **PERINGATAN:** Jangan upgrade numpy ke 2.x. PaddlePaddle belum support numpy 2.x dan akan crash saat runtime dengan error C-API incompatible.

### Setup Venv (sekali saja)

```bash
# Pastikan pakai Python 3.11, BUKAN 3.12 atau 3.13
py -3.11 -m venv venv              # Windows
python3.11 -m venv venv            # Linux/Mac

# Aktivasi
venv\Scripts\activate              # Windows
source venv/bin/activate           # Linux/Mac

# Install urutan ini: numpy dulu, paddle setelah itu, baru sisanya
pip install --upgrade pip
pip install numpy==1.26.4
pip install paddlepaddle==2.6.1
pip install -r requirements.txt
```

---

## 5. Struktur Direktori (Domain-Driven)

```
ml-dicatatin/
├── core/
│   ├── __init__.py
│   ├── config.py              # Pydantic Settings — semua env var dari sini
│   └── exceptions.py          # Custom exception classes
│
├── ocr/
│   ├── __init__.py            # Export: preprocess_image, extract_text, sanitize_text
│   ├── preprocessor.py        # OpenCV: deskew, denoise, resize, sharpen
│   ├── extractor_llm.py       # JALUR UTAMA: GPT-4o Vision API
│   ├── extractor.py           # JALUR FALLBACK: PaddleOCR lokal
│   └── sanitizer.py           # LLM: normalisasi singkatan bahasa Indonesia
│
├── transform/
│   ├── __init__.py
│   ├── prompts/               # File .txt prompt — satu file per metode
│   │   ├── mind_map.txt
│   │   ├── cornell.txt
│   │   ├── boxing.txt
│   │   ├── charting.txt
│   │   ├── zettelkasten.txt
│   │   ├── sketchnoting.txt
│   │   └── feynman.txt
│   ├── schemas.py             # Pydantic schema untuk setiap metode output
│   ├── router.py              # FastAPI route definitions
│   └── transformer.py         # Core LLM caller dengan instructor
│
├── flashcard/
│   ├── __init__.py
│   ├── extractor.py           # LLM: generate Q&A pairs dari catatan
│   ├── schemas.py             # Pydantic schema untuk flashcard
│   └── sm2.py                 # Algoritma SuperMemo-2 (spaced repetition)
│
├── utils/
│   ├── __init__.py
│   └── image_utils.py         # Base64 encode/decode, resizing helper
│
├── models/
│   └── custom_rec/            # (Opsional) model PaddleOCR custom jika dilatih
│
├── tests/
│   ├── __init__.py
│   ├── sample_images/         # Minimal 5 foto catatan test
│   └── test_pipeline.py
│
├── .env                       # API keys (JANGAN commit ke Git)
├── .env.example               # Template env var (wajib ada di repo)
├── .gitignore
├── Dockerfile
├── main.py                    # Entry point FastAPI app
└── requirements.txt
```

---

## 6. Pipeline Inti: OCR & Transformasi

### 6.1 Alur Lengkap dari Gambar ke React Flow Nodes

```
[Image Bytes]
     │
     ▼
preprocessor.py
  ├── Resize (min 1000px sisi terpendek)
  ├── Denoise (fastNlMeansDenoisingColored)
  ├── Deskew (minAreaRect angle correction)
  └── Sharpen (unsharp mask kernel)
     │
     ▼ numpy array BGR
     │
     ├──► [JALUR UTAMA] extractor_llm.py
     │       └── OpenAI Vision API (gpt-4o / gpt-4o-mini)
     │           Input: base64 encoded image
     │           Output: raw text string
     │
     └──► [FALLBACK jika API error/timeout] extractor.py
              └── PaddleOCR lokal (CPU)
                  lang='en', use_angle_cls=True
                  Output: raw text string + confidence float
     │
     ▼
sanitizer.py
  └── LLM (gpt-4o-mini, temperature=0.1)
      Perbaiki: singkatan indo, typo, struktur kalimat rusak
      Output: clean_text string
     │
     ▼
transformer.py
  ├── Load prompt dari transform/prompts/{method}.txt
  ├── Inject clean_text ke dalam prompt
  ├── Call LLM dengan instructor (structured output)
  ├── Validate output dengan Pydantic schema
  └── Convert schema ke React Flow nodes + edges format
     │
     ▼
flashcard/extractor.py
  └── LLM generate Q&A dari clean_text
      Return: list of flashcard objects
     │
     ▼
[Final Response ke Backend]
{
  "raw_text": str,
  "clean_text": str,
  "nodes": [...],    ← React Flow format
  "edges": [...],    ← React Flow format
  "flashcards": [...],
  "method": str,
  "metadata": {...}
}
```

### 6.2 Logika Fallback OCR 

```python
# Di extractor atau main pipeline:
try:
    raw_text = await extract_via_llm(image_bytes)   # Jalur utama
except (APIError, TimeoutError) as e:
    logger.warning(f"LLM OCR gagal: {e}. Switching ke PaddleOCR.")
    raw_text, confidence = extract_via_paddle(preprocessed_img)  # Fallback
```

### 6.3 Kontrak Internal Antar Modul (bisa berubah flownya nanti)

```python
# preprocessor.py
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Return: BGR numpy array siap untuk OCR"""

# extractor_llm.py
async def extract_via_llm(image_bytes: bytes) -> str:
    """Return: raw text string"""

# extractor.py (PaddleOCR)
def extract_via_paddle(preprocessed_img: np.ndarray) -> tuple[str, float]:
    """Return: (raw_text, confidence_score 0.0-1.0)"""

# sanitizer.py
def sanitize_text(raw_text: str) -> str:
    """Return: clean text string"""

# transformer.py
def transform_notes(clean_text: str, method: str) -> dict:
    """Return: {"nodes": [...], "edges": [...], "method": str, "metadata": {...}}"""

# flashcard/extractor.py
def generate_flashcards(clean_text: str) -> list[dict]:
    """Return: list of {id, question, answer, difficulty}"""
```

---

## 7. Kontrak API (ML → Backend)

Ini adalah endpoint yang Backend (Laravel) panggil ke ML Service. ML Service **tidak expose ke Frontend secara langsung**.

### `POST /process` — Pipeline Utama

Endpoint terpenting. Terima gambar, return workspace penuh.

**Request:**

```
Content-Type: multipart/form-data
Body:
  - file: File (JPG/PNG, max 10MB)
  - method: string (mind_map | cornell | boxing | charting | zettelkasten | sketchnoting | feynman)
```

**Response 200:**

```json
{
  "status": "success",
  "data": {
    "raw_text": "teks mentah hasil OCR sebelum dibersihkan",
    "clean_text": "teks bersih setelah normalisasi AI",
    "method": "mind_map",
    "nodes": [
      {
        "id": "mm_root",
        "type": "mindMapRoot",
        "position": { "x": 400, "y": 200 },
        "data": { "label": "Biologi Sel" }
      }
    ],
    "edges": [
      {
        "id": "e-root-1",
        "source": "mm_root",
        "target": "mm_branch_1",
        "type": "straight",
        "style": { "stroke": "#93C5FD", "strokeWidth": 2 }
      }
    ],
    "flashcards": [
      {
        "id": "fc_uuid_1",
        "question": "Apa perbedaan Mitosis dan Meiosis?",
        "answer": "Mitosis: 2 sel diploid. Meiosis: 4 sel haploid.",
        "difficulty": 3
      }
    ],
    "metadata": {
      "ocr_engine": "llm_vision",
      "confidence_score": 0.94,
      "processing_time_seconds": 8.2,
      "warning": null
    }
  }
}
```

**Response 422 (gambar tidak bisa dibaca):**

```json
{
  "status": "error",
  "message": "Gambar terlalu buram untuk diproses. Coba foto dengan pencahayaan lebih terang."
}
```

---

### `POST /transform` — Ganti Metode Catatan

Dipanggil Backend saat user klik "Ganti Metode" di workspace. Tidak upload gambar ulang — gunakan `clean_text` yang sudah tersimpan.

**Request:**

```json
{
  "clean_text": "teks catatan yang sudah dibersihkan sebelumnya",
  "new_method": "cornell"
}
```

**Response 200:**

```json
{
  "status": "success",
  "data": {
    "method": "cornell",
    "nodes": [...],
    "edges": [],
    "flashcards": [...],
    "metadata": {
      "processing_time_seconds": 3.1
    }
  }
}
```

---

### `GET /health` — Health Check

Dipakai Docker Compose dan Backend untuk cek apakah ML service hidup.

**Response 200:**

```json
{
  "status": "ok",
  "service": "ml-dicatatin",
  "version": "1.0.0"
}
```

---

## 8. Skema Output per Metode Belajar

Ini adalah output Pydantic schema yang dihasilkan LLM sebelum dikonversi ke format React Flow. Definisikan semua di `transform/schemas.py`.

### Mind Map

```python
class MindMapNode(BaseModel):
    id: str           # "mm_root", "mm_branch_1", "mm_leaf_1_1"
    label: str        # Teks singkat di node
    level: int        # 0 = root, 1 = branch, 2 = leaf
    children: list["MindMapNode"] = []

class MindMapSchema(BaseModel):
    root: MindMapNode
    title: str        # Judul catatan untuk header kanvas
```

### Cornell Notes

```python
class CornellCue(BaseModel):
    id: str
    keyword: str      # Kata kunci singkat (kolom kiri 30%)
    row_index: int    # Untuk alignment vertikal dengan note-nya

class CornellNote(BaseModel):
    id: str
    content: str      # Teks detail (kolom kanan 70%)
    cue_id: str       # Referensi ke cue yang sejajar

class CornellSchema(BaseModel):
    title: str
    date: str         # Format: DD MMM YYYY
    cues: list[CornellCue]
    notes: list[CornellNote]
    summary: str      # Paragraf ringkasan (area bawah 200px)
```

### Boxing Method

```python
class BoxingItem(BaseModel):
    id: str
    content: str

class BoxingGroup(BaseModel):
    id: str
    topic: str        # Label di atas kotak (parent node)
    color: str        # Hex warna pastel, ex: "#FEF3C7"
    items: list[BoxingItem]

class BoxingSchema(BaseModel):
    title: str
    groups: list[BoxingGroup]
```

### Charting

```python
class ChartingSchema(BaseModel):
    title: str
    headers: list[str]           # Nama kolom, ex: ["Aspek", "Mitosis", "Meiosis"]
    rows: list[list[str]]        # Data cells, rows[i][j] = nilai cell
```

### Zettelkasten

```python
class ZettelAtom(BaseModel):
    id: str           # Kode unik: "1a", "1b", "2a", dst
    content: str      # Isi ide atomik (1-2 kalimat)
    links: list[str]  # list of id yang terhubung, ex: ["1a", "2b"]

class ZettelkastenSchema(BaseModel):
    atoms: list[ZettelAtom]
```

### Sketchnoting

```python
class SketchNode(BaseModel):
    id: str
    content: str
    importance: int   # 1-5, menentukan ukuran node
    icon: str         # Nama icon SVG sederhana: "lightbulb", "star", "arrow", "book"
    position_hint: str  # "top-left", "center", "bottom-right", dll (hint untuk layout)

class SketchnotingSchema(BaseModel):
    title: str
    nodes: list[SketchNode]
```

### Feynman Technique

```python
class FeynmanSchema(BaseModel):
    subject: str           # Nama konsep yang dipelajari
    concept: str           # Penjelasan konsep asli
    simple_explanation: str  # Penjelasan versi sederhana
    gaps: list[str]        # Bagian yang belum dipahami
    analogy: str           # Analogi untuk memudahkan pemahaman
    refinement_notes: list[str]  # Hasil riset untuk mengisi gaps
```

---

## 9. Node & Edge Spec (React Flow)

Ini adalah format akhir yang dikirim ke Frontend. ML harus menghasilkan format ini persis.

### Tipe Node per Metode

#### Mind Map

```json
{ "id": "mm_root",     "type": "mindMapRoot",   "position": {"x": 400, "y": 200}, "data": {"label": "Topik Utama"} }
{ "id": "mm_branch_1", "type": "mindMapBranch",  "position": {"x": 150, "y": 350}, "data": {"label": "Cabang 1", "depth": 1} }
{ "id": "mm_leaf_1_1", "type": "mindMapLeaf",    "position": {"x": 50,  "y": 450}, "data": {"label": "Detail", "depth": 2} }
```

Edge: `type: "straight"`, tanpa panah.

#### Cornell Notes

```json
{ "id": "cc1",  "type": "cornellCue",     "position": {"x": 20,  "y": 80},  "data": {"label": "Kata Kunci", "rowIndex": 0} }
{ "id": "cn1",  "type": "cornellNote",    "position": {"x": 230, "y": 80},  "data": {"label": "Penjelasan detail...", "cueId": "cc1"} }
{ "id": "cs1",  "type": "cornellSummary", "position": {"x": 20,  "y": 580}, "data": {"label": "Ringkasan keseluruhan..."} }
```

Edge: Tidak ada edge (keterhubungan via posisi grid).

#### Boxing Method

```json
{ "id": "bg1",   "type": "boxingGroup", "position": {"x": 20, "y": 80},  "data": {"label": "Topik A", "color": "#FEF3C7"}, "style": {"width": 300, "height": 200} }
{ "id": "bi1_1", "type": "boxingItem",  "position": {"x": 20, "y": 40},  "data": {"label": "Poin 1"}, "parentId": "bg1", "extent": "parent" }
```

Edge: Tidak ada edge (keterhubungan via parent-child).

#### Charting

```json
{ "id": "ch_header_0", "type": "chartingHeader", "position": {"x": 0,   "y": 0},   "data": {"label": "Aspek"} }
{ "id": "ch_cell_1_0", "type": "chartingCell",   "position": {"x": 0,   "y": 100}, "data": {"label": "Ukuran inti"} }
{ "id": "ch_cell_1_1", "type": "chartingCell",   "position": {"x": 150, "y": 100}, "data": {"label": "Sama seperti sel induk"} }
```

Edge: Straight edge tipis membentuk garis tabel (opsional, bisa diganti CSS grid di custom node).

#### Zettelkasten

```json
{ "id": "z_1a", "type": "zettelAtom", "position": {"x": 50,  "y": 80},  "data": {"label": "Mitosis adalah pembelahan sel...", "code": "1a"} }
{ "id": "z_1b", "type": "zettelAtom", "position": {"x": 300, "y": 200}, "data": {"label": "Menghasilkan 2 sel anak...", "code": "1b"} }
```

Edge: `type: "step"`, dengan `markerEnd: {type: "ArrowClosed"}`.

#### Sketchnoting

```json
{ "id": "sk1", "type": "sketchNode", "position": {"x": 100, "y": 50}, "data": {"label": "Konsep Utama", "icon": "lightbulb", "importance": 5} }
{ "id": "sk2", "type": "sketchNode", "position": {"x": 300, "y": 200}, "data": {"label": "Detail kecil", "icon": "star", "importance": 2} }
```

Edge: `type: "smoothstep"`, warna-warni, tanpa panah.

#### Feynman

```json
{ "id": "fy_concept",  "type": "feynmanStep", "position": {"x": 200, "y": 20},  "data": {"label": "The Concept", "content": "Fotosintesis adalah...", "step": 1} }
{ "id": "fy_simple",   "type": "feynmanStep", "position": {"x": 200, "y": 160}, "data": {"label": "Simple Explanation", "content": "Tumbuhan makan dari cahaya...", "step": 2} }
{ "id": "fy_gap",      "type": "feynmanStep", "position": {"x": 200, "y": 300}, "data": {"label": "Gap Identification", "content": "Saya belum paham: reaksi terang...", "step": 3} }
{ "id": "fy_analogy",  "type": "feynmanStep", "position": {"x": 200, "y": 440}, "data": {"label": "Analogy", "content": "Seperti pabrik yang pakai solar panel...", "step": 4} }
{ "id": "fy_ref_1",    "type": "feynmanRef",  "position": {"x": 480, "y": 300}, "data": {"label": "Hasil riset: reaksi terang terjadi di..."} }
```

Edge: `type: "bezier"`, `strokeWidth: 3`, panah besar ke bawah antar step. Ref node ke gap: `type: "straight"`.

### Kalkulasi Posisi Otomatis (Algoritma Layout)

ML harus menghitung `position.x` dan `position.y` setiap node. Jangan hardcode — generate secara algoritmik.

```python
# Contoh untuk Mind Map radial layout
import math

def calculate_mindmap_positions(root_node, canvas_center=(400, 250)):
    """
    Distribusi cabang secara radial dari center.
    Level 1: radius 200px, level 2: radius 350px
    """
    positions = {}
    positions[root_node.id] = canvas_center

    branches = root_node.children
    n = len(branches)
    for i, branch in enumerate(branches):
        angle = (2 * math.pi / n) * i - math.pi / 2  # mulai dari atas
        radius = 200
        x = canvas_center[0] + radius * math.cos(angle)
        y = canvas_center[1] + radius * math.sin(angle)
        positions[branch.id] = (round(x), round(y))

        # Level 2
        for j, leaf in enumerate(branch.children):
            leaf_angle = angle + (math.pi / 4) * (j - len(branch.children)/2)
            leaf_x = x + 150 * math.cos(leaf_angle)
            leaf_y = y + 150 * math.sin(leaf_angle)
            positions[leaf.id] = (round(leaf_x), round(leaf_y))

    return positions

# Untuk Cornell: posisi berdasarkan grid row
def calculate_cornell_positions(cues, notes, row_height=80, start_y=80):
    positions = {}
    for i, cue in enumerate(cues):
        positions[cue.id] = (20, start_y + i * row_height)
    for note in notes:
        cue_idx = next(i for i, c in enumerate(cues) if c.id == note.cue_id)
        positions[note.id] = (230, start_y + cue_idx * row_height)
    return positions
```

---

## 10. Modul Flashcard & SM-2

### Format Flashcard (Konsisten di seluruh sistem)

```python
class FlashcardSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    answer: str
    difficulty: int = Field(ge=1, le=5, default=3)
    # SM-2 fields (disimpan di Backend DB, tidak direturn saat generate awal)
    interval: int = 1          # Hari sampai review berikutnya
    easiness: float = 2.5      # Easiness factor (min 1.3)
    repetitions: int = 0       # Berapa kali sudah dijawab benar
    next_review: str = ""      # ISO datetime string
```

### Algoritma SM-2 (sm2.py)

```python
def update_schedule(interval: int, easiness: float, repetitions: int, user_rating: int) -> dict:
    """
    user_rating: 0-5
      0-2 = gagal (lupa total, ulangi dari awal)
      3   = benar tapi sulit
      4   = benar dengan usaha sedang
      5   = benar sempurna
    """
    if user_rating < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness)
        repetitions += 1

    # Update easiness factor
    easiness = easiness + 0.1 - (5 - user_rating) * (0.08 + (5 - user_rating) * 0.02)
    easiness = max(1.3, easiness)  # Batas bawah 1.3

    from datetime import datetime, timedelta
    next_review = (datetime.utcnow() + timedelta(days=interval)).isoformat()

    return {
        "interval": interval,
        "easiness": round(easiness, 2),
        "repetitions": repetitions,
        "next_review": next_review
    }
```

### Prompt Generate Flashcard

Simpan di `flashcard/prompts/generate.txt`:

```
Kamu adalah tutor akademis yang ahli membuat pertanyaan belajar aktif.

Dari catatan kuliah berikut, buat 5 hingga 10 pasangan flashcard berkualitas tinggi.

Aturan pembuatan pertanyaan:
- Pertanyaan harus menguji PEMAHAMAN, bukan hafalan mentah
- Variasikan jenis: definisi, perbandingan, penerapan, sebab-akibat
- Jawaban singkat dan padat (maksimal 3 kalimat)
- Difficulty: 1 (hafalan mudah) → 5 (analisis kompleks)
- Semua dalam Bahasa Indonesia

Output HANYA JSON array, tidak ada teks lain:
[
  {"question": "...", "answer": "...", "difficulty": 3},
  ...
]

Catatan:
{clean_text}
```

---

## 11. Konfigurasi & Environment

### `core/config.py` (Pydantic Settings — satu-satunya sumber kebenaran env var)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model_ocr: str = "gpt-4o"           # Untuk Vision OCR
    openai_model_transform: str = "gpt-4o"     # Untuk transformasi metode
    openai_model_sanitizer: str = "gpt-4o-mini"  # Hemat biaya untuk sanitasi
    openai_model_flashcard: str = "gpt-4o-mini"  # Hemat biaya untuk flashcard

    # Timeouts (detik)
    ocr_timeout: int = 30
    transform_timeout: int = 45
    flashcard_timeout: int = 30

    # OCR Config
    ocr_fallback_enabled: bool = True  # Aktifkan PaddleOCR jika LLM gagal

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### `.env.example`

```env
# OpenAI API Key — wajib ada
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx

# Model override (opsional, ada default di config.py)
OPENAI_MODEL_OCR=gpt-4o
OPENAI_MODEL_TRANSFORM=gpt-4o
OPENAI_MODEL_SANITIZER=gpt-4o-mini
OPENAI_MODEL_FLASHCARD=gpt-4o-mini

# Timeout dalam detik
OCR_TIMEOUT=30
TRANSFORM_TIMEOUT=45

# Set False jika tidak mau install PaddlePaddle
OCR_FALLBACK_ENABLED=true

# Environment
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 12. Error Handling & Response Standard

### Semua error dari ML Service harus mengikuti format ini:

```json
{
  "status": "error",
  "message": "Pesan error yang informatif dan actionable untuk user"
}
```

### `core/exceptions.py`

```python
from fastapi import HTTPException

class ImageTooBlurryError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=422,
            detail="Gambar terlalu buram. Coba foto dengan pencahayaan lebih terang dan kamera tidak bergerak."
        )

class UnsupportedFileTypeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Format file tidak didukung. Gunakan JPG atau PNG."
        )

class FileTooLargeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=413,
            detail="Ukuran file terlalu besar. Maksimal 10MB."
        )

class LLMTimeoutError(HTTPException):
    def __init__(self, stage: str):
        super().__init__(
            status_code=504,
            detail=f"AI timeout saat {stage}. Coba lagi dalam beberapa detik."
        )

class InvalidMethodError(HTTPException):
    def __init__(self, method: str):
        valid = "mind_map, cornell, boxing, charting, zettelkasten, sketchnoting, feynman"
        super().__init__(
            status_code=400,
            detail=f"Metode '{method}' tidak valid. Pilihan: {valid}"
        )
```

### Aturan Warning (bukan error, tapi perlu dikomunikasikan)

```python
# Tambahkan ke metadata response jika berlaku:
{
  "metadata": {
    "warning": "Kualitas gambar rendah (confidence: 0.52). Hasil mungkin tidak akurat."
    # atau null jika tidak ada masalah
  }
}

# Threshold warning:
# confidence < 0.60 → warning kualitas rendah
# confidence < 0.40 → raise ImageTooBlurryError
```

---

## 13. Aturan Kode & Konvensi

### Naming Convention

- **File:** `snake_case.py`
- **Class:** `PascalCase`
- **Function/Variable:** `snake_case`
- **Konstanta:** `UPPER_SNAKE_CASE`
- **Pydantic Schema:** nama diakhiri `Schema` (ex: `CornellSchema`, `MindMapSchema`)

### Wajib Ada di Setiap Fungsi

```python
async def extract_via_llm(image_bytes: bytes) -> str:
    """
    Ekstrak teks dari gambar menggunakan GPT-4o Vision API.

    Args:
        image_bytes: Raw bytes dari gambar JPG/PNG/JPEG

    Returns:
        String teks mentah hasil ekstraksi

    Raises:
        LLMTimeoutError: Jika API tidak respond dalam timeout
        ImageTooBlurryError: Jika tidak ada teks terdeteksi
    """
```

### Larangan Keras

- ❌ Jangan hardcode API key di kode. Selalu dari `get_settings()`.
- ❌ Jangan hardcode posisi node. Hitung secara algoritmik.
- ❌ Jangan buat endpoint yang bisa diakses langsung oleh Frontend (semua lewat Backend).
- ❌ Jangan commit file `.env` ke Git.
- ❌ Jangan gunakan `print()` untuk logging. Gunakan `import logging; logger = logging.getLogger(__name__)`.
- ❌ Jangan gunakan numpy >= 2.0.0 (akan konflik dengan PaddlePaddle).

### Gunakan instructor untuk Structured Output

```python
import instructor
from openai import OpenAI
from transform.schemas import CornellSchema

client = instructor.from_openai(OpenAI(api_key=settings.openai_api_key))

# Ini akan otomatis retry dan validate sampai schema terpenuhi
result = client.chat.completions.create(
    model=settings.openai_model_transform,
    response_model=CornellSchema,  # ← Magic dari instructor
    messages=[{"role": "user", "content": prompt}],
    max_retries=3
)
# result sudah berupa CornellSchema object, bukan raw string
```

---

## 14. Checklist Sebelum Submit ke Tim

### Sebelum push ke repo:

- [ ] `.env` tidak ter-commit (ada di `.gitignore`)
- [ ] `.env.example` sudah diupdate dengan semua env var baru
- [ ] Semua fungsi punya docstring
- [ ] `GET /health` endpoint return 200
- [ ] `POST /process` ditest dengan minimal 3 foto catatan berbeda
- [ ] Semua 7 metode menghasilkan output tanpa error
- [ ] Output `nodes[]` dan `edges[]` sesuai format React Flow (validasi dengan Frontend)
- [ ] `confidence_score` muncul di response metadata
- [ ] `warning` muncul saat foto kualitas rendah
- [ ] Fallback ke PaddleOCR berfungsi (test dengan `OCR_FALLBACK_ENABLED=true` dan API key salah)

### Sebelum demo ke juri:

- [ ] Docker container ML bisa start dalam < 30 detik (model PaddleOCR sudah di-cache di image)
- [ ] End-to-end dari upload foto ke render React Flow < 30 detik
- [ ] Ada minimal 1 foto catatan berantakan yang bisa didemonstrasikan
- [ ] Bisa menjelaskan setiap keputusan teknis di pipeline

---

_Dokumen ini adalah sumber kebenaran tunggal (single source of truth) untuk ML Engineer DICATAT.IN. Jika ada konflik antara dokumen ini dengan kode yang sudah ada, ikuti dokumen ini dan update kodenya._
