import unittest
import os
import json
import shutil
from config import ensure_project_dirs, CHROMA_PERSIST_DIR, LOG_FILE, UPLOAD_DIR
from logs.schema import ParsedDocument, ParsedPage, Chunk
from ingestion.parser import parse_pdf
from ingestion.cleaner import clean_pages
from ingestion.metadata import enrich_metadata
from ingestion.chunker import chunk_pages
from indexing.index_builder import build_index

class TestPhase0to5Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure clean test environment."""
        ensure_project_dirs()
        cls.test_pdf = os.path.join(UPLOAD_DIR, "00_test_text.pdf")
        if not os.path.exists(cls.test_pdf):
            raise FileNotFoundError(f"Test PDF missing at {cls.test_pdf}")

    def test_full_pipeline(self):
        # 1. Directory Verification
        self.assertTrue(os.path.exists(UPLOAD_DIR))
        self.assertTrue(os.path.exists(os.path.dirname(LOG_FILE)))
        self.assertTrue(os.path.exists(CHROMA_PERSIST_DIR))

        # 2. Parsing Stage
        parsed = parse_pdf(self.test_pdf)
        self.assertIsInstance(parsed, ParsedDocument)
        self.assertGreater(parsed.total_pages, 0)
        self.assertEqual(len(parsed.pages), parsed.total_pages)

        # 3. Cleaning Stage
        cleaned = clean_pages(parsed)
        self.assertIsInstance(cleaned, ParsedDocument)
        for page in cleaned.pages:
            self.assertTrue(hasattr(page, 'raw_text'))

        # 4. Metadata Enrichment Stage
        enriched = enrich_metadata(cleaned)
        self.assertIsInstance(enriched, ParsedDocument)
        for page in enriched.pages:
            self.assertIsNotNone(page.section_title)
            self.assertGreater(len(page.section_title), 0)

        # 5. Chunking Stage
        chunks = chunk_pages(enriched)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        for chunk in chunks:
            self.assertIsInstance(chunk, Chunk)
            # Verify required metadata fields
            self.assertIsNotNone(chunk.chunk_id)
            self.assertIsNotNone(chunk.text)
            self.assertIsNotNone(chunk.page_start)
            self.assertIsNotNone(chunk.page_end)
            self.assertIsNotNone(chunk.section_title)
            self.assertIsNotNone(chunk.char_count)
            # Assert char_count integrity
            self.assertEqual(chunk.char_count, len(chunk.text))

        # 6. Indexing Stage
        summary = build_index(chunks, source_doc="00_test_text")
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["indexed_chunk_count"], len(chunks))
        self.assertEqual(summary["collection_name"], "pdf_agent_collection")
        self.assertEqual(summary["persist_path"], CHROMA_PERSIST_DIR)

        # 7. Persistence Verification
        # Check for sqlite file or segment directories
        self.assertTrue(os.path.exists(CHROMA_PERSIST_DIR))
        files = os.listdir(CHROMA_PERSIST_DIR)
        self.assertGreater(len(files), 0, "Chroma persistence directory is empty")

        # 8. Log Event Verification
        required_events = {
            "parse_start",
            "page_cleaned",
            "enrichment_complete",
            "chunk_complete",
            "embedding_batch_complete",
            "collection_add_complete",
            "index_build_complete"
        }
        
        self.assertTrue(os.path.exists(LOG_FILE), f"Log file missing at {LOG_FILE}")
        
        found_events = set()
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if "event" in entry:
                        found_events.add(entry["event"])
                except json.JSONDecodeError:
                    continue
        
        missing = required_events - found_events
        self.assertEqual(len(missing), 0, f"Missing log events: {missing}")

    def tearDown(self):
        """Summary printing."""
        pass

if __name__ == "__main__":
    print("\n" + "="*50)
    print("PHASE 0-5 INTEGRATION TEST SUITE")
    print("="*50)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase0to5Integration)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    if result.wasSuccessful():
        print("\nSUMMARY: INTEGRATION PASS")
        print("FOUNDATION STABLE FOR PHASE 6")
    else:
        print("\nSUMMARY: INTEGRATION FAIL")
        print(f"Errors: {len(result.errors)}")
        print(f"Failures: {len(result.failures)}")
    print("="*50 + "\n")
