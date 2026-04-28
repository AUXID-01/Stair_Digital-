"""
conversation/query_rewriter.py
Responsibility: Resolve ambiguous references like "it" or "that section" using conversation history.
Inputs: query (str), List[dict] chat history
Outputs: rewritten query (str)
Dependencies: llm/groq_client.py, config.py
"""
