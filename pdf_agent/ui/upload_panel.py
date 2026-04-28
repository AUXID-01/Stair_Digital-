"""
ui/upload_panel.py
Responsibility: Render PDF upload widget and trigger ingestion pipeline on new upload.
Inputs: Streamlit session state
Outputs: None (side effect: updates session state, triggers index_builder)
Dependencies: indexing/index_builder.py, logging/logger.py
"""

import os
import streamlit as st
from logs.logger import get_logger
from config import UPLOAD_DIR

log = get_logger("ui.upload_panel")

def render_upload_panel(session_state) -> None:
    """Renders the PDF upload widget and updates session state."""
    
    # Create upload directory if missing
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

    if uploaded_file is not None:
        filename = uploaded_file.name
        
        # Check if the file is truly a PDF (Streallit type filter handles this mostly, but good practice)
        if not filename.lower().endswith(".pdf"):
            st.warning(f"File {filename} is not a PDF. Please upload a valid PDF.")
            log.warning("invalid_file_type", filename=filename)
            return

        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Only save if it doesn't exist or we want to overwrite (for Phase 1, we just save)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Update session state if it's a new file or needs indexing
        if session_state.get("uploaded_doc") != filename:
            session_state["uploaded_doc"] = filename
            session_state["indexed"] = False
            session_state["doc_id"] = filename.rsplit(".", 1)[0]
            
            st.success(f"Successfully uploaded: {filename}")
            log.info("pdf_uploaded", filename=filename, doc_id=session_state["doc_id"])
    else:
        # Reset doc state if no file is present (optional, but keep it stable for now)
        pass
