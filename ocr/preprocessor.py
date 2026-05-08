import cv2
import numpy as np


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Terima raw bytes dari upload, return numpy array BGR
    yang sudah dibersihkan dan diluruskan.
    PaddleOCR menerima BGR numpy array secara langsung.
    """
    # Decode bytes ke numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Gambar tidak bisa dibaca. Pastikan format JPG atau PNG.")

    # 1. Resize jika terlalu kecil (OCR butuh resolusi minimal)
    h, w = img.shape[:2]
    min_side = 1000
    if min(h, w) < min_side:
        scale = min_side / min(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_CUBIC)

    # 2. Denoise (kurangi noise kamera HP)
    img = cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10,
                                          templateWindowSize=7,
                                          searchWindowSize=21)

    # 3. Deskew (luruskan kemiringan halaman)
    img = _deskew(img)

    # 4. Sharpen (perjelas tepi tulisan)
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    img = cv2.filter2D(img, -1, kernel)

    return img


def _deskew(img: np.ndarray) -> np.ndarray:
    """Deteksi dan koreksi kemiringan gambar menggunakan garis horizontal."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255,
                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 10:
        return img  # tidak cukup titik untuk deskew

    angle = cv2.minAreaRect(coords)[-1]

    # Koreksi sudut
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Abaikan koreksi kecil (< 0.5 derajat) agar tidak ada distorsi
    if abs(angle) < 0.5:
        return img

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return rotated