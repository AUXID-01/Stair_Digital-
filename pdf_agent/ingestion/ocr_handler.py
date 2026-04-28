"""
ingestion/ocr_handler.py
Responsibility: Fallback OCR for scanned or image-only PDFs using pytesseract + pdf2image.
Inputs: PDF file path (str)
Outputs: List[ParsedPage]
Dependencies: config.py, logs/schema.py
"""
