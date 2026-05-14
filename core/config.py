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
    # Vision API — Model untuk OCR
    # -------------------------------------------------------------------------
    vision_model_name: str = "gpt-5.4-nano"

    # -------------------------------------------------------------------------
    # NLP API (Biznet AI / Lainnya) — API Key untuk Transformasi & Flashcard
    # -------------------------------------------------------------------------
    llm_api_key: str | None = None
    llm_model_name: str | None = "openai/gpt-oss-20b"
    llm_base_url: str | None = "https://api.biznetgio.ai/v1"

    # -------------------------------------------------------------------------
    # Timeout (dalam detik)
    # -------------------------------------------------------------------------
    ocr_timeout: int = 30         # Timeout untuk Vision API OCR
    transform_timeout: int = 45   # Timeout untuk transformasi metode
    flashcard_timeout: int = 30   # Timeout untuk generate flashcard

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
        "Settings loaded | env=%s | vision_model=%s | llm_model=%s",
        settings.app_env,
        settings.vision_model_name,
        settings.llm_model_name,
    )
    return settings
