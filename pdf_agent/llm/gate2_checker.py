"""
llm/gate2_checker.py
Responsibility: Gate 2 — validate that answer contains citations and no [INSUFFICIENT] marker.
Inputs: AnswerObject
Outputs: AnswerObject (validated) or RefusalObject
Dependencies:logs/schema.py, refusal/formatter.py
"""
