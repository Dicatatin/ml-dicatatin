"""
ocr/__init__.py

Mengekspor fungsi-fungsi utama dari submodul OCR 
agar lebih mudah dan rapi di-import dari luar modul (misalnya oleh main.py).
"""

from .preprocessor import preprocess_image
from .extractor_llm import extract_text_api
from .extractor import extract_text_paddle
from .sanitizer import sanitize_text

__all__ = [
    "preprocess_image",
    "extract_text_api",
    "extract_via_paddle",
    "sanitize_text"
]
