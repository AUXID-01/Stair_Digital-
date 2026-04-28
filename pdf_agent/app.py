import streamlit as st
import os
import json
from datetime import datetime
from config import ensure_project_dirs, UPLOAD_DIR
from ingestion.parser import parse_pdf
from ingestion.cleaner import clean_pages
from ingestion.metadata import enrich_metadata
from ingestion.chunker import chunk_pages
from indexing.index_builder import build_index

# 1. Page Configuration
st.set_page_config(
    page_title="Phase 0-5 Foundation Stable | Ready for Retrieval",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Session State Initialization
if "current_pdf" not in st.session_state:
    st.session_state.current_pdf = None
if "indexed" not in st.session_state:
    st.session_state.indexed = False
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_index_summary" not in st.session_state:
    st.session_state.last_index_summary = None
if "trace_events" not in st.session_state:
    st.session_state.trace_events = []

def add_trace(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.trace_events.append(f"[{timestamp}] {level}: {message}")
    if len(st.session_state.trace_events) > 20:
        st.session_state.trace_events.pop(0)

# 3. Sidebar: Configuration & Status
with st.sidebar:
    st.title("🎛️ Control Panel")
    
    # Upload Widget
    uploaded_file = st.file_uploader("Upload Source PDF", type=["pdf"])
    if uploaded_file:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        if st.session_state.current_pdf != uploaded_file.name:
            # New file uploaded
            ensure_project_dirs()
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.current_pdf = uploaded_file.name
            st.session_state.indexed = False
            st.session_state.chunk_count = 0
            st.session_state.last_index_summary = None
            add_trace(f"Uploaded {uploaded_file.name}")
            st.success(f"File uploaded: {uploaded_file.name}")

    st.markdown("---")
    
    # Ingest Button
    can_ingest = st.session_state.current_pdf is not None and not st.session_state.indexed
    if st.button("🚀 Ingest & Index", disabled=not can_ingest):
        with st.spinner("Processing PDF Pipeline..."):
            try:
                add_trace("Starting ingestion pipeline...")
                file_path = os.path.join(UPLOAD_DIR, st.session_state.current_pdf)
                
                # Run Pipeline
                parsed = parse_pdf(file_path)
                add_trace(f"Parsed {parsed.total_pages} pages")
                
                cleaned = clean_pages(parsed)
                add_trace("Text cleaning complete")
                
                enriched = enrich_metadata(cleaned)
                add_trace("Metadata enrichment complete")
                
                chunks = chunk_pages(enriched)
                add_trace(f"Created {len(chunks)} chunks")
                
                summary = build_index(chunks, source_doc=st.session_state.current_pdf)
                add_trace("Vector indexing complete")
                
                # Update State
                st.session_state.indexed = True
                st.session_state.chunk_count = summary.get("indexed_chunk_count", 0)
                st.session_state.last_index_summary = summary
                
            except Exception as e:
                add_trace(f"Error during ingestion: {str(e)}", level="ERROR")
                st.error(f"Ingestion failed: {e}")

    st.markdown("---")
    
    # Status Display
    st.subheader("System Status")
    if not st.session_state.current_pdf:
        st.info("Upload PDF to begin")
    elif not st.session_state.indexed:
        st.warning("Ready to index")
    else:
        st.success(f"✅ Indexed {st.session_state.chunk_count} chunks from {st.session_state.current_pdf}")
        if st.session_state.last_index_summary:
            with st.expander("Index Summary"):
                st.json(st.session_state.last_index_summary)

    st.markdown("---")
    
    # Sidebar Trace
    st.subheader("Execution Trace")
    trace_container = st.container(height=300)
    with trace_container:
        for event in reversed(st.session_state.trace_events):
            st.caption(event)

# 4. Main Panel: Chat Interface
st.title("📄 PDF-Grounded Conversational Agent")

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask a question about the document"):
    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    add_trace(f"User query: {prompt}")

    # Show Stub Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Processing... ⚙️")
        
        # In a real app, logic for RAG would go here.
        # For Phase 5, we just provide a stub.
        if not st.session_state.indexed:
            response = "I haven't indexed the document yet. Please click 'Ingest & Index' in the sidebar first."
        else:
            response = f"I've received your question about '{st.session_state.current_pdf}', but retrieval logic is not yet enabled (Phase 6)."
        
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        message_placeholder.markdown(response)

# 5. Footer / Info
if not st.session_state.chat_history:
    st.markdown("""
    ### Welcome!
    This is the foundation for your PDF-grounded assistant.
    1. **Upload** a PDF in the sidebar.
    2. **Ingest** it to create searchable embeddings.
    3. **Chat** will be enabled for retrieval in the next phase.
    """)
