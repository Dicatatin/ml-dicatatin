"""
transform/router.py

Mendefinisikan endpoint FastAPI untuk fitur Transform (Ganti Metode).
Endpoint ini digunakan ketika user ingin mengubah metode catatan 
dari teks yang sudah ada (clean_text) tanpa harus upload/OCR gambar ulang.
"""

import time
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from transform.transformer import transform_notes
from flashcard.extractor import generate_flashcards

router = APIRouter(prefix="/transform", tags=["Transform"])

# -----------------------------------------------------------------------------
# Schemas for Request & Response
# -----------------------------------------------------------------------------
class TransformRequest(BaseModel):
    clean_text: str = Field(..., description="Teks catatan yang sudah dibersihkan")
    new_method: str = Field(..., description="Metode baru (contoh: cornell, mind_map, boxing)")

class TransformResponseData(BaseModel):
    method: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    flashcards: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class TransformResponse(BaseModel):
    status: str = "success"
    data: TransformResponseData

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@router.post("", response_model=TransformResponse)
async def transform_method(request: TransformRequest):
    """
    Ganti metode catatan menggunakan clean_text yang sudah ada.
    Dipanggil dari Backend Laravel saat user klik "Ganti Metode" di frontend.
    """
    start_time = time.time()
    
    # Panggil core LLM transformer (akan melempar InvalidMethodError/LLMTimeoutError jika gagal)
    result = await transform_notes(clean_text=request.clean_text, method=request.new_method)
    
    # Panggil modul flashcard/extractor.py untuk mengenerate Q&A baru
    try:
        flashcards = await generate_flashcards(request.clean_text)
    except Exception as e:
        # Jika gagal, fallback ke list kosong agar user tetap mendapat UI catatan
        flashcards = []
    
    processing_time = round(time.time() - start_time, 2)
    
    metadata = result.get("metadata", {})
    metadata["processing_time_seconds"] = processing_time

    return TransformResponse(
        status="success",
        data=TransformResponseData(
            method=request.new_method,
            nodes=result["nodes"],
            edges=result["edges"],
            flashcards=flashcards,
            metadata=metadata
        )
    )
