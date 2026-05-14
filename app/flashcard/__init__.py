"""
flashcard/__init__.py

Mengekspor fungsi-fungsi utama dari submodul Flashcard 
agar lebih mudah di-import oleh sistem luar.
"""

from .extractor import generate_flashcards
from .sm2 import update_schedule

__all__ = [
    "generate_flashcards",
    "update_schedule"
]
