"""
ui/citation_card.py
Responsibility: Render a styled citation chip showing Page X | Section Y for each hit.
Inputs: RetrievalHit or citation dict
Outputs: None (pure Streamlit render)
Dependencies: logs/schema.py
"""

import streamlit as st
from logs.schema import RetrievalHit

def render_citation_card(hit: RetrievalHit) -> None:
    """Renders a single citation chip with styling."""
    
    citation_text = f"📄 Page {hit.page} | § {hit.section} (score: {hit.score:.2f})"
    
    # Subtle styling using blockquote
    st.markdown(f"> {citation_text}")
