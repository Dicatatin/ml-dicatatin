"""
api/schemas.py

Pydantic schemas untuk Request & Response di level API (HTTP layer).
Schemas ini terpisah dari domain schemas (transform/schemas.py, flashcard/schemas.py)
karena fungsinya berbeda: ini untuk contract API, bukan untuk LLM output validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Request Schemas
# -----------------------------------------------------------------------------
class TransformRequest(BaseModel):
    """Request body untuk endpoint POST /transform (ganti metode)."""
    clean_text: str = Field(..., description="Teks catatan yang sudah dibersihkan")
    new_method: str = Field(..., description="Metode baru (contoh: cornell, mind_map, boxing)")


class FlashcardRequest(BaseModel):
    """Request body untuk endpoint POST /flashcard (regenerate)."""
    clean_text: str = Field(..., description="Teks catatan yang sudah dibersihkan")


# -----------------------------------------------------------------------------
# Response Schemas
# -----------------------------------------------------------------------------
class ProcessMetadata(BaseModel):
    """Metadata hasil pemrosesan pipeline."""
    ocr_engine: str = "vision_api"
    processing_time_seconds: float = 0.0


class ProcessResponseData(BaseModel):
    """Data utama dari response /process."""
    raw_text: str
    clean_text: str
    method: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    flashcards: List[Dict[str, Any]]
    metadata: ProcessMetadata


class ProcessResponse(BaseModel):
    """Response schema untuk endpoint POST /process."""
    status: str = "success"
    data: ProcessResponseData


class TransformMetadata(BaseModel):
    """Metadata hasil re-transformasi."""
    processing_time_seconds: float = 0.0


class TransformResponseData(BaseModel):
    """Data utama dari response /transform."""
    method: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    flashcards: List[Dict[str, Any]]
    metadata: TransformMetadata


class TransformResponse(BaseModel):
    """Response schema untuk endpoint POST /transform."""
    status: str = "success"
    data: TransformResponseData


class FlashcardMetadata(BaseModel):
    """Metadata hasil generate flashcard."""
    processing_time_seconds: float = 0.0


class FlashcardResponseData(BaseModel):
    """Data utama dari response /flashcard."""
    flashcards: List[Dict[str, Any]]
    metadata: FlashcardMetadata


class FlashcardResponse(BaseModel):
    """Response schema untuk endpoint POST /flashcard."""
    status: str = "success"
    data: FlashcardResponseData
