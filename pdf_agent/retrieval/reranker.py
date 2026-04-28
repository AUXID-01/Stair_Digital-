"""
retrieval/reranker.py
Responsibility: Rerank retrieved chunks using CrossEncoder for improved precision.
Inputs: query (str), List[RetrievalHit]
Outputs: List[RetrievalHit] (reordered)
Dependencies: config.py, logs/schema.py
"""
