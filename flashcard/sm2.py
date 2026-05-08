"""
flashcard/sm2.py

Implementasi algoritma SuperMemo-2 (SM-2) untuk menghitung jadwal
spaced repetition (pengulangan berjarak) dari sebuah flashcard 
berdasarkan feedback atau rating (0-5) dari user.
"""

from datetime import datetime, timedelta
from typing import Dict, Union

def update_schedule(
    interval: int, 
    easiness: float, 
    repetitions: int, 
    user_rating: int
) -> Dict[str, Union[int, float, str]]:
    """
    Menghitung jadwal review flashcard berikutnya menggunakan algoritma SM-2.
    
    Args:
        interval (int): Jumlah hari sampai review berikutnya (dari data terakhir).
        easiness (float): Easiness factor (E-factor), tingkat kemudahan kartu.
        repetitions (int): Berapa kali kartu dijawab benar berturut-turut.
        user_rating (int): Rating dari user (0 sampai 5).
            0-2 = Gagal (lupa total, harus diulangi dari awal)
            3   = Benar tapi sulit
            4   = Benar dengan usaha sedang
            5   = Benar sempurna
            
    Returns:
        Dict berisi field yang harus diupdate ke database:
        {
            "interval": int,
            "easiness": float,
            "repetitions": int,
            "next_review": str (ISO datetime)
        }
    """
    
    # Validasi rating batas (jaga-jaga input aneh dari frontend/backend)
    user_rating = max(0, min(5, user_rating))
    
    # Jika jawaban salah atau sangat sulit (rating di bawah 3)
    if user_rating < 3:
        repetitions = 0
        interval = 1
    else:
        # Jika jawaban benar, hitung interval berdasarkan repetisi berturut-turut
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness)
            
        repetitions += 1

    # Update easiness factor (E-factor)
    # Rumus SM-2: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    # dimana q adalah user_rating
    easiness = easiness + 0.1 - (5 - user_rating) * (0.08 + (5 - user_rating) * 0.02)
    
    # E-factor tidak boleh jatuh di bawah 1.3 (aturan baku SM-2)
    easiness = max(1.3, easiness)

    # Kalkulasi jadwal review berikutnya berbasis waktu UTC
    next_review_dt = datetime.utcnow() + timedelta(days=interval)
    next_review_iso = next_review_dt.isoformat()

    return {
        "interval": interval,
        "easiness": round(easiness, 2),
        "repetitions": repetitions,
        "next_review": next_review_iso
    }
