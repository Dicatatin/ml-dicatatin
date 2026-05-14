"""
api/__init__.py

Mengekspor router-router API untuk diregistrasi di main.py.
"""

from .routes_process import router as process_router
from .routes_transform import router as transform_router
from .routes_flashcard import router as flashcard_router

__all__ = [
    "process_router",
    "transform_router",
    "flashcard_router",
]
