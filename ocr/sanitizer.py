"""
ocr/sanitizer.py

Menggunakan LLM untuk membersihkan teks mentah hasil OCR (memperbaiki typo, 
singkatan, dan formatting) sebelum masuk ke proses transformasi.
"""

def sanitize_text(raw_text: str) -> str:
    """
    Membersihkan teks raw hasil OCR. 
    Saat ini versi dummy/stub. Nanti akan diimplementasikan 
    pemanggilan LLM (gpt-4o-mini) sesuai blueprint.
    """
    if not raw_text:
        return ""
    # TODO: Implementasikan LLM sanitization
    return raw_text.strip()
