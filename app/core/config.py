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
    # OpenAI — API Key (WAJIB ada, digunakan untuk semua LLM call)
    # -------------------------------------------------------------------------
    openai_api_key: str

    # -------------------------------------------------------------------------
    # Model per stage pipeline
    # -------------------------------------------------------------------------
    model_ocr: str = "gpt-4o-mini"       # Vision OCR (ekstraksi teks dari gambar)
    model_transform: str = "gpt-4o-mini"  # Transformasi metode belajar
    model_flashcard: str = "gpt-4o-mini"  # Generate flashcard

    # -------------------------------------------------------------------------
    # Timeout (dalam detik)
    # -------------------------------------------------------------------------
    ocr_timeout: int = 30         # Timeout untuk Vision API OCR
    transform_timeout: int = 60   # Timeout untuk transformasi metode
    flashcard_timeout: int = 60   # Timeout untuk generate flashcard

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
        "Settings loaded | env=%s | ocr=%s | transform=%s | flashcard=%s",
        settings.app_env,
        settings.model_ocr,
        settings.model_transform,
        settings.model_flashcard,
    )
    return settings
