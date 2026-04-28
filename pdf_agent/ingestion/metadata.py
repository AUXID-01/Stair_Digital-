"""
ingestion/metadata.py
Responsibility: Tag each chunk with page number, detected section title, and unique chunk ID.
Inputs: List[Chunk] (untagged)
Outputs: List[Chunk] (tagged with metadata)
Dependencies: config.py, logs/schema.py
"""

import re
from logs.logger import get_logger
from logs.schema import ParsedPage, ParsedDocument

log = get_logger("ingestion.metadata")

def detect_section(page: ParsedPage) -> str:
    """
    Detects the likely section title for a given page using heuristics.
    """
    lines = [line.strip() for line in page.raw_text.split("\n") if line.strip()]
    if not lines:
        log.info("section_detected", page_no=page.page_no, detected_section="General", heuristic_used="fallback")
        return "General"

    # Regex for HEURISTIC 1
    RE_SECTION = re.compile(r"^(Section\s+)?\d+(\.\d+)*\.?\s+\S+", re.IGNORECASE)

    # HEURISTIC 1: Numbered section pattern
    for line in lines:
        if len(line) <= 80 and RE_SECTION.match(line):
            log.info("section_detected", page_no=page.page_no, detected_section=line, heuristic_used="1")
            return line

    # HEURISTIC 2: ALL CAPS heading
    for line in lines:
        if 4 <= len(line) <= 80 and line.isupper() and len(line.split()) >= 2:
            log.info("section_detected", page_no=page.page_no, detected_section=line, heuristic_used="2")
            return line

    # HEURISTIC 3: Title Case heading
    for line in lines:
        if 4 <= len(line) <= 80 and line.istitle() and not line.endswith((".", ",")):
            log.info("section_detected", page_no=page.page_no, detected_section=line, heuristic_used="3")
            return line

    # HEURISTIC 4: Short bold-like line (first non-empty line)
    first_line = lines[0]
    if 4 <= len(first_line) <= 60 and not first_line.endswith((".", ",", ";", ":")):
        log.info("section_detected", page_no=page.page_no, detected_section=first_line, heuristic_used="4")
        return first_line

    # FALLBACK
    log.info("section_detected", page_no=page.page_no, detected_section="General", heuristic_used="fallback")
    return "General"

def enrich_metadata(doc: ParsedDocument) -> ParsedDocument:
    """
    Assigns section titles to all pages in the document.
    """
    log.info("enrichment_start", filename=doc.filename)
    for page in doc.pages:
        page.section_title = detect_section(page)
    log.info("enrichment_complete", filename=doc.filename)
    return doc
