# resume_parser/extractor.py

import os
import io
import pdfplumber
import pytesseract
import fitz  # PyMuPDF
from PIL import Image


# 👉 Set Tesseract path for Windows (change if needed)
# If tesseract is in PATH already, you can comment this line.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _ocr_image_pil(image: Image.Image) -> str:
    """Run OCR on a PIL Image and return text."""
    return pytesseract.image_to_string(image)


def extract_text_from_pdf(path: str) -> str:
    """Extract text from PDF. If digital text is very low, fall back to OCR."""
    text_chunks = []

    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t.strip():
                    text_chunks.append(t)
    except Exception as e:
        print(f"[WARN] pdfplumber failed, will rely on OCR. Error: {e}")

    joined = "\n".join(text_chunks).strip()

    # If little or no text → likely scanned → use OCR
    if len(joined) < 100:
        print("[INFO] PDF looks scanned / empty. Running OCR with PyMuPDF + Tesseract...")
        joined = ocr_pdf(path)

    return joined


def ocr_pdf(path: str) -> str:
    """OCR for scanned PDFs using PyMuPDF + Tesseract."""
    text = []
    doc = fitz.open(path)
    for page in doc:
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        page_text = _ocr_image_pil(image)
        text.append(page_text)
    return "\n".join(text)


def extract_text_from_docx(path: str) -> str:
    """Extract text from a DOCX file."""
    import docx  # imported here to keep dependencies local
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_image(path: str) -> str:
    """OCR for image files (JPG/PNG)."""
    img = Image.open(path)
    return _ocr_image_pil(img)


def extract_text_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(path: str) -> str:
    """
    Main entry: detect file extension and route to correct extractor.
    Supports: PDF, DOCX, TXT, JPG, JPEG, PNG
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    elif ext in [".txt", ".text"]:
        return extract_text_from_txt(path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        return extract_text_from_image(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF, DOCX, TXT, JPG, PNG.")
