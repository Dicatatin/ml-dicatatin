"""
flashcard/schemas.py

Pydantic schemas untuk modul Flashcard dan sistem spaced repetition (SM-2).
Digunakan sebagai response model ketika instructor mengekstrak list 
pertanyaan-jawaban dari catatan menggunakan LLM.
"""

import uuid
from typing import List

from pydantic import BaseModel, Field

class FlashcardSchema(BaseModel):
    """
    Representasi dari satu buah kartu flashcard beserta 
    metadata algoritma SM-2 (Spaced Repetition).
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="Unique UUID untuk flashcard"
    )
    question: str = Field(
        description="Pertanyaan yang menguji pemahaman, bukan sekadar hafalan mentah"
    )
    answer: str = Field(
        description="Jawaban singkat dan padat (maksimal 3 kalimat)"
    )
    difficulty: int = Field(
        ge=1, le=5, default=3, 
        description="Tingkat kesulitan: 1 (hafalan mudah) hingga 5 (analisis kompleks)"
    )
    
    # -------------------------------------------------------------------------
    # SM-2 Spaced Repetition Fields
    # -------------------------------------------------------------------------
    # Field-field di bawah ini diatur default-nya di sini. Saat flashcard 
    # baru digenerate oleh AI, nilainya akan mengikuti default.
    # Nilai-nilai ini nantinya di-update secara berkala (direkam di PostgreSQL 
    # Laravel backend) setelah user me-review dan memberikan rating skor.
    
    interval: int = Field(
        default=1, 
        description="Jumlah hari sampai flashcard perlu direview berikutnya"
    )
    easiness: float = Field(
        default=2.5, ge=1.3, 
        description="Easiness factor algoritma SM-2 (tidak boleh di bawah 1.3)"
    )
    repetitions: int = Field(
        default=0, 
        description="Jumlah run berturut-turut flashcard ini dijawab dengan benar"
    )
    next_review: str = Field(
        default="", 
        description="ISO datetime string untuk jadwal review berikutnya"
    )


class FlashcardListSchema(BaseModel):
    """
    Wrapper array untuk memaksa output LLM berupa list of flashcards
    melalui library Instructor.
    """
    flashcards: List[FlashcardSchema] = Field(
        description="Daftar pasangan Q&A berkualitas tinggi yang diekstrak dari catatan"
    )
