"""
core/config.py

Satu-satunya sumber kebenaran untuk semua konfigurasi dan environment variable.
Semua modul harus mengambil config dari sini via get_settings().

Penggunaan:
    from core.config import get_settings
    settings = get_settings()
    api_key = settings.openai_api_key
"""

import logging
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Konfigurasi aplikasi ml-dicatatin.

    Semua nilai diambil dari environment variable atau file .env.
    Nama env var bersifat case-insensitive (APP_ENV = app_env).
    """

    # -------------------------------------------------------------------------
    # OpenAI — API Key (WAJIB ada)
    # -------------------------------------------------------------------------
    openai_api_key: str

    # -------------------------------------------------------------------------
    # NLP API (Biznet AI / Lainnya) — API Key untuk Transformasi & Flashcard
    # -------------------------------------------------------------------------
    llm_api_key: str | None = None
    llm_model_name: str | None = None
    llm_base_url: str | None = None

    # Model per stage pipeline
    openai_model_ocr: str = "gpt-4o"          # Vision OCR (jalur utama)
    openai_model_transform: str = "gpt-4o"    # Transformasi metode belajar (fallback)
    openai_model_sanitizer: str = "gpt-4o-mini"  # Sanitasi teks (hemat biaya)
    openai_model_flashcard: str = "gpt-4o-mini"  # Generate flashcard (hemat biaya)

    # -------------------------------------------------------------------------
    # Timeout (dalam detik)
    # -------------------------------------------------------------------------
    ocr_timeout: int = 30         # Timeout untuk LLM Vision OCR
    transform_timeout: int = 45   # Timeout untuk transformasi metode
    flashcard_timeout: int = 30   # Timeout untuk generate flashcard

    # -------------------------------------------------------------------------
    # OCR Config
    # -------------------------------------------------------------------------
    ocr_fallback_enabled: bool = True  # Aktifkan PaddleOCR jika LLM OCR gagal

    # Threshold untuk evaluasi confidence PaddleOCR
    ocr_confidence_warning_threshold: float = 0.60   # Di bawah ini → warning
    ocr_confidence_error_threshold: float = 0.40     # Di bawah ini → ImageTooBlurryError

    # -------------------------------------------------------------------------
    # Upload Limits
    # -------------------------------------------------------------------------
    max_upload_size_mb: int = 10  # Ukuran maksimal file upload (MB)

    @property
    def max_upload_size_bytes(self) -> int:
        """Konversi max_upload_size_mb ke bytes untuk validasi."""
        return self.max_upload_size_mb * 1024 * 1024

    # -------------------------------------------------------------------------
    # App & Logging
    # -------------------------------------------------------------------------
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # -------------------------------------------------------------------------
    # Service Info (untuk /health endpoint)
    # -------------------------------------------------------------------------
    service_name: str = "ml-dicatatin"
    service_version: str = "1.0.0"

    # -------------------------------------------------------------------------
    # Pydantic Settings Config
    # -------------------------------------------------------------------------
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Abaikan env var yang tidak terdefinisi di sini
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Return instance Settings yang di-cache (singleton).

    Menggunakan lru_cache sehingga .env hanya dibaca sekali saat startup.
    Untuk testing, panggil get_settings.cache_clear() lalu override env var.

    Returns:
        Settings: Instance konfigurasi aplikasi.

    Raises:
        ValidationError: Jika OPENAI_API_KEY tidak ditemukan di environment.
    """
    settings = Settings()  # type: ignore[call-arg]
    logger.info(
        "Settings loaded | env=%s | ocr_model=%s | transform_model=%s | fallback=%s",
        settings.app_env,
        settings.openai_model_ocr,
        settings.openai_model_transform,
        settings.ocr_fallback_enabled,
    )
    return settings
