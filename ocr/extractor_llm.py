"""
ocr/extractor_llm.py

Modul untuk mengekstrak teks dari gambar menggunakan Vision API (GPT-5.4 Nano).
Ini adalah satu-satunya jalur OCR di branch main (tanpa engine lokal).
"""

import base64
import logging

from openai import AsyncOpenAI

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Inisialisasi klien Async OpenAI
client = AsyncOpenAI(api_key=settings.openai_api_key)


def _encode_image(image_bytes: bytes) -> str:
    """Mengubah raw bytes gambar menjadi string Base64."""
    return base64.b64encode(image_bytes).decode('utf-8')


async def extract_text_api(image_bytes: bytes) -> tuple[str, float]:
    """
    Mengirim gambar ke Vision API untuk ekstraksi teks (OCR).
    Return: (raw_text, confidence_score)
    """
    base64_image = _encode_image(image_bytes)
    
    system_prompt = (
        "Kamu adalah mesin OCR tingkat lanjut. Tugasmu HANYA mengekstrak "
        "teks dari gambar yang diberikan. Jangan tambahkan basa-basi, jangan "
        "gunakan markdown (seperti ``` atau **), jangan koreksi ejaan secara berlebihan, "
        "dan salin baris baru (newline) sesuai aslinya. "
        "Jika tidak ada teks atau gambar tidak jelas, balas HANYA dengan string kosong."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.vision_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=2000,
            temperature=0.1
        )
        
        extracted_text = response.choices[0].message.content.strip()
        confidence = 0.90 if extracted_text else 0.0
        
        return extracted_text, confidence
        
    except Exception as e:
        logger.error(f"[OCR API Error] Kegagalan memanggil Vision API: {e}")
        return "", 0.0