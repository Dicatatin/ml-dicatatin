import os
import sys

# Trik agar script di dalam folder 'tests' bisa membaca folder 'ocr' di luarnya
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr.extractor import extract_text_paddle

# Mengamankan eksekusi kalau jiwer belum diinstall
try:
    import jiwer
except ImportError:
    print("❌ Error: Library 'jiwer' belum diinstall.")
    print("👉 Jalankan di terminal: pip install jiwer")
    sys.exit(1)

# Dictionary berisi pasangan Nama File dan Transkrip Asli (Bisa ditambah lebih dari 1 file nanti)
GROUND_TRUTH = {
    "test.jpeg" : "Research based on Academic Information System of Univ Amikom Yogyakarta.\n\nData in Academic Information system includes many things for academics that can be classified as a data or information\n\nData :\n- Bobot SKS\n- Nama\n- ID\n- Course Name\n- Departement\n- Course Assigned\n\nInformation :\n- Profile\n- Jadwal Kuliah\n- Transkrip Akademik\n- Administrasi\n- Announce\n- Materi\n\nData in Academic Information system consist of student records, course detail, financial transaction\n\nInformation is the processed output consist of academic transcript, financial summaries, and class schedule which help student, lecturer, and administration"
}

IMAGE_DIR = os.path.join("tests", "sample_images")

def run_pipeline():
    print("🔄 Memulai Pipeline Evaluasi OCR DICATAT.IN...")
    
    predictions = []
    references = []

    for filename, true_text in GROUND_TRUTH.items():
        img_path = os.path.join(IMAGE_DIR, filename)
        
        if not os.path.exists(img_path):
            print(f"⚠️ Melewati {filename}: Gambar tidak ditemukan di path -> {img_path}")
            continue

        print(f"\n📄 Memproses Gambar: {filename} ...")
        try:
            # Memanggil mesin OCR (Pastikan use_angle_cls=False di file extractor.py kamu)
            hasil_teks = extract_text_paddle(img_path)
            
            print("=== HASIL EKSTRAKSI PADDLEOCR ===")
            print(hasil_teks)
            print("=================================")
            
            # Normalisasi teks (huruf kecil semua & hilangkan spasi berlebih) agar evaluasi adil
            predictions.append(hasil_teks.lower().strip())
            references.append(true_text.lower().strip())
            
        except Exception as e:
            print(f"❌ Terjadi error pada {filename}: {e}")

    # Kalkulasi Metrik jika ada data yang berhasil diekstrak
    if predictions and references:
        wer = jiwer.wer(references, predictions)
        cer = jiwer.cer(references, predictions)
        
        print("\n" + "📊" * 15)
        print("    HASIL EVALUASI METRIK AI")
        print("📊" * 15)
        print(f"Word Error Rate (WER)      : {wer * 100:.2f}%")
        print(f"Character Error Rate (CER) : {cer * 100:.2f}%")
        print("-" * 30)
        
        if cer > 0.15:
            print("🚨 Kesimpulan: CER > 15%. Model bawaan terlalu payah untuk tulisan tangan ini.")
            print("   Rekomendasi: Jadikan ini murni fallback, dan pakai GPT-5.4 Nano untuk jalur utama.")
        else:
            print("✅ Kesimpulan: Akurasi cukup baik! Cocok dipertahankan tanpa perlu Fine-Tuning.")

if __name__ == "__main__":
    run_pipeline()