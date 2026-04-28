"""
conversation/history.py
Responsibility: Store and retrieve last N conversation turns from session state.
Inputs: turn (dict with role + content), session state
Outputs: List[dict] — recent history
Dependencies: config.py
"""
