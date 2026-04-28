"""
ingestion/table_extractor.py
Responsibility: Detect and extract tables from PDF pages using pdfplumber.
Inputs: PDF file path (str), page number (int)
Outputs: List[dict] — each dict is one extracted table as row/column data
Dependencies: config.py, logs/schema.py
"""
