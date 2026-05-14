import time
import logging
from typing import Any, Dict, List

from app.core.exceptions import InvalidMethodError
from app.ocr.extractor_llm import extract_text_api
from app.ocr.sanitizer import sanitize_text
from app.transform.transformer import transform_notes
from app.flashcard.extractor import generate_flashcards

logger = logging.getLogger(__name__)

# Daftar metode yang valid (single source of truth)
VALID_METHODS = [
    "mind_map", "cornell", "boxing", "charting",
    "zettelkasten", "sketchnoting", "feynman"
]


def validate_method(method: str) -> None:
    """Validasi apakah metode belajar yang dipilih valid."""
    if method not in VALID_METHODS:
        raise InvalidMethodError(method)


async def _generate_flashcards_safe(clean_text: str) -> List[Dict[str, Any]]:
    """
    Wrapper generate flashcards dengan graceful fallback.
    Kalau gagal, return list kosong agar user tetap dapat catatan.
    """
    try:
        return await generate_flashcards(clean_text)
    except Exception as e:
        logger.error(f"Gagal generate flashcard: {e}")
        return []


async def process_image(
    file_bytes: bytes,
    method: str
) -> Dict[str, Any]:
    """
    Pipeline utama: Gambar → OCR → Sanitize → Transform → Flashcard.
    
    Args:
        file_bytes: Raw bytes dari gambar yang di-upload
        method: Metode belajar (mind_map, cornell, boxing, dll.)
        
    Returns:
        Dict berisi raw_text, clean_text, method, nodes, edges, 
        flashcards, dan metadata.
        
    Raises:
        InvalidMethodError: Jika metode tidak valid
        HTTPException(422): Jika OCR gagal mendeteksi teks
        LLMTimeoutError: Jika LLM timeout saat transformasi
    """
    start_time = time.time()
    validate_method(method)

    # Step 1: OCR via Vision API
    raw_text = await _extract_text(file_bytes)

    # Step 2: Sanitasi teks
    clean_text = sanitize_text(raw_text)

    # Step 3: Transform + Flashcard (bisa dijalankan paralel di masa depan)
    transform_result = await transform_notes(clean_text, method)
    flashcards = await _generate_flashcards_safe(clean_text)

    processing_time = round(time.time() - start_time, 2)

    return {
        "raw_text": raw_text,
        "clean_text": clean_text,
        "method": method,
        "nodes": transform_result["nodes"],
        "edges": transform_result["edges"],
        "flashcards": flashcards,
        "metadata": {
            "ocr_engine": "vision_api",
            "processing_time_seconds": processing_time,
        }
    }


async def retransform(
    clean_text: str,
    new_method: str
) -> Dict[str, Any]:
    """
    Re-transformasi teks yang sudah ada ke metode baru.
    Dipanggil saat user klik "Ganti Metode" di frontend.
    
    Bedanya dengan process_image():
    - Tidak ada OCR (teks sudah tersedia)
    - Tidak perlu validasi file
    - Lebih cepat karena skip langkah OCR + sanitasi
    
    Args:
        clean_text: Teks catatan yang sudah dibersihkan
        new_method: Metode baru yang dipilih user
        
    Returns:
        Dict berisi method, nodes, edges, flashcards, dan metadata.
    """
    start_time = time.time()
    validate_method(new_method)

    # Transform ke metode baru
    transform_result = await transform_notes(clean_text, new_method)
    flashcards = await _generate_flashcards_safe(clean_text)

    processing_time = round(time.time() - start_time, 2)

    metadata = transform_result.get("metadata", {})
    metadata["processing_time_seconds"] = processing_time

    return {
        "method": new_method,
        "nodes": transform_result["nodes"],
        "edges": transform_result["edges"],
        "flashcards": flashcards,
        "metadata": metadata,
    }


async def _extract_text(file_bytes: bytes) -> str:
    """
    Wrapper OCR extraction dengan error handling terpusat.
    
    Raises:
        HTTPException(422): Jika tidak ada teks terdeteksi
    """
    from fastapi import HTTPException

    try:
        raw_text = await extract_text_api(file_bytes)
    except Exception as e:
        logger.error(f"OCR Vision API Error: {e}")
        raw_text = ""

    if not raw_text or len(raw_text.strip()) < 5:
        raise HTTPException(
            status_code=422,
            detail="Gambar terlalu buram atau tidak ada teks yang terdeteksi."
        )

    return raw_text


async def regenerate_flashcards(
    clean_text: str
) -> Dict[str, Any]:
    """
    Regenerate flashcards dari teks yang sudah ada.
    Dipanggil saat user klik "Regenerate Flashcard" di frontend.
    
    Args:
        clean_text: Teks catatan yang sudah dibersihkan
        
    Returns:
        Dict berisi flashcards, dan metadata.
    """
    start_time = time.time()
    
    flashcards = await _generate_flashcards_safe(clean_text)

    processing_time = round(time.time() - start_time, 2)

    return {
        "flashcards": flashcards,
        "metadata": {
            "processing_time_seconds": processing_time,
        }
    }
