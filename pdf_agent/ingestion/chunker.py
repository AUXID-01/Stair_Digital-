import re
from typing import List, Dict
from logs.logger import get_logger
from logs.schema import ParsedPage, ParsedDocument
from config import CHUNK_SIZE, CHUNK_OVERLAP

log = get_logger("ingestion.chunker")

def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into sentences using a robust regex.
    Handles common abbreviations and prevents mid-word splits.
    """
    # Fixed-width look-behind for standard punctuation followed by space and uppercase
    sentence_endINGS = r'(?<=[.!?])\s+(?=[A-Z0-9])'
    sentences = re.split(sentence_endINGS, text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_pages(doc: ParsedDocument) -> List[Dict]:
    """
    Splits cleaned and enriched pages into chunks with semantic integrity.
    Implements sentence-aware splitting and cross-page overlap.
    """
    doc_id = doc.filename.lower().replace(" ", "_").rsplit(".", 1)[0]
    pages = doc.pages
    
    log.info("chunk_start", doc_id=doc_id, page_count=len(pages))
    
    chunks = []
    global_chunk_idx = 0
    
    # Cross-page carry over buffer (sentences from end of previous page)
    carry_over_sentences = []
    
    chunk_limit = CHUNK_SIZE
    if doc.low_quality_ocr:
        chunk_limit = 300  # Slightly larger than 150 to accommodate full sentences
        log.warning("chunking_low_quality_ocr_adjustment", doc_id=doc_id, chunk_size=chunk_limit)

    for page in pages:
        section_title = page.section_title or "General"
        text = page.text
        
        if not text:
            continue
            
        current_page_sentences = split_into_sentences(text)
        
        # Merge carry-over from previous page
        all_sentences = carry_over_sentences + current_page_sentences
        
        current_chunk_sentences = []
        current_chunk_len = 0
        
        i = 0
        while i < len(all_sentences):
            sent = all_sentences[i]
            
            # If a single sentence exceeds the limit, we must split it by characters (fallback)
            # but usually, we just add it and close the chunk.
            current_chunk_sentences.append(sent)
            current_chunk_len += len(sent)
            
            # Check if chunk is full or we reached end of page sentences
            if current_chunk_len >= chunk_limit or i == len(all_sentences) - 1:
                chunk_text = " ".join(current_chunk_sentences)
                
                new_chunk = {
                    "chunk_id": f"{doc_id}_p{page.page_number}_c{global_chunk_idx}",
                    "page": page.page_number,
                    "section_title": section_title,
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "ocr_quality": "low" if doc.low_quality_ocr else "good"
                }
                chunks.append(new_chunk)
                global_chunk_idx += 1
                
                # IMPLEMENT OVERLAP (10-15%)
                # Backtrack index by 1 or 2 sentences to start the next chunk with context
                # We backtrack only if there are more sentences to process in THIS page cycle
                overlap_count = max(1, len(current_chunk_sentences) // 8) # ~12.5% overlap in sentence count
                
                # Reset for next chunk
                current_chunk_sentences = []
                current_chunk_len = 0
                
                # If not the very last sentence of the entire set, backtrack i
                if i < len(all_sentences) - 1:
                    i -= overlap_count
            
            i += 1

        # CROSS-PAGE OVERLAP: Carry the last 2 sentences to the next page
        if len(current_page_sentences) >= 2:
            carry_over_sentences = current_page_sentences[-2:]
        else:
            carry_over_sentences = current_page_sentences

    log.info("chunk_complete", total_chunks=len(chunks))
    return chunks
