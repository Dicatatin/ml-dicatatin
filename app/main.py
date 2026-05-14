from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logger import setup_logging
from app.api import process_router, transform_router, flashcard_router

# Inisialisasi logging terpusat (sebelum apapun)
setup_logging()

settings = get_settings()

app = FastAPI(
    title="ML DICATAT.IN",
    version=settings.service_version,
    description="Machine Learning service untuk DICATAT.IN — "
                "mengubah foto catatan menjadi catatan digital terstruktur.",
)

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