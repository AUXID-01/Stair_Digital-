"""
retrieval/searcher.py
Responsibility: Phase 6 Retrieval. Performs semantic search against ChromaDB using query embeddings.
Enforces strict document-level filtering to ensure results only come from the active document.
"""

from typing import List, Dict, Optional
import re
from indexing.embedder import get_model
from indexing.vector_store import VectorStore
from config import TOP_K
from logs.logger import get_logger

log = get_logger("retrieval.searcher")

def build_preview(text: str, max_chars: int = 280) -> str:
    """
    Cleans and truncates a chunk of text for UI preview.
    Normalizes whitespace and avoids cutting words in half.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return "No preview available."
    
    clean_text = " ".join(text.split()).strip()
    
    if len(clean_text) <= max_chars:
        return clean_text
    
    truncated = clean_text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > int(max_chars * 0.85):
        truncated = truncated[:last_space]
        
    return truncated.rstrip() + "..."

def search_query(query: str, doc_id: str, top_k: int = TOP_K) -> List[Dict]:
    """
    Encodes the input query and retrieves the most relevant chunks.
    Strictly filters results by document identity.
    
    Args:
        query: The user's natural language question.
        doc_id: Unique identifier to restrict the search.
        top_k: Number of nearest neighbors to retrieve.
        
    Returns:
        A validated list of retrieval hits for the active document.
    """
    if not doc_id:
        log.error("retrieval_missing_doc_id")
        raise ValueError("doc_id is mandatory for constrained retrieval.")
    if not query or not query.strip():
        log.warning("retrieval_skip_empty_query")
        return []

    try:
        log.info("retrieval_start", query=query, doc_id=doc_id, top_k=top_k)

        # 1. Encode Query
        model = get_model()
        
        try:
            query_embeddings = model.encode([query], convert_to_numpy=True).tolist()
        except Exception as e:
            log.error("retrieval_failure", error="Embedding generation failed")
            return []
            
        query_vector = query_embeddings[0]
        log.info("retrieval_query_embedded")

        # 2. Open Persistent Store
        vector_store = VectorStore()
        vector_store.initialize()
        
        if not vector_store.collection:
            log.error("retrieval_failure", error="Vector store collection not initialized")
            return []

        # 3. Handle Filtering Strategy
        where_filter = None
        if doc_id:
            # Enforce strict document isolation using 'doc_id' field
            where_filter = {"doc_id": doc_id}
            log.info("retrieval_filter_applied", doc_id=doc_id)

        results = vector_store.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # 5. Normalize and Strictly Verify Hits
        hits = []
        total_preview_len = 0
        
        if results and results.get("documents") and results["documents"]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            chroma_ids = results["ids"][0]

            for i in range(len(documents)):
                meta = metadatas[i]
                actual_doc = meta.get("doc_id")
                
                text_content = documents[i]
                preview_text = build_preview(text_content)
                total_preview_len += len(preview_text)
                
                hits.append({
                    "chunk_id": meta.get("chunk_id", chroma_ids[i]),
                    "text": text_content,
                    "preview": preview_text,
                    "distance": float(distances[i]),
                    "page": int(meta.get("page", 0)),
                    "section": meta.get("section_title", "General"),
                    "ocr_quality": meta.get("ocr_quality", "good"),
                    "doc_id": actual_doc
                })

        log.info("retrieval_complete", 
                 hit_count=len(hits), 
                 preview_length=total_preview_len)
        return hits

    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Retrieval failed | query='{query}' | error={type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        return []
