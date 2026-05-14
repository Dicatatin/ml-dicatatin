"""
api/routes_process.py

Endpoint untuk pipeline utama: Upload gambar → proses → React Flow JSON.
Route handler ini TIPIS — hanya validasi input HTTP lalu delegasi ke service layer.
"""

import logging

from fastapi import APIRouter, UploadFile, File, Form

from app.core.config import get_settings
from app.core.exceptions import UnsupportedFileTypeError, FileTooLargeError
from app.api.schemas import ProcessResponse, ProcessResponseData, ProcessMetadata
from app.services.pipeline import process_image

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Process"])


@router.post("/process", response_model=ProcessResponse)
async def process_endpoint(
    file: UploadFile = File(...),
    method: str = Form(...)
):
    """
    Pipeline utama: Gambar → OCR → Sanitize → Transform → Flashcard → JSON.
    
    - **file**: Gambar catatan (JPG/PNG, maks 10MB)
    - **method**: Metode belajar (mind_map, cornell, boxing, charting, 
      zettelkasten, sketchnoting, feynman)
    """
    # ── Validasi HTTP-level (file type & size) ──
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise UnsupportedFileTypeError()

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise FileTooLargeError()

    # ── Delegasi ke service layer ──
    result = await process_image(file_bytes=file_bytes, method=method)

    # ── Build typed response ──
    return ProcessResponse(
        data=ProcessResponseData(
            raw_text=result["raw_text"],
            clean_text=result["clean_text"],
            method=result["method"],
            nodes=result["nodes"],
            edges=result["edges"],
            flashcards=result["flashcards"],
            metadata=ProcessMetadata(**result["metadata"]),
        )
    )
