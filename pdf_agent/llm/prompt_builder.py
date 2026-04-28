"""
llm/prompt_builder.py
Responsibility: Assemble system prompt and context block from retrieved chunks + metadata.
Inputs: List[RetrievalHit], query (str), chat_history (list)
Outputs: system_prompt (str), user_message (str)
Dependencies: config.py, logging/schema.py
"""
