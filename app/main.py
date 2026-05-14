"""
main.py

Entry point untuk FastAPI app ml-dicatatin.
File ini HANYA bertanggung jawab untuk:
1. Membuat instance FastAPI app
2. Setup middleware & startup events
3. Registrasi routers dari api/
4. Health check endpoint

Semua business logic ada di services/ dan domain modules.
"""

from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logger import setup_logging
from api import process_router, transform_router, flashcard_router

# Inisialisasi logging terpusat (sebelum apapun)
setup_logging()

settings = get_settings()

app = FastAPI(
    title="ML DICATAT.IN",
    version=settings.service_version,
    description="Machine Learning service untuk DICATAT.IN — "
                "mengubah foto catatan menjadi catatan digital terstruktur.",
)

# Konfigurasi CORS (untuk integrasi antar container atau frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registrasi Routers ──
app.include_router(process_router)
app.include_router(transform_router)
app.include_router(flashcard_router)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint untuk Docker dan backend Laravel."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version
    }