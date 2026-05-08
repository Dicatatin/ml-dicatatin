"""
utils/image_utils.py

Berisi utilitas untuk manipulasi gambar dasar, khususnya konversi
format byte ke OpenCV (numpy array), Pillow, dan string Base64 yang
sangat dibutuhkan oleh GPT-4o Vision API.
"""

import base64
import io
import logging
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Mengubah raw image bytes menjadi string Base64.
    Digunakan sebagai payload untuk dikirim ke GPT-4o Vision API.
    
    Args:
        image_bytes: Raw bytes dari gambar.
        
    Returns:
        String Base64 utf-8.
    """
    return base64.b64encode(image_bytes).decode('utf-8')

def decode_base64_to_image(base64_str: str) -> bytes:
    """
    Mengubah string Base64 kembali menjadi raw image bytes.
    """
    return base64.b64decode(base64_str)

def bytes_to_numpy_image(image_bytes: bytes) -> np.ndarray:
    """
    Mengubah raw bytes (misal dari UploadFile FastAPI) menjadi numpy array (format BGR).
    Digunakan sebagai input untuk pipeline Preprocessing OpenCV dan PaddleOCR.
    
    Args:
        image_bytes: Raw bytes gambar JPG/PNG.
        
    Returns:
        Numpy array (H, W, 3) dalam format warna BGR OpenCV.
        
    Raises:
        ValueError: Jika format bytes gambar tidak dikenali / rusak.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img_cv2 is None:
        raise ValueError("Gagal decode image bytes ke Numpy Array. Mungkin format file tidak didukung.")
        
    return img_cv2

def numpy_image_to_bytes(img_cv2: np.ndarray, ext: str = '.jpg') -> bytes:
    """
    Mengubah gambar numpy array OpenCV (BGR) kembali menjadi raw bytes.
    Sangat berguna jika setelah gambar di-denoise/deskew di OpenCV, kita ingin
    mengirim gambar yang sudah 'bersih' ke Vision API (membutuhkan konversi ini).
    
    Args:
        img_cv2: Gambar numpy array (BGR).
        ext: Ekstensi output encoding (default: '.jpg').
        
    Returns:
        Encoded image bytes.
    """
    success, encoded_img = cv2.imencode(ext, img_cv2)
    if not success:
        logger.error("Gagal melakukan encode OpenCV image ke bytes.")
        raise ValueError("Image encoding failed")
        
    return encoded_img.tobytes()

def numpy_image_to_base64(img_cv2: np.ndarray, ext: str = '.jpg') -> str:
    """
    Shortcut untuk mengonversi gambar Numpy array (OpenCV BGR) 
    langsung menjadi string Base64.
    """
    img_bytes = numpy_image_to_bytes(img_cv2, ext)
    return encode_image_to_base64(img_bytes)

def get_image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    """
    Mendapatkan resolusi dimensi (width, height) dari raw bytes secara efisien 
    menggunakan library Pillow. Berguna untuk pengecekan validasi ukuran minimal.
    
    Args:
        image_bytes: Raw bytes gambar.
        
    Returns:
        Tuple (width, height).
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            return img.width, img.height
    except Exception as e:
        logger.error(f"Gagal membaca metadata dimensi gambar dengan Pillow: {e}")
        raise ValueError("Format gambar tidak valid.")
