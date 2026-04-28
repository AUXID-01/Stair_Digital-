"""
ingestion/loader.py
Responsibility: Validate uploaded PDF and route it to the correct parser based on type.
Inputs: PDF file path (str)
Outputs: List[ParsedPage]
Dependencies: ingestion/parser.py, ingestion/ocr_handler.py, config.py,logs/schema.py
"""

import os
import fitz
from logs.logger import get_logger

log = get_logger("ingestion.loader")

def load_pdf(pdf_path: str) -> dict:
    """
    Validates the PDF file and returns path + metadata.
    Does NOT parse the PDF.
    """
    # 1. Check if file exists
    if not os.path.exists(pdf_path):
        log.error("file_not_found", path=pdf_path)
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # 2. Check extension
    if not pdf_path.lower().endswith(".pdf"):
        log.error("invalid_extension", path=pdf_path)
        raise ValueError(f"Extension is not .pdf: {pdf_path}")

    # 3. Check file size
    file_size = os.path.getsize(pdf_path)
    if file_size == 0:
        log.error("empty_file", path=pdf_path)
        raise ValueError(f"File is empty: {pdf_path}")

    # 4. Log validation
    size_kb = file_size / 1024
    log.info("pdf_load_start", path=pdf_path, size_kb=round(size_kb, 2))

    metadata = {
        "path": pdf_path,
        "filename": os.path.basename(pdf_path),
        "size_kb": round(size_kb, 2)
    }

    log.info("pdf_load_complete", path=pdf_path)
    return metadata
