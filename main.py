"""
main.py

Entry point untuk FastAPI app ml-dicatatin.
Menyediakan endpoint utama (/process) untuk memproses gambar menjadi workspace React Flow,
serta endpoint ganti metode (/transform) dan health check (/health).
"""

import time
import logging
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.exceptions import InvalidMethodError, UnsupportedFileTypeError, FileTooLargeError
from transform.router import router as transform_router
from transform.transformer import transform_notes
from flashcard.extractor import generate_flashcards

# Impor pipeline OCR
from ocr.preprocessor import preprocess_image
from ocr.extractor_llm import extract_text_api
from ocr.sanitizer import sanitize_text

# Inisialisasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="ML DICATAT.IN", version=settings.service_version)

# Konfigurasi CORS (untuk integrasi antar container atau frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan Router Lainnya
app.include_router(transform_router)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint untuk Docker dan backend Laravel."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version
    }


@app.post("/process")
async def process_endpoint(
    file: UploadFile = File(...), 
    method: str = Form(...)
):
    """
    Pipeline utama Aplikasi:
    Gambar -> OCR Extraction -> Text Sanitization -> 
    LLM Transformation -> Flashcard Generation -> JSON React Flow
    """
    start_time = time.time()
    
    # -------------------------------------------------------------------------
    # 1. Validasi Input
    # -------------------------------------------------------------------------
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise UnsupportedFileTypeError()
        
    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise FileTooLargeError()
        
    valid_methods = ["mind_map", "cornell", "boxing", "charting", "zettelkasten", "sketchnoting", "feynman"]
    if method not in valid_methods:
        raise InvalidMethodError(method)

    ocr_engine = "llm_vision"
    warning_msg = None

    # -------------------------------------------------------------------------
    # 2. Preprocessing & OCR Extraction
    # -------------------------------------------------------------------------
    try:
        # Panggil ekstraksi LLM OCR (Jalur utama)
        # TODO: Jika preprocessor cv2 dirasa sangat esensial sebelum masuk ke Vision API,
        # kita bisa menyelipkan preprocess_image(file_bytes) di sini.
        raw_text, confidence_score = await extract_text_api(file_bytes)
    except Exception as e:
        logger.error(f"OCR LLM Error: {e}")
        # Jika ada error dari Vision API, kita beri fallback string kosong
        # agar ditangkap oleh error 422 di bawah, kecuali ada PaddleOCR lokal.
        raw_text, confidence_score = "", 0.0
        
    if not raw_text or len(raw_text.strip()) < 5:
        raise HTTPException(
            status_code=422, 
            detail="Gambar terlalu buram atau tidak ada teks yang terdeteksi."
        )
        
    if confidence_score < settings.ocr_confidence_warning_threshold:
        warning_msg = f"Kualitas gambar rendah (confidence: {confidence_score}). Hasil mungkin tidak akurat."

    # -------------------------------------------------------------------------
    # 3. Sanitasi Teks
    # -------------------------------------------------------------------------
    # Membersihkan struktur teks, typo, dan singkatan agar lebih mudah dicerna transformer
    clean_text = sanitize_text(raw_text)
    
    # -------------------------------------------------------------------------
    # 4. Transformasi ke React Flow Nodes & Edges
    # -------------------------------------------------------------------------
    transform_result = await transform_notes(clean_text, method)
    
    # -------------------------------------------------------------------------
    # 5. Generate Flashcard Spaced Repetition (Q&A)
    # -------------------------------------------------------------------------
    try:
        flashcards = await generate_flashcards(clean_text)
    except Exception as e:
        logger.error(f"Gagal generate flashcard: {e}")
        # Tetap lanjutkan pipeline tanpa flashcard daripada user kehilangan notes-nya
        flashcards = []
        
    processing_time = round(time.time() - start_time, 2)
    
    # -------------------------------------------------------------------------
    # 6. Response Builder
    # -------------------------------------------------------------------------
    return {
        "status": "success",
        "data": {
            "raw_text": raw_text,
            "clean_text": clean_text,
            "method": method,
            "nodes": transform_result["nodes"],
            "edges": transform_result["edges"],
            "flashcards": flashcards,
            "metadata": {
                "ocr_engine": ocr_engine,
                "confidence_score": confidence_score,
                "processing_time_seconds": processing_time,
                "warning": warning_msg
            }
        }
    }