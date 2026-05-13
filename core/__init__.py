"""
core/__init__.py

Mengekspor fungsi-fungsi utama dari submodul Core
"""

from .config import get_settings

__all__ = [
    "get_settings"
]
