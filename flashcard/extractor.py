"""
flashcard/extractor.py

Modul untuk mengekstrak pertanyaan-jawaban (Q&A) dari catatan bersih (clean_text)
menjadi format Flashcard menggunakan LLM.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

import instructor
from openai import AsyncOpenAI

from core.config import get_settings
from core.exceptions import LLMTimeoutError
from flashcard.schemas import FlashcardListSchema

logger = logging.getLogger(__name__)
settings = get_settings()

# Inisialisasi AsyncOpenAI dengan instructor
client = instructor.from_openai(AsyncOpenAI(api_key=settings.openai_api_key))

PROMPT_FILE = Path(__file__).parent / "prompts" / "generate.txt"


def load_prompt() -> str:
    """Membaca template prompt flashcard dari file .txt"""
    if not PROMPT_FILE.exists():
        logger.warning(f"File prompt {PROMPT_FILE} tidak ditemukan. Menggunakan fallback.")
        return "Buat 5 hingga 10 pasangan flashcard (question, answer, difficulty 1-5) dari teks: {clean_text}"
        
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


async def generate_flashcards(clean_text: str) -> List[Dict[str, Any]]:
    """
    Menghasilkan array/list dari dict flashcard menggunakan LLM
    berdasarkan catatan yang sudah dibersihkan.
    
    Args:
        clean_text: Catatan teks yang sudah dinormalisasi (hasil sanitizer)
        
    Returns:
        List of dictionaries. Tiap elemen berisi id, question, answer, 
        difficulty, interval, easiness, repetitions, next_review.
        
    Raises:
        LLMTimeoutError: Jika LLM terlalu lama merespon
        Exception: Jika instructor/OpenAI gagal validasi
    """
    prompt_template = load_prompt()
    prompt = prompt_template.replace("{clean_text}", clean_text)
    
    logger.info("Generating flashcards with LLM...")
    
    try:
        # Gunakan asyncio.wait_for untuk mengamankan dari timeout yang menggantung
        model_name = settings.model_flashcard
        structured_output = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_name,
                response_model=FlashcardListSchema,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Sedikit deterministik untuk menghindari halusinasi
                max_retries=3     # Coba 3x jika JSON schema output gagal diparse
            ),
            timeout=settings.flashcard_timeout
        )
    except asyncio.TimeoutError:
         logger.error("Timeout saat generate flashcards")
         raise LLMTimeoutError(stage="generate_flashcards")
    except Exception as e:
        logger.error(f"Error saat generate flashcards: {e}")
        raise
        
    # Mengonversi Pydantic models kembali menjadi dict standar
    # Semua default value dari SM-2 (easiness, interval, dll) akan ikut terekspor
    return [fc.model_dump() for fc in structured_output.flashcards]
