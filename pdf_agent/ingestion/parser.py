"""
ingestion/parser.py
Responsibility: Extract raw text and block-level structure from PDF pages using PyMuPDF.
Inputs: PDF file path (str)
Outputs: List[ParsedPage]
Dependencies: config.py, logs/schema.py
"""

import os
import fitz
from typing import List
from logs.logger import get_logger
from logs.schema import ParsedPage, ParsedDocument

log = get_logger("ingestion.parser")

def parse_pdf(pdf_path: str) -> ParsedDocument:
    """
    Parses a PDF file into a ParsedDocument object using PyMuPDF (fitz).
    """
    if not os.path.exists(pdf_path):
        log.error("pdf_not_found", path=pdf_path)
        raise ValueError(f"PDF file not found: {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        log.error("fitz_open_failed", path=pdf_path, error=str(e))
        raise ValueError(f"Failed to open PDF with fitz: {e}")

    page_count = len(doc)
    if page_count == 0:
        log.error("empty_pdf", path=pdf_path)
        doc.close()
        raise ValueError("PDF has 0 pages")

    log.info("parse_start", path=pdf_path, page_count=page_count)

    parsed_pages = []
    total_blocks_count = 0

    for i, page in enumerate(doc):
        page_no = i + 1
        
        # Extract blocks: (x0, y0, x1, y1, text, block_no, block_type)
        # block_type: 0 = text, 1 = image
        raw_blocks = page.get_text("blocks")
        
        page_blocks = []
        block_texts = []
        
        for b in raw_blocks:
            x0, y0, x1, y1, text, block_no, block_type = b
            
            if not text.strip():
                continue
                
            block_dict = {
                "block_no": int(block_no),
                "text": text,
                "bbox": [x0, y0, x1, y1],
                "type": "text" if block_type == 0 else "image",
                "line_count": len(text.strip().split("\n"))
            }
            
            page_blocks.append(block_dict)
            block_texts.append(text)
        
        raw_text = "\n".join(block_texts)
        
        parsed_page = ParsedPage(
            page_no=page_no,
            raw_text=raw_text,
            blocks=page_blocks
        )
        
        parsed_pages.append(parsed_page)
        total_blocks_count += len(page_blocks)
        
        log.info(
            "page_parsed", 
            page_no=page_no, 
            block_count=len(page_blocks), 
            char_count=len(raw_text)
        )

    doc.close()
    
    parsed_doc = ParsedDocument(
        source_path=pdf_path,
        filename=os.path.basename(pdf_path),
        total_pages=page_count,
        pages=parsed_pages
    )

    log.info(
        "parse_complete", 
        total_pages=page_count, 
        total_blocks=total_blocks_count
    )
    
    return parsed_doc
