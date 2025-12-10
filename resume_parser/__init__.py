# resume_parser/__init__.py

from .extractor import extract_text
from .nlp import build_structured_data


def parse_resume(path: str) -> dict:
    """
    High-level function used by app.py:
    1. Extract raw text from file (PDF/DOCX/TXT/Image)
    2. Run NLP pipeline to map to schema
    """
    text = extract_text(path)
    return build_structured_data(text)
