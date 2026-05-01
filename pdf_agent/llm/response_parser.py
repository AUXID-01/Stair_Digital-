import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class Citation:
    chunk_id: str
    page: int
    section: str

@dataclass
class ParsedResponse:
    answer_text: str
    citations: List[Citation]
    is_valid: bool  # False if no citations found

def parse_llm_response(raw_response: str) -> ParsedResponse:
    """
    Splits LLM output into answer body and citation list.
    Returns is_valid=False if no CITATIONS block is found.
    """
    citation_pattern = re.compile(
        r"CITATIONS:\s*((?:-\s*ID:\s*.+?\|\s*Page\s*\d+\s*\|\s*Section\s*.+\n?)+)",
        re.IGNORECASE
    )
    
    match = citation_pattern.search(raw_response)
    
    if not match:
        return ParsedResponse(
            answer_text=raw_response.strip(),
            citations=[],
            is_valid=False
        )
    
    answer_text = raw_response[:match.start()].strip()
    citation_block = match.group(1)
    
    seen = set()
    citations = []
    for line in citation_block.strip().splitlines():
        line = line.strip().lstrip("-").strip()
        if not line:
            continue
        
        # Format: ID: <chunk_id> | Page <number> | Section <section_title>
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            continue
            
        try:
            # Extract ID
            chunk_id = re.sub(r"^ID:\s*", "", parts[0], flags=re.IGNORECASE).strip()
            
            # Extract Page
            page_num = int(re.search(r"\d+", parts[1]).group())
            
            # Extract Section
            section_raw = parts[2].strip()
            section = re.sub(r"^Section\s+", "", section_raw, flags=re.IGNORECASE).strip()
            
            key = (chunk_id, page_num, section.lower())
            if key in seen:
                continue
            seen.add(key)
            
            citations.append(Citation(chunk_id=chunk_id, page=page_num, section=section))
        except (AttributeError, ValueError):
            continue
    
    return ParsedResponse(
        answer_text=answer_text,
        citations=citations,
        is_valid=len(citations) > 0
    )
