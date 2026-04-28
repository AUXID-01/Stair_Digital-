"""
ui/trace_panel.py
Responsibility: Render per-turn retrieval trace in the Streamlit sidebar for observability.
Inputs: List[dict] trace log from logging/trace.py
Outputs: None (pure render)
Dependencies: logs/trace.py
"""

import streamlit as st

def render_trace_panel(trace_log: list) -> None:
    """Renders the retrieval trace in the sidebar."""
    
    st.sidebar.header("🔍 Retrieval Trace")
    
    if not trace_log:
        st.sidebar.info("No trace yet for this turn.")
        return

    for event in trace_log:
        event_type = event.get("event_type", "Unknown Event")
        payload = event.get("payload", {})
        
        # Render event type as bold heading
        st.sidebar.markdown(f"**{event_type}**")
        # Render payload as JSON
        st.sidebar.json(payload)
