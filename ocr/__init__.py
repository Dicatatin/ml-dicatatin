"""
ocr/__init__.py

Mengekspor fungsi-fungsi utama dari submodul OCR (API-only, tanpa engine lokal).
"""

from .extractor_llm import extract_text_api
from .sanitizer import sanitize_text

__all__ = [
    "extract_text_api",
    "sanitize_text",
]
