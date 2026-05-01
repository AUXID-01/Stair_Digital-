import sys
import os
import json
import re

# Add project root to path
sys.path.append(os.getcwd())

from ingestion.parser import parse_pdf
from ingestion.cleaner import clean_pages
from ingestion.metadata import enrich_metadata
from ingestion.chunker import chunk_pages
from indexing.index_builder import build_index
from retrieval.searcher import search_query
from retrieval.reranker import rerank
from retrieval.hallucination_gate import evaluate
from llm.prompt_builder import build_messages, SYSTEM_PROMPT
from llm.groq_client import call_llm
from llm.response_parser import parse_llm_response
from llm.gate2_checker import validate_citations_against_chunks

def run_test(name, fn):
    print(f"\n=== TEST: {name} ===")
    try:
        fn()
    except Exception as e:
        print(f"FAILED: {e}")

# 1. Setup - Index the PDFs
print("Indexing PDFs...")
pdfs = ["finance.pdf", "biology.pdf", "cooking.pdf"]
for pdf in pdfs:
    path = f"data/test_pdfs/{pdf}"
    parsed = parse_pdf(path)
    cleaned = clean_pages(parsed)
    enriched = enrich_metadata(cleaned)
    chunks = chunk_pages(enriched)
    build_index(chunks, source_doc=pdf)

def test_document_isolation():
    # Query for "growth rate" but restricted to finance.pdf
    # Before, biology.pdf would have leaked in if filter failed.
    # Now, we expect 100% isolation.
    query = "What is the growth rate?"
    doc_id = "finance.pdf"
    hits = search_query(query, doc_id=doc_id, top_k=10)
    
    print(f"Query: {query} | Target: {doc_id}")
    leakage = [h for h in hits if h['doc_id'] != doc_id]
    
    for i, h in enumerate(hits):
        print(f"{i+1}. Source: {h['doc_id']} | Text: {h['preview']}")
            
    print(f"\nLeakage count: {len(leakage)}")
    if len(leakage) == 0:
        print("RESULT: SUCCESS - 100% Document Isolation.")
    else:
        print("RESULT: FAILURE - Leakage detected.")

def test_intent_vs_similarity():
    query = "What are inflation risks?"
    hits = search_query(query, doc_id="finance.pdf", top_k=5)
    hits = rerank(query, hits)
    
    messages = build_messages(hits, query)
    raw_answer = call_llm(SYSTEM_PROMPT, messages)
    parsed = parse_llm_response(raw_answer)
    
    print(f"Query: {query}")
    print(f"Answer: {parsed.answer_text}")
    print(f"Citations: {[c.chunk_id for c in parsed.citations]}")
    
    pages = [c.page for c in parsed.citations]
    if 2 in pages:
        print("RESULT: Correct intent captured (Page 2 cited).")
    else:
        print("RESULT: Intent failure.")

def test_citation_grounding_hardened():
    query = "What is the inflation risk mentioned on Page 2?"
    hits = search_query(query, doc_id="finance.pdf", top_k=5)
    hits = rerank(query, hits)
    
    messages = build_messages(hits, query)
    raw_answer = call_llm(SYSTEM_PROMPT, messages)
    parsed = parse_llm_response(raw_answer)
    
    validation = validate_citations_against_chunks(parsed, hits)
    print(f"Answer: {parsed.answer_text}")
    print(f"Citations: {[(c.chunk_id, c.page) for c in parsed.citations]}")
    print(f"Gate 2 Passed: {validation['passed']} | Reason: {validation['reason']}")

def test_intent_coverage_check():
    # Ask about something completely absent
    query = "What is the capital of France?"
    hits = search_query(query, doc_id="finance.pdf", top_k=5)
    hits = rerank(query, hits)
    
    gate_res = evaluate(hits, query)
    print(f"Query: {query}")
    print(f"Gate Passed: {gate_res.passed} | Reason: {gate_res.reason}")
    if not gate_res.passed:
        print(f"Refusal Message: {gate_res.message[:100]}...")

run_test("Document Isolation", test_document_isolation)
run_test("Intent vs Similarity (CrossEncoder)", test_intent_vs_similarity)
run_test("Hardened Grounding (Gate 2)", test_citation_grounding_hardened)
run_test("Intent Coverage Check", test_intent_coverage_check)
