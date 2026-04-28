"""
llm/response_parser.py
Responsibility: Parse LLM response string into AnswerObject with citations extracted.
Inputs: raw response (str), List[RetrievalHit]
Outputs: AnswerObject
Dependencies: logging/schema.py
"""
