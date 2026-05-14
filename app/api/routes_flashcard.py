"""
api/routes_flashcard.py

Endpoint untuk generate ulang flashcard dari teks yang sudah ada.
Dipanggil saat user klik "Regenerate Flashcard" di frontend.
"""

import logging

from fastapi import APIRouter

from app.api.schemas import FlashcardRequest, FlashcardResponse, FlashcardResponseData, FlashcardMetadata
from app.services.pipeline import regenerate_flashcards

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Flashcard"])


@router.post("/flashcard", response_model=FlashcardResponse)
async def flashcard_regenerate(request: FlashcardRequest):
    """
    Regenerate flashcards dari teks catatan.
    
    - **clean_text**: Teks catatan yang sudah dibersihkan (dari response /process)
    """
    # ── Delegasi ke service layer ──
    result = await regenerate_flashcards(
        clean_text=request.clean_text
    )

    # ── Build typed response ──
    return FlashcardResponse(
        data=FlashcardResponseData(
            flashcards=result["flashcards"],
            metadata=FlashcardMetadata(**result["metadata"]),
        )
    )
