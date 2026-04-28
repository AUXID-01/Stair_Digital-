"""
logs/trace.py
Responsibility: Collect per-turn trace events and expose them for the Streamlit sidebar.
Inputs: trace events (query, retrievals, gate decision, citations)
Outputs: List[dict] — trace log for current turn
Dependencies: logs/schema.py
"""

from datetime import datetime
from typing import List

def init_trace(session_state) -> None:
    """Sets session_state['trace_log'] = [] if not already present."""
    if "trace_log" not in session_state:
        session_state["trace_log"] = []

def add_trace_event(session_state, event_type: str, payload: dict) -> None:
    """Appends a dict to session_state['trace_log']."""
    if "trace_log" not in session_state:
        init_trace(session_state)
    
    event = {
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.now().isoformat()
    }
    session_state["trace_log"].append(event)

def get_trace(session_state) -> List[dict]:
    """Returns session_state['trace_log'] or empty list."""
    return session_state.get("trace_log", [])
