"""
retrieval/hallucination_gate.py
Responsibility: Gate 1 — block LLM call if retrieval scores are below threshold.
Inputs: List[RetrievalHit], threshold (float)
Outputs: bool (True = pass, False = refuse) + optional RefusalObject
Dependencies: config.py, logs/schema.py, refusal/formatter.py
"""
