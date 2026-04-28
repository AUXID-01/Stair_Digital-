"""
retrieval/searcher.py
Responsibility: Embed user query and retrieve top-k similar chunks from ChromaDB.
Inputs: query (str), top_k (int)
Outputs: List[RetrievalHit]
Dependencies: indexing/embedder.py, indexing/vector_store.py, config.py, logs/schema.py
"""
