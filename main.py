import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
import fitz  # PyMuPDF

# Import dari pipeline OCR kita
from ocr.preprocessor import preprocess_image
from ocr.extractor_llm import extract_text_api # <-- Pakai mesin API yang baru
from ocr.sanitizer import sanitize_text

app = FastAPI()

async def process_single_image_api(image_bytes: bytes) -> tuple[str, float]:
    # Tetap lewat preprocessor (deskew) agar API lebih mudah membacanya
    preprocessed_img = preprocess_image(image_bytes)
    
    # Convert numpy array balik ke JPG bytes untuk dikirim ke API
    import cv2
    _, buffer = cv2.imencode('.jpg', preprocessed_img)
    encoded_bytes = buffer.tobytes()
    
    # AWAIT pemanggilan API
    raw_text, confidence = await extract_text_api(encoded_bytes)
    return raw_text, confidence

async def process_pdf_api(pdf_bytes: bytes) -> tuple[str, float]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    digital_text = ""
    for page in doc:
        digital_text += page.get_text() + "\n"
    doc.close()

    if len(digital_text.strip()) > 50:
        return digital_text.strip(), 1.0
        
    # Fallback ke Scanned PDF via API
    images = convert_from_bytes(pdf_bytes, dpi=200, fmt="jpeg", first_page=1, last_page=5)
    all_text = []
    
    for img in images:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        
        # Eksekusi API per halaman
        raw_text, _ = await process_single_image_api(img_byte_arr.getvalue())
        all_text.append(raw_text)

    combined_text = "\n\n".join(all_text)
    return combined_text, 0.99 if combined_text.strip() else 0.0


@app.post("/ocr-api-test")
async def ocr_endpoint(file: UploadFile = File(...)):
    file_bytes = await file.read()
    
    try:
        if file.content_type == "application/pdf":
            raw_text, confidence = await process_pdf_api(file_bytes)
        else:
            raw_text, confidence = await process_single_image_api(file_bytes)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses file: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Tidak ada teks yang dapat diekstrak.")

    # Bersihkan sisa-sisa halusinasi teks jika ada
    clean_text = sanitize_text(raw_text)

    return {
        "status": "success",
        "engine": "gpt-5.4-nano",
        "raw_ocr": raw_text,
        "clean_text": clean_text,
        "confidence_score": confidence
    }