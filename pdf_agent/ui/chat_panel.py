"""
ui/chat_panel.py
Responsibility: Render conversation history and capture new user input.
Inputs: Streamlit session state (chat history)
Outputs: user input string
Dependencies: conversation/history.py
"""

import streamlit as st
from typing import Optional

def render_chat_panel(session_state) -> Optional[str]:
    """Renders the chat interface and returns new user input."""
    
    # Display chat history
    for message in session_state.get("chat_history", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the document..."):
        return prompt

    return None
