"""
DocSense - PDF Research Assistant
REFACTORED: Two Completely Isolated Modes

🧠 Chat Mode: Pure conversational AI (no documents, no RAG)
📚 Document Mode: Strict RAG (only uploaded documents, no pretrained knowledge)

Author: AI Assistant
Last Updated: October 2025
"""

import logging
import os
import sys
import time
from typing import List, Optional, Dict, Any
import traceback

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import mode modules
try:
    from chat_mode import get_chat_mode, ChatModeError
    from document_mode import get_document_mode, DocumentModeError
    from ingestion import ingest_documents, get_ingestion_stats, clear_vector_store, DocumentIngestionError, compute_file_hash
except ImportError as e:
    st.error(f"Failed to import required modules: {str(e)}")
    st.stop()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_FILES = 5
MAX_TOTAL_SIZE_MB = 50
MAX_TOTAL_SIZE_BYTES = MAX_TOTAL_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = ["pdf", "txt"]

# Page configuration
st.set_page_config(
    page_title="DocSense - AI Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .mode-indicator {
        text-align: center;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .chat-mode {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .doc-mode {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .upload-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 16px;
        text-align: center;
        margin: 3rem auto;
        max-width: 600px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        font-size: 1.1rem;
        line-height: 1.8;
    }
    
    .upload-info strong {
        display: block;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .success-container {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .error-container {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    .warning-container {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .upload-info {
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables for both modes."""
    # Mode selection
    if 'mode' not in st.session_state:
        st.session_state.mode = 'chat'  # Default to chat mode
    
    # Chat Mode state (completely isolated)
    if 'chat_mode_history' not in st.session_state:
        st.session_state.chat_mode_history = []
    
    # Document Mode state (completely isolated)
    if 'doc_mode_history' not in st.session_state:
        st.session_state.doc_mode_history = []
    
    # Document tracking
    if 'current_doc_hash' not in st.session_state:
        st.session_state.current_doc_hash = None
    
    # UI preferences
    if 'show_sources' not in st.session_state:
        st.session_state.show_sources = True
    
    if 'detail_level' not in st.session_state:
        st.session_state.detail_level = 'auto'


def validate_environment() -> bool:
    """Validate required environment variables."""
    if not os.getenv("OPENAI_API_KEY"):
        st.error("""
        🔑 **OpenAI API Key Required**
        
        Please set your OpenAI API key as an environment variable:
        
        **Linux/macOS:**
        ```bash
        export OPENAI_API_KEY="your_api_key_here"
        ```
        
        **Windows:**
        ```cmd
        set OPENAI_API_KEY="your_api_key_here"
        ```
        
        Then restart the application.
        """)
        return False
    return True


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size = size_bytes
    i = 0
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def render_mode_selector():
    """Render mode selection radio buttons."""
    st.markdown("### 🧭 Select Mode")
    
    mode_options = {
        '🧠 Chat Mode': 'chat',
        '📚 Document Mode': 'document'
    }
    
    selected_label = '🧠 Chat Mode' if st.session_state.mode == 'chat' else '📚 Document Mode'
    
    mode_selection = st.radio(
        "Choose your interaction mode:",
        options=list(mode_options.keys()),
        index=0 if st.session_state.mode == 'chat' else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Update mode if changed
    new_mode = mode_options[mode_selection]
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        logger.info(f"Mode switched to: {new_mode}")
        st.rerun()


def render_mode_info():
    """Render information about current mode."""
    if st.session_state.mode == 'chat':
        st.markdown("""
        <div class="mode-indicator chat-mode">
            🧠 <strong>Chat Mode Active</strong><br>
            <span style="font-size: 0.9rem;">General AI assistant - No document retrieval</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mode-indicator doc-mode">
            📚 <strong>Document Mode Active</strong><br>
            <span style="font-size: 0.9rem;">Strict RAG - Answers only from your uploaded documents</span>
        </div>
        """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with mode-specific controls."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Detail level control
        st.markdown("### Response Style")
        detail_options = {
            'Auto (Adaptive)': 'auto',
            'Brief': 'brief',
            'Detailed': 'detailed'
        }
        
        detail_label = [k for k, v in detail_options.items() if v == st.session_state.detail_level][0]
        
        detail_selection = st.selectbox(
            "Response Detail Level",
            options=list(detail_options.keys()),
            index=list(detail_options.values()).index(st.session_state.detail_level),
            help="Auto adapts to query complexity, Brief for concise answers, Detailed for comprehensive analysis"
        )
        st.session_state.detail_level = detail_options[detail_selection]
        
        st.markdown("---")
        
        # Document Mode specific controls
        if st.session_state.mode == 'document':
            st.markdown("## 📁 Document Upload")
            
            uploaded_files = st.file_uploader(
                label="Upload Documents (PDF/TXT)",
                type=SUPPORTED_FORMATS,
                accept_multiple_files=True,
                help=f"Upload up to {MAX_FILES} files, maximum {MAX_TOTAL_SIZE_MB}MB total",
                key="document_uploader"
            )
            
            if uploaded_files:
                # Validate upload
                if len(uploaded_files) > MAX_FILES:
                    st.error(f"❌ Too many files. Maximum: {MAX_FILES}")
                else:
                    total_size = sum(f.size for f in uploaded_files)
                    if total_size > MAX_TOTAL_SIZE_BYTES:
                        st.error(f"❌ Total size too large: {format_file_size(total_size)} (limit: {MAX_TOTAL_SIZE_MB}MB)")
                    else:
                        st.success(f"✅ {len(uploaded_files)} file(s) validated ({format_file_size(total_size)})")
                        
                        if st.button("🚀 Process Documents", use_container_width=True):
                            process_documents(uploaded_files)
            
            st.markdown("---")
            
            # Show document stats
            st.markdown("## 📊 Document Status")
            try:
                stats = get_ingestion_stats()
                if stats["total_chunks"] > 0:
                    st.info(f"📄 Files: {stats['total_files']}\n\n🔢 Chunks: {stats['total_chunks']}")
                    
                    # Show sources toggle
                    st.session_state.show_sources = st.checkbox(
                        "Show Source Citations",
                        value=st.session_state.show_sources,
                        help="Display document chunks used for answers"
                    )
                    
                    if st.button("🗑️ Clear Documents", help="Remove all uploaded documents"):
                        clear_vector_store()
                        st.session_state.current_doc_hash = None
                        st.session_state.doc_mode_history = []
                        st.success("Documents cleared!")
                        st.rerun()
                else:
                    st.warning("⚠️ No documents uploaded yet")
            except Exception as e:
                st.error(f"Error loading stats: {str(e)}")
        
        else:
            # Chat Mode info
            st.markdown("## 💬 Chat Mode")
            st.info("""
            **Chat Mode** provides general AI assistance without accessing any documents.
            
            Perfect for:
            • General questions
            • Brainstorming
            • Learning concepts
            • Casual conversation
            """)
        
        st.markdown("---")
        
        # Clear chat button for current mode
        if st.session_state.mode == 'chat' and len(st.session_state.chat_mode_history) > 0:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_mode_history = []
                st.success("Chat history cleared!")
                st.rerun()
        elif st.session_state.mode == 'document' and len(st.session_state.doc_mode_history) > 0:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.doc_mode_history = []
                st.success("Document chat history cleared!")
                st.rerun()


def process_documents(uploaded_files: List):
    """Process uploaded documents for Document Mode."""
    try:
        session_doc_hash = st.session_state.get('current_doc_hash', None)
        
        with st.spinner("🔄 Processing documents..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Checking for changes...")
            progress_bar.progress(15)
            
            # Compute hash
            current_hash = compute_file_hash(uploaded_files)
            
            if session_doc_hash and session_doc_hash == current_hash:
                status_text.text("Documents unchanged - using cache...")
                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                st.markdown("""
                <div class="success-container">
                    ✅ <strong>Documents already processed!</strong><br>
                    Using cached embeddings from previous upload.
                </div>
                """, unsafe_allow_html=True)
                return
            
            status_text.text("Extracting text...")
            progress_bar.progress(35)
            
            total_chunks, files_processed, doc_hash = ingest_documents(uploaded_files, session_doc_hash)
            st.session_state.current_doc_hash = doc_hash
            
            progress_bar.progress(90)
            status_text.text("Finalizing...")
            
            progress_bar.progress(100)
            progress_bar.empty()
            status_text.empty()
            
            change_indicator = "🔄 Updated" if session_doc_hash else "✨ New"
            
            st.markdown(f"""
            <div class="success-container">
                ✅ <strong>{change_indicator} - Processing complete!</strong><br>
                📄 Files: {files_processed} | 🔢 Chunks: {total_chunks}<br>
                🎯 Ready for document-based Q&A!
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        st.markdown(f"""
        <div class="error-container">
            ❌ <strong>Processing failed</strong><br>
            {str(e)}
        </div>
        """, unsafe_allow_html=True)


def handle_chat_mode():
    """Handle Chat Mode interface and logic."""
    st.markdown("### 💬 Chat with AI")
    
    # Display chat history
    for message in st.session_state.chat_mode_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.chat_mode_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            
            try:
                with thinking_placeholder.container():
                    st.markdown("🤖 **Thinking...**")
                
                # Get chat mode
                chat_mode = get_chat_mode()
                
                # Generate response
                response_stream, metadata = chat_mode.generate_response(
                    query=prompt,
                    detail_level=st.session_state.detail_level,
                    conversation_history=st.session_state.chat_mode_history,
                    thinking_placeholder=thinking_placeholder
                )
                
                # Stream response
                response_placeholder = st.empty()
                full_response = ""
                
                for chunk in response_stream:
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                
                # Show metadata
                detail_level = metadata.get('detail_level', 'auto')
                st.caption(f"💬 Chat Mode | {detail_level.capitalize()} response")
                
                # Save to history
                st.session_state.chat_mode_history.append({"role": "assistant", "content": full_response})
                
            except ChatModeError as e:
                error_msg = f"❌ Chat Mode error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_mode_history.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                logger.error(f"Unexpected error in Chat Mode: {str(e)}")
                logger.error(traceback.format_exc())
                error_msg = "❌ An unexpected error occurred. Please try again."
                st.error(error_msg)
                st.session_state.chat_mode_history.append({"role": "assistant", "content": error_msg})


def handle_document_mode():
    """Handle Document Mode interface and logic."""
    # Check if documents are available
    try:
        stats = get_ingestion_stats()
        has_documents = stats["total_chunks"] > 0
    except:
        has_documents = False
    
    if not has_documents:
        st.markdown("""
        <div class="upload-info">
            <strong>📄 No Documents Uploaded</strong>
            <div style="margin-top: 1rem;">
                Upload PDF or TXT files using the sidebar<br>
                <span style="font-size: 0.9rem; opacity: 0.9;">Maximum 5 files, 50MB total</span>
            </div>
            <div style="margin-top: 1.5rem; font-size: 0.95rem; opacity: 0.85;">
                👈 Use the sidebar to get started with Document Mode
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("### 📚 Document Q&A")
    st.caption(f"📊 {stats['total_files']} document(s) loaded | {stats['total_chunks']} chunks indexed")
    
    # Display document mode history
    for message in st.session_state.doc_mode_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources if available
            if message["role"] == "assistant" and "sources" in message and st.session_state.show_sources:
                if message["sources"]:
                    with st.expander("📚 View Source Citations"):
                        for i, source in enumerate(message["sources"], 1):
                            metadata = source.get('metadata', {})
                            similarity = source.get('similarity', 0.0)
                            st.caption(f"**[Source {i}]**: {metadata.get('source', 'Unknown')} (Chunk {metadata.get('chunk_index', 'N/A')}, Relevance: {similarity:.2f})")
                            st.code(source.get('content', '')[:400] + "...")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.doc_mode_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            
            try:
                with thinking_placeholder.container():
                    st.markdown("🔍 **Searching documents...**")
                
                # Get document mode
                doc_mode = get_document_mode()
                
                # Generate RAG response
                response_stream, sources, metadata = doc_mode.answer_from_documents(
                    query=prompt,
                    detail_level=st.session_state.detail_level,
                    conversation_history=st.session_state.doc_mode_history,
                    thinking_placeholder=thinking_placeholder
                )
                
                # Stream response
                response_placeholder = st.empty()
                full_response = ""
                
                for chunk in response_stream:
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                
                response_placeholder.markdown(full_response)
                
                # Show metadata if successful
                if not metadata.get('error'):
                    chunks_retrieved = metadata.get('chunks_retrieved', 0)
                    detail_level = metadata.get('detail_level', 'auto')
                    st.caption(f"📚 Document Mode | Retrieved {chunks_retrieved} chunks | {detail_level.capitalize()} response")
                
                # Save to history
                st.session_state.doc_mode_history.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": sources
                })
                
            except DocumentModeError as e:
                error_msg = f"❌ Document Mode error: {str(e)}"
                st.error(error_msg)
                st.session_state.doc_mode_history.append({"role": "assistant", "content": error_msg, "sources": []})
            except Exception as e:
                logger.error(f"Unexpected error in Document Mode: {str(e)}")
                logger.error(traceback.format_exc())
                error_msg = "❌ An unexpected error occurred. Please try again."
                st.error(error_msg)
                st.session_state.doc_mode_history.append({"role": "assistant", "content": error_msg, "sources": []})


def main():
    """Main application entry point."""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Validate environment
        if not validate_environment():
            st.stop()
        
        # Main header
        st.markdown("""
        <div class="main-header">
            📚 DocSense: AI Research Assistant
        </div>
        """, unsafe_allow_html=True)
        
        # Mode selector
        render_mode_selector()
        
        # Mode indicator
        render_mode_info()
        
        # Sidebar
        render_sidebar()
        
        # Main content based on mode
        if st.session_state.mode == 'chat':
            handle_chat_mode()
        else:
            handle_document_mode()
        
        # Footer
        st.markdown("---")
        with st.expander("ℹ️ About DocSense", expanded=False):
            st.markdown("""
            **DocSense** - Two Isolated AI Modes
            
            **🧠 Chat Mode:**
            - General conversational AI
            - No document retrieval
            - Adaptive response depth
            - Perfect for learning and brainstorming
            
            **📚 Document Mode:**
            - Strict RAG (Retrieval-Augmented Generation)
            - Answers ONLY from uploaded documents
            - Rich citations [Source 1], [Source 2]
            - Perfect for research and analysis
            
            **Technologies:**
            - DeepSeek R1T2 Chimera (via OpenRouter)
            - ChromaDB Vector Database
            - Streamlit UI Framework
            - LangChain Document Processing
            """)
    
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("🚨 Critical application error. Please check logs and restart.")
        st.stop()


if __name__ == "__main__":
    main()
