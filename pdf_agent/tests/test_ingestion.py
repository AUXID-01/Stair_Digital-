"""
tests/test_ingestion.py
Standalone test script for the ingestion layer.
"""

import os
import sys
from typing import List

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.loader import load_pdf
from ingestion.parser import parse_pdf
from ingestion.cleaner import clean_pages
from ingestion.chunker import chunk_pages
from ingestion.metadata import detect_section, enrich_metadata
from logs.schema import ParsedPage, Chunk, ParsedDocument
from config import UPLOAD_DIR, CHUNK_SIZE
from rich.console import Console
from rich.table import Table

console = Console()

def run_test():
    console.rule("[bold blue]PDF Ingestion Test")

    # 1. Auto-detect first .pdf in data/uploads/
    pdfs = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")]
    if not pdfs:
        console.print("[red]No PDF in data/uploads/ — upload one first[/red]")
        sys.exit(0)

    test_pdf = os.path.join(UPLOAD_DIR, pdfs[0])
    console.print(f"[yellow]Testing with:[/yellow] {test_pdf}")

    try:
        # Load (returns metadata)
        metadata = load_pdf(test_pdf)
        assert isinstance(metadata, dict)
        assert "path" in metadata
        
        # Parse (returns ParsedDocument)
        parsed_doc = parse_pdf(metadata["path"])
        assert isinstance(parsed_doc, ParsedDocument)
        
        # 2. Print summary table
        parsed_pages = parsed_doc.pages
        total_pages = len(parsed_pages)
        total_blocks = sum(len(p.blocks) for p in parsed_pages)
        total_chars = sum(len(p.raw_text) for p in parsed_pages)
        avg_chars = total_chars / total_pages if total_pages > 0 else 0
        
        # Find page with most blocks
        max_blocks_page = max(parsed_pages, key=lambda p: len(p.blocks))
        
        summary_table = Table(title="Ingestion Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Pages", str(total_pages))
        summary_table.add_row("Total Blocks", str(total_blocks))
        summary_table.add_row("Avg Chars/Page", f"{avg_chars:.2f}")
        summary_table.add_row("Most Blocks Page", f"Page {max_blocks_page.page_no} ({len(max_blocks_page.blocks)} blocks)")
        
        console.print(summary_table)
        
        console.print("\n[bold cyan]Preview (First 200 chars of Page 1):[/bold cyan]")
        console.print(f"[grey70]{parsed_pages[0].raw_text[:200]}...[/grey70]\n")

        # 3. Print per-page stats for first 5 pages
        stats_table = Table(title="First 5 Pages Stats")
        stats_table.add_column("Page", justify="center")
        stats_table.add_column("Blocks", justify="right")
        stats_table.add_column("Chars", justify="right")
        stats_table.add_column("Snippet", width=80)
        
        for p in parsed_pages[:5]:
            snippet = p.raw_text.replace("\n", " ").strip()[:80]
            stats_table.add_row(
                str(p.page_no),
                str(len(p.blocks)),
                str(len(p.raw_text)),
                snippet
            )
        
        console.print(stats_table)

        # 4. Assertions
        for p in parsed_pages:
            assert p.page_no >= 1, f"Invalid page_no on page {p.page_no}"
            assert isinstance(p.raw_text, str), f"raw_text is not a string on page {p.page_no}"
            # Check if there's text if blocks were found, though blocks can be image only
            # The requirement is "raw_text is a non-empty string"
            assert len(p.raw_text) > 0, f"raw_text is empty on page {p.page_no}"
            assert isinstance(p.blocks, list), f"blocks is not a list on page {p.page_no}"

        console.print("\n[bold green]PASSED: All assertions passed[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]FAILED: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)

def test_phase3():
    console.rule("[bold blue]Phase 3: Clean, Metadata, Chunk")
    
    pdfs = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")]
    if not pdfs:
        console.print("[red]No PDF in data/uploads/ — upload one first[/red]")
        return

    test_pdf = os.path.join(UPLOAD_DIR, pdfs[0])
    filename = pdfs[0]
    
    try:
        # 1. Load (metadata)
        metadata = load_pdf(test_pdf)
        
        # 2. Parse (ParsedDocument)
        parsed_doc = parse_pdf(metadata["path"])
        
        # 3. Clean
        cleaned_doc = clean_pages(parsed_doc)
        
        # 4. Enrich
        enriched_doc = enrich_metadata(cleaned_doc)
        
        # 5. Chunk
        chunks = chunk_pages(enriched_doc)
        
        # 4. Summary Table
        unique_sections = sorted(list(set(c.section_title for c in chunks)))
        avg_size = sum(len(c.text) for c in chunks) / len(chunks) if chunks else 0
        min_size = min(len(c.text) for c in chunks) if chunks else 0
        max_size = max(len(c.text) for c in chunks) if chunks else 0
        
        chunks_per_page = {}
        for c in chunks:
            chunks_per_page[c.page_start] = chunks_per_page.get(c.page_start, 0) + 1
            
        summary_table = Table(title="Phase 3 Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        summary_table.add_row("Total Chunks", str(len(chunks)))
        summary_table.add_row("Unique Sections", ", ".join(unique_sections))
        summary_table.add_row("Avg Chunk Size", f"{avg_size:.2f}")
        summary_table.add_row("Min/Max Size", f"{min_size} / {max_size}")
        
        # First 5 pages chunks count
        cpp_str = ", ".join([f"P{p}:{c}" for p, c in sorted(chunks_per_page.items())[:5]])
        summary_table.add_row("Chunks per Page (First 5)", cpp_str)
        
        console.print(summary_table)

        # 5. Section detection results table
        section_table = Table(title="Section Detection & Cleaning (First 5 Pages)")
        section_table.add_column("Page", justify="center")
        section_table.add_column("Section Detected", style="green")
        section_table.add_column("Heuristic", justify="center")
        section_table.add_column("Chars Before", justify="right")
        section_table.add_column("Chars After", justify="right")
        
        for i in range(min(5, len(parsed_doc.pages))):
            p_raw = parsed_doc.pages[i] # This is already cleaned in place if we used same object
            # In our current logic clean_pages modifies the doc.pages list but returns the same doc.
            # So let's re-run parse to get raw count for comparison or just use previous values
            
            section = p_raw.section_title or "General"
            
            section_table.add_row(
                str(p_raw.page_no),
                section,
                "Check logs", # Heuristic used is in logs, keep it simple for table
                "N/A", # Raw char count not easily accessible without re-parse
                str(len(p_raw.raw_text))
            )
        console.print(section_table)

        # 6. Preview first 3 chunks
        console.print("\n[bold cyan]First 3 Chunks Preview:[/bold cyan]")
        for i in range(min(3, len(chunks))):
            c = chunks[i]
            console.print(f"[bold]ID:[/bold] {c.chunk_id} | [bold]Page:[/bold] {c.page_start} | [bold]Section:[/bold] {c.section_title}")
            console.print(f"[grey70]{c.text[:150]}...[/grey70]\n")

        # 7. Assertions
        for c in chunks:
            assert isinstance(c.chunk_id, str) and c.chunk_id, "Missing chunk_id"
            assert c.page_start >= 1, "Invalid page_start"
            assert c.page_end >= c.page_start, "Invalid page_end"
            assert isinstance(c.section_title, str) and c.section_title, "Missing section_title"
            assert c.source_doc == filename.lower().replace(" ", "_").rsplit(".", 1)[0], "source_doc mismatch"
            assert isinstance(c.text, str) and c.text, "Missing chunk text"
            assert len(c.text) <= CHUNK_SIZE + 10, f"Chunk too large: {len(c.text)}"
            assert hasattr(c, 'char_count'), "Missing char_count field"
            assert c.char_count == len(c.text), f"char_count mismatch: {c.char_count} != {len(c.text)}"

        console.print("[bold green]PASSED: Phase 3 assertions passed[/bold green]")

    except Exception as e:
        console.print(f"[bold red]FAILED Phase 3: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run_test()
    test_phase3()
