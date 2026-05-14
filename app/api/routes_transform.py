"""
api/routes_transform.py

Endpoint untuk ganti metode catatan dari teks yang sudah ada.
Dipanggil saat user klik "Ganti Metode" di frontend tanpa upload ulang.
"""

import logging

from fastapi import APIRouter

from api.schemas import TransformRequest, TransformResponse, TransformResponseData, TransformMetadata
from services.pipeline import retransform

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Transform"])


@router.post("/transform", response_model=TransformResponse)
async def transform_method(request: TransformRequest):
    """
    Re-transformasi teks ke metode belajar baru.
    
    - **clean_text**: Teks catatan yang sudah dibersihkan (dari response /process)
    - **new_method**: Metode baru yang ingin digunakan
    """
    # ── Delegasi ke service layer ──
    result = await retransform(
        clean_text=request.clean_text,
        new_method=request.new_method
    )

    # ── Build typed response ──
    return TransformResponse(
        data=TransformResponseData(
            method=result["method"],
            nodes=result["nodes"],
            edges=result["edges"],
            flashcards=result["flashcards"],
            metadata=TransformMetadata(**result["metadata"]),
        )
    )
