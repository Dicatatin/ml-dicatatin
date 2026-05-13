# """
# ocr/extractor.py

# Modul fallback untuk melakukan ekstraksi teks (OCR) secara lokal menggunakan PaddleOCR.
# Hanya akan dieksekusi jika LLM Vision API mengalami kegagalan/timeout
# dan variabel OCR_FALLBACK_ENABLED=true di konfigurasi.
# """

# import logging
# import numpy as np

# # Lazy loading PaddleOCR untuk menghemat memori jika tidak dipanggil
# _paddle_ocr_instance = None

# logger = logging.getLogger(__name__)

# def _get_ocr_instance():
#     """
#     Singleton pattern untuk menginisialisasi model PaddleOCR hanya 
#     saat dibutuhkan pertama kali (lazy initialization).
#     Menggunakan CPU secara default agar hemat resource.
#     """
#     global _paddle_ocr_instance
#     if _paddle_ocr_instance is None:
#         try:
#             from paddleocr import PaddleOCR
#             # Inisialisasi: lang='en' cukup untuk teks alfabet latin bahasa Indonesia.
#             # use_angle_cls=True agar orientasi rotasi otomatis diperbaiki.
#             _paddle_ocr_instance = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
#             logger.info("PaddleOCR model berhasil dimuat di memori.")
#         except ImportError:
#             logger.error("Library PaddleOCR tidak terinstall. Pastikan paddlepaddle dan paddleocr terinstall.")
#             raise
#     return _paddle_ocr_instance

# def extract_via_paddle(preprocessed_img: np.ndarray) -> tuple[str, float]:
#     """
#     Mengekstrak teks dari gambar BGR Numpy Array menggunakan PaddleOCR.
    
#     Args:
#         preprocessed_img: Numpy array BGR (hasil OpenCV preprocessor)
        
#     Returns:
#         tuple (raw_text: str, confidence_score: float [0.0 - 1.0])
#     """
#     try:
#         ocr = _get_ocr_instance()
        
#         logger.info("Memulai ekstraksi teks lokal menggunakan PaddleOCR...")
#         # Lakukan OCR ke numpy array gambar
#         result = ocr.ocr(preprocessed_img, cls=True)
        
#         # Jika tidak ada hasil
#         if not result or result[0] is None:
#             return "", 0.0
            
#         extracted_lines = []
#         confidences = []
        
#         # Parse output dari PaddleOCR
#         # Struktur data result: [[ [koordinat], ('teks', confidence) ], ...]
#         for line in result[0]:
#             text_tuple = line[1]
#             text = text_tuple[0]
#             confidence = float(text_tuple[1])
            
#             extracted_lines.append(text)
#             confidences.append(confidence)
            
#         # Gabungkan semua baris menjadi satu teks dengan spasi/newline
#         raw_text = "\n".join(extracted_lines)
        
#         # Rata-rata confidence (jika ada)
#         mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
#         return raw_text, round(mean_confidence, 2)
        
#     except Exception as e:
#         logger.error(f"Gagal memproses gambar dengan PaddleOCR: {e}")
#         return "", 0.0



# =============================

from paddleocr import PaddleOCR
import logging

# Opsional: Mematikan log bawaan PaddleOCR yang sangat berisik di terminal
logging.getLogger("ppocr").setLevel(logging.WARNING)

# 1. INISIALISASI MODEL (Hanya dilakukan SATU KALI saat server/skrip menyala)
# Jika kamu belum mendownload modelnya, skrip ini akan otomatis mendownload model default dari internet
print("⏳ Memuat model PaddleOCR ke dalam memori...")
ocr_engine = PaddleOCR(use_angle_cls=False, lang="en", enable_mkldnn=False) # Pakai 'en' untuk alfabet latin biasa

def extract_text_paddle(image_path: str) -> str:
    """
    Mengekstrak teks dari gambar menggunakan mesin PaddleOCR.
    """
    # 2. MELAKUKAN PREDIKSI PADA GAMBAR
    # Di sinilah image_path dimasukkan, BUKAN saat inisialisasi model
    result = ocr_engine.ocr(image_path)
    
    extracted_text = ""
    
    # 3. PARSING HASIL (Output PaddleOCR itu nested list yang cukup dalam)
    # Struktur result: [[[[x,y], [x,y], [x,y], [x,y]], ('Teksnya', confidence_score)], ...]
    if result and result[0]:
        for line in result[0]:
            # Ambil teksnya saja (index 1 adalah tuple (teks, skor), index 0 dari tuple adalah teksnya)
            text = line[1][0] 
            extracted_text += text + "\n"
            
    return extracted_text.strip()

# Blok ini hanya berjalan jika kamu mengeksekusi file ini langsung (untuk testing cepat)
if __name__ == "__main__":
    import os
    # Pastikan file ini benar-benar ada di foldermu
    test_img = os.path.join("..", "tests", "sample_images", "test.jpeg") 
    print(extract_text_paddle(test_img))