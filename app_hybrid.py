"""
DocSense - Hybrid AI Research Assistant (ChromaDB-Free Version)

Architecture:
- Chat Mode: GROQ (Llama 3.3) for general conversation
- Document Mode: Mistral (OpenRouter) for retrieval + GROQ for answering
- Storage: In-memory document store (no vector DB required)

Author: AI Assistant
Created: November 2025
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
    from simple_document_mode import (
        get_simple_document_store,
        process_uploaded_files
    )
    from table_formatter import display_response_with_visuals, extract_numerical_data
except ImportError as e:
    st.error(f"Failed to import modules: {str(e)}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="DocSense - AI Assistant",
    page_icon="🤖",
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
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'mode' not in st.session_state:
    st.session_state.mode = 'chat'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False

# Header
st.markdown('<div class="main-header">🤖 DocSense AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Powered by GROQ + Mistral</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Mode selection
    mode = st.radio(
        "Select Mode",
        ["💬 Chat Mode", "📚 Document Mode"],
        index=0 if st.session_state.mode == 'chat' else 1
    )
    
    if "Chat" in mode:
        st.session_state.mode = 'chat'
        st.markdown('<div class="mode-badge chat-mode-badge">Chat Mode Active</div>', unsafe_allow_html=True)
        st.info("General conversation with GROQ Llama 3.3")
    else:
        st.session_state.mode = 'document'
        st.markdown('<div class="mode-badge doc-mode-badge">Document Mode Active</div>', unsafe_allow_html=True)
        st.info("Q&A from your documents using Mistral + GROQ")
    
    st.divider()
    
    # Document upload (only in document mode)
    if st.session_state.mode == 'document':
        st.subheader("📄 Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Upload PDF or TXT files",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="Upload documents to ask questions about them"
        )
        
        if uploaded_files:
            if st.button("🚀 Process Documents", use_container_width=True):
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                status_container = st.container()
                
                def update_progress(current, total, message):
                    """Callback to update progress."""
                    if total > 0:
                        progress = int((current / total) * 100)
                        progress_bar.progress(progress)
                        progress_text.text(f"{message} ({current}/{total})")
                
                try:
                    update_progress(0, 1, "Starting document processing...")
                    
                    if process_uploaded_files(uploaded_files, update_progress):
                        progress_bar.progress(100)
                        progress_text.text("✓ Processing complete!")
                        st.session_state.documents_loaded = True
                        import time
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    progress_text.empty()
                    progress_bar.empty()
        
        # Show document stats
        if st.session_state.documents_loaded:
            doc_store = get_simple_document_store()
            stats = doc_store.get_stats()
            
            st.success("✓ Documents Loaded")
            st.metric("Total Chunks", stats['total_documents'])
            st.metric("Total Characters", f"{stats['total_chars']:,}")
            
            with st.expander("📁 Loaded Files"):
                for source in stats['sources']:
                    st.text(f"• {source}")
            
            if st.button("🗑️ Clear Documents", use_container_width=True):
                doc_store.clear()
                st.session_state.documents_loaded = False
                st.session_state.messages = []
                st.rerun()
    
    st.divider()
    
    # Response settings
    st.subheader("🎛️ Response Settings")
    detail_level = st.selectbox(
        "Detail Level",
        ["Brief", "Detailed"],
        index=1
    )
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.caption("DocSense v2.0 - Hybrid Architecture")

# Main chat interface
st.subheader(f"{'💬 General Chat' if st.session_state.mode == 'chat' else '📚 Document Q&A'}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and st.session_state.mode == 'document':
            # Check if message contains structured data
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
                
                # Format conversation history properly
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
                # Document Mode: Mistral retrieval + GROQ answering
                doc_store = get_simple_document_store()
                query_engine = get_hybrid_query_engine()
                
                # Search documents
                relevant_docs = doc_store.search(prompt, top_k=5)
                
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
            response_placeholder.empty()  # Clear the streaming placeholder
            
            # Check if response contains structured data
            df = extract_numerical_data(full_response)
            
            if df is not None and not df.empty and st.session_state.mode == 'document':
                # Display with tables and charts
                display_response_with_visuals(full_response, show_charts=True)
            else:
                # Regular markdown display
                st.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            response_placeholder.error(error_msg)
            logger.error(f"Chat error: {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🤖 GROQ: Answer Generation")
with col2:
    st.caption("🔍 Mistral: Document Retrieval")
with col3:
    st.caption("💾 In-Memory Storage")
