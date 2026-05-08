import os
import base64
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Muat variabel dari .env
load_dotenv()

# Inisialisasi klien Async OpenAI (sangat penting agar FastAPI tidak terblokir)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VISION_MODEL = os.getenv("VISION_MODEL_NAME", "gpt-5.4-nano")

def _encode_image(image_bytes: bytes) -> str:
    """Mengubah raw bytes gambar menjadi string Base64."""
    return base64.b64encode(image_bytes).decode('utf-8')

async def extract_text_api(image_bytes: bytes) -> tuple[str, float]:
    """
    Mengirim gambar ke GPT-5.4 Nano untuk ekstraksi teks (OCR).
    Return: (raw_text, confidence_score)
    """
    base64_image = _encode_image(image_bytes)
    
    # Prompting adalah kunci! Kita harus membungkam LLM agar tidak cerewet.
    system_prompt = (
        "Kamu adalah mesin OCR tingkat lanjut. Tugasmu HANYA mengekstrak "
        "teks dari gambar yang diberikan. Jangan tambahkan basa-basi, jangan "
        "gunakan markdown (seperti ``` atau **), jangan koreksi ejaan secara berlebihan, "
        "dan salin baris baru (newline) sesuai aslinya. "
        "Jika tidak ada teks atau gambar tidak jelas, balas HANYA dengan string kosong."
    )

    try:
        response = await client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high" # Gunakan 'high' agar model bisa membaca tulisan kecil/miring
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1 # Suhu rendah = tidak halusinasi, murni deterministik
        )
        
        extracted_text = response.choices[0].message.content.strip()
        
        # Karena LLM API tidak memberikan skor confidence per karakter seperti PaddleOCR,
        # kita pukul rata confidence 0.99 jika berhasil mengembalikan teks.
        confidence = 0.90 if extracted_text else 0.0
        
        return extracted_text, confidence
        
    except Exception as e:
        print(f"[OCR API Error] Kegagalan memanggil Vision API: {str(e)}")
        # Jika gagal, kembalikan string kosong agar sistem bisa memicu fallback ke PaddleOCR
        return "", 0.0