"""
core/exceptions.py

Custom exception classes untuk ML Service DICATAT.IN.
Semua error mengikuti format standar: {"status": "error", "message": "..."}
"""

from fastapi import HTTPException


class ImageTooBlurryError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=422,
            detail="Gambar terlalu buram. Coba foto dengan pencahayaan lebih terang dan kamera tidak bergerak."
        )


class UnsupportedFileTypeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Format file tidak didukung. Gunakan JPG atau PNG."
        )


class FileTooLargeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=413,
            detail="Ukuran file terlalu besar. Maksimal 10MB."
        )


class LLMTimeoutError(HTTPException):
    def __init__(self, stage: str):
        super().__init__(
            status_code=504,
            detail=f"AI timeout saat {stage}. Coba lagi dalam beberapa detik."
        )


class InvalidMethodError(HTTPException):
    def __init__(self, method: str):
        valid = "mind_map, cornell, boxing, charting, zettelkasten, sketchnoting, feynman"
        super().__init__(
            status_code=400,
            detail=f"Metode '{method}' tidak valid. Pilihan: {valid}"
        )
