"""
DocSense v2 - Enhanced AI Document Q&A with Vector Embeddings

Architecture:
- Chat Mode: GROQ (Llama 3.3) for general conversation
- Document Mode: Vector Search (FAISS) + Mistral retrieval + GROQ answering
- Storage: FAISS vector embeddings with semantic + keyword hybrid search

Author: AI Assistant
Created: November 2025
Version: 2.0
"""

import logging
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from chat_mode import get_chat_mode
    from hybrid_query_engine import get_hybrid_query_engine
    from document_engine import process_documents_with_embeddings
    from vector_store import get_vector_store
    from table_formatter import display_response_with_visuals, extract_numerical_data
except ImportError as e:
    st.error(f"Failed to import modules: {str(e)}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="DocSense v2 - AI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        border-radius: 10px;
    }
    
    .version-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .mode-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem;
    }
    
    .chat-mode-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .doc-mode-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🧠 AI Assistant <span class="version-badge">v2.0</span></div>', unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'mode' not in st.session_state:
    st.session_state.mode = 'chat'

if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Mode selection
    st.subheader("Select Mode")
    mode = st.radio(
        "Mode",
        ["💬 Chat Mode", "📚 Document Mode"],
        index=0 if st.session_state.mode == 'chat' else 1,
        label_visibility="collapsed"
    )
    
    # Update mode
    new_mode = 'chat' if mode == "💬 Chat Mode" else 'document'
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.session_state.messages = []
        st.rerun()
    
    # Mode description
    if st.session_state.mode == 'chat':
        st.info("💬 **Chat Mode Active**\n\nDirect conversation with GROQ AI")
    else:
        st.info("📚 **Document Mode Active**\n\nVector-based Q&A from your documents")
    
    st.divider()
    
    # Document upload section (only in document mode)
    if st.session_state.mode == 'document':
        st.header("📄 Upload Documents")
        st.caption("Upload PDF or TXT files")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if st.button("🚀 Process Documents", use_container_width=True):
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                def update_progress(current, total, message):
                    if total > 0:
                        progress = int((current / total) * 100)
                        progress_bar.progress(progress)
                        progress_text.text(f"{message} ({current}/{total})")
                
                try:
                    success = process_documents_with_embeddings(
                        uploaded_files,
                        progress_callback=update_progress
                    )
                    
                    if success:
                        st.session_state.documents_loaded = True
                        progress_bar.progress(100)
                        progress_text.text("✅ Complete!")
                        
                        # Show stats
                        vector_store = get_vector_store()
                        stats = vector_store.get_stats()
                        
                        st.success("✓ Documents Loaded")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Chunks", stats['total_documents'])
                        with col2:
                            st.metric("Vectors", stats['vector_count'])
                        with col3:
                            st.metric("Dimensions", stats['dimension'])
                        
                        with st.expander("📁 Loaded Files"):
                            for source in stats['sources']:
                                st.write(f"• {source}")
                        
                        st.info("💡 Using semantic embeddings for intelligent search")
                        
                finally:
                    progress_bar.empty()
                    progress_text.empty()
    
    st.divider()
    
    # Response settings
    st.header("🎛️ Response Settings")
    detail_level = st.select_slider(
        "Detail Level",
        options=["Brief", "Detailed"],
        value="Detailed"
    )

# Main content area
st.subheader("🤖 DocSense AI Assistant")
st.caption(f"{'💬 Chat Mode' if st.session_state.mode == 'chat' else '📚 Document Q&A with Vector Search'}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and st.session_state.mode == 'document':
            df = extract_numerical_data(message["content"])
            if df is not None and not df.empty:
                display_response_with_visuals(message["content"], show_charts=True)
            else:
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Check if documents are needed
    if st.session_state.mode == 'document' and not st.session_state.documents_loaded:
        st.warning("⚠️ Please upload and process documents first!")
        st.stop()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            if st.session_state.mode == 'chat':
                # Chat Mode: Pure GROQ conversation
                chat_engine = get_chat_mode()
                
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    chat_history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                for chunk in chat_engine.stream_response(
                    prompt,
                    detail_level.lower(),
                    chat_history
                ):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                
            else:
                # Document Mode: Vector search + Mistral + GROQ
                vector_store = get_vector_store()
                query_engine = get_hybrid_query_engine()
                
                # Semantic + keyword search
                relevant_docs = vector_store.semantic_search(
                    prompt,
                    top_k=5,
                    keyword_boost=0.3
                )
                
                if not relevant_docs:
                    full_response = "❌ No relevant documents found. Please upload documents related to your question."
                else:
                    # Use hybrid query engine
                    for chunk in query_engine.query(
                        prompt,
                        relevant_docs,
                        detail_level.lower()
                    ):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
            
            # Final response with visual formatting
            response_placeholder.empty()
            
            df = extract_numerical_data(full_response)
            if df is not None and not df.empty and st.session_state.mode == 'document':
                display_response_with_visuals(full_response, show_charts=True)
            else:
                st.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            response_placeholder.error(error_msg)
            logger.error(f"Chat error: {str(e)}", exc_info=True)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🤖 GROQ: Answer Generation")
with col2:
    st.caption("🔍 Mistral: Document Retrieval")
with col3:
    st.caption("🧠 FAISS: Vector Search")

# Info expandable
with st.expander("ℹ️ About DocSense v2"):
    st.markdown("""
    ### Features
    - **Vector Search**: FAISS-based semantic embeddings for intelligent document retrieval
    - **Hybrid Retrieval**: Combines semantic similarity with keyword matching
    - **Dual-Model Pipeline**: Mistral extracts context, GROQ generates answers
    - **Structured Data**: Automatic extraction of numerical data from PDFs
    - **Visual Output**: Auto-generates tables and interactive charts
    - **Persistent Memory**: Vector index can be saved/loaded for faster access
    
    ### How It Works
    1. Upload PDFs → Extract text → Create semantic embeddings
    2. Store in FAISS vector index for fast similarity search
    3. Query → Find relevant chunks (semantic + keyword)
    4. Mistral summarizes → GROQ formats answer
    5. Display with tables/charts
    
    ### Models
    - Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
    - Retrieval: `mistralai/mistral-7b-instruct:free`
    - Generation: `llama-3.3-70b-versatile`
    """)
