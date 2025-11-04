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

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import mode modules
try:
    from chat_mode import get_chat_mode, ChatModeError
    from document_mode import get_document_mode, DocumentModeError
    from ingestion import ingest_documents, get_ingestion_stats, clear_vector_store, DocumentIngestionError, compute_file_hash
    from chromadb_manager import get_chromadb_manager
    CHROMADB_MANAGER_AVAILABLE = True
except ImportError as e:
    if "chromadb_manager" not in str(e):
        st.error(f"Failed to import required modules: {str(e)}")
        st.stop()
    CHROMADB_MANAGER_AVAILABLE = False
    logger.warning("ChromaDB manager not available")

# Constants
MAX_FILES = 5
MAX_TOTAL_SIZE_MB = 50
MAX_TOTAL_SIZE_BYTES = MAX_TOTAL_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = ["pdf", "txt", "xlsx", "xls", "csv", "xlsm"]

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
    
    /* ENHANCED: No files uploaded message - highly visible in both themes */
    .no-files-message {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white !important;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        text-align: center;
        margin: 2rem auto;
        max-width: 650px;
        box-shadow: 0 10px 30px rgba(255, 107, 107, 0.4);
        font-size: 1.3rem;
        font-weight: 700;
        line-height: 1.8;
        border: 3px solid rgba(255, 255, 255, 0.3);
    }
    
    .no-files-message p {
        color: white !important;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* ADDED: Status indicators for visual feedback */
    .status-ready {
        background: #10b981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .status-processing {
        background: #f59e0b;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        font-weight: 600;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    
    .status-error {
        background: #ef4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
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
    
    # OPTIMIZATION: Track processed files to skip re-embedding
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = {}  # {file_hash: filename}
    
    # UI preferences
    if 'show_sources' not in st.session_state:
        st.session_state.show_sources = True
    
    if 'detail_level' not in st.session_state:
        st.session_state.detail_level = 'detailed'  # Default to detailed mode
    
    # ADDED: Intent tracking for context awareness
    if 'last_intent' not in st.session_state:
        st.session_state.last_intent = None
    
    if 'last_mode' not in st.session_state:
        st.session_state.last_mode = None


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
        old_mode = st.session_state.mode
        st.session_state.mode = new_mode
        st.session_state.last_mode = old_mode
        logger.info(f"Mode switched: {old_mode} → {new_mode}")
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
        
        # ENHANCED: Response Detail Level toggle (Brief vs Detailed)
        st.markdown("### 📝 Response Detail Level")
        detail_options = {
            'Brief (Concise)': 'brief',
            'Detailed (Default)': 'detailed'
        }
        
        detail_selection = st.radio(
            "Choose response style:",
            options=list(detail_options.keys()),
            index=list(detail_options.values()).index(st.session_state.detail_level),
            help="Brief: Max 4 sentences | Detailed: Comprehensive research-grade answers (≥2000 tokens)",
            horizontal=False
        )
        st.session_state.detail_level = detail_options[detail_selection]
        
        st.markdown("---")
        
        # Document Mode specific controls
        if st.session_state.mode == 'document':
            st.markdown("## 📁 Document Upload")
            
            # AUTO-PROCESSING: File uploader with on_change callback
            uploaded_files = st.file_uploader(
                label="Upload Documents (PDF/TXT/Excel/CSV)",
                type=SUPPORTED_FORMATS,
                accept_multiple_files=True,
                help=f"Upload up to {MAX_FILES} files, max {MAX_TOTAL_SIZE_MB}MB total\n\n✨ Documents process automatically on upload!\n\n📊 Supports: PDF, TXT, Excel (.xlsx, .xls), CSV",
                key="document_uploader",
                on_change=auto_process_documents  # AUTO-PROCESS ON UPLOAD
            )
            
            # NO PROCESS BUTTON - auto-processing handles it!
            
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
                    
                    # Database Health Tools
                    if CHROMADB_MANAGER_AVAILABLE:
                        st.markdown("---")
                        st.markdown("### 🔧 Database Tools")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🏥 Check Health", help="Verify database integrity"):
                                manager = get_chromadb_manager()
                                stats = manager.get_collection_stats()
                                if stats.get('healthy', False):
                                    st.success(f"✅ Healthy\n{stats['count']} docs")
                                else:
                                    st.warning(f"⚠️ Issues detected\n{stats.get('error', 'Unknown error')}")
                        
                        with col2:
                            if st.button("🔄 Rebuild Index", help="Fix database errors"):
                                with st.spinner("Rebuilding..."):
                                    manager = get_chromadb_manager()
                                    manager.rebuild_index()
                                    st.success("✅ Rebuilt! Re-upload documents.")
                                    st.rerun()
                    
                    st.markdown("---")
                    
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




def auto_process_documents():
    """
    AUTO-PROCESSING: Callback triggered when files are uploaded.
    Automatically processes documents without requiring button click.
    """
    uploaded_files = st.session_state.get('document_uploader', None)
    
    if not uploaded_files or len(uploaded_files) == 0:
        return
    
    # Validate upload
    if len(uploaded_files) > MAX_FILES:
        st.error(f"❌ Too many files. Maximum: {MAX_FILES}")
        return
    
    total_size = sum(f.size for f in uploaded_files)
    if total_size > MAX_TOTAL_SIZE_BYTES:
        st.error(f"❌ Total size too large: {format_file_size(total_size)} (limit: {MAX_TOTAL_SIZE_MB}MB)")
        return
    
    # Process immediately
    process_documents(uploaded_files)


def process_documents(uploaded_files: List):
    """Process uploaded documents for Document Mode with AUTO-PROCESSING."""
    try:
        session_doc_hash = st.session_state.get('current_doc_hash', None)
        
        # Compute hash
        current_hash = compute_file_hash(uploaded_files)
        
        # OPTIMIZATION: Check if already processed
        if session_doc_hash and session_doc_hash == current_hash:
            # Already processed - silently use cache
            logger.info(f"✅ Files already processed (hash: {current_hash[:8]}...)")
            return
        
        # Additional check: individual file tracking
        if current_hash in st.session_state.processed_files:
            logger.info(f"✅ Using cached embeddings for: {st.session_state.processed_files[current_hash]}")
            st.session_state.current_doc_hash = current_hash
            return
        
        # Show processing indicator
        with st.spinner("🔄 Auto-processing documents..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📄 Extracting text from documents...")
            progress_bar.progress(25)
            
            total_chunks, files_processed, doc_hash = ingest_documents(uploaded_files, session_doc_hash)
            st.session_state.current_doc_hash = doc_hash
            
            # Track processed files
            filenames = ", ".join([f.name for f in uploaded_files])
            st.session_state.processed_files[doc_hash] = filenames
            logger.info(f"📝 Cached embeddings: {filenames} (hash: {doc_hash[:8]}...)")
            
            progress_bar.progress(75)
            status_text.text("✨ Creating embeddings and indexing...")
            
            progress_bar.progress(100)
            time.sleep(0.3)
            progress_bar.empty()
            status_text.empty()
        
        # Show success message
        st.success(f"✅ **Documents processed successfully!** {files_processed} file(s), {total_chunks} chunks indexed. Ready for Q&A!")
        
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        st.error(f"❌ **Processing failed:** {str(e)}")


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
        # Clear "No files uploaded" message
        st.markdown("""
        <div class="no-files-message">
            <p><strong>📄 NO DOCUMENTS UPLOADED</strong></p>
            <div style="margin-top: 1.2rem; font-size: 1.1rem;">
                Upload PDF or TXT files using the sidebar to begin!
            </div>
            <div style="margin-top: 1rem; font-size: 0.95rem; opacity: 0.95;">
                📁 Maximum: 5 files, 50MB total<br>
                ✨ Documents process automatically on upload
            </div>
            <div style="margin-top: 1.5rem; font-size: 1rem; font-weight: 600;">
                👈 Use the sidebar to get started!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("### 📚 Document Q&A")
    
    # Status indicator
    if stats['total_chunks'] > 0:
        st.markdown('<div class="status-ready">🟢 Ready for Questions</div>', unsafe_allow_html=True)
    
    st.caption(f"📊 {stats['total_files']} document(s) | {stats['total_chunks']} chunks")
    
    # Display chat history
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
                            st.caption(f"**[Source {i}]**: {metadata.get('source', 'Unknown')} (Relevance: {similarity:.2f})")
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
                
                # Track intent
                intent = metadata.get('intent', 'document_query')
                st.session_state.last_intent = intent
                st.session_state.last_mode = 'document'
                
                # Show metadata
                if not metadata.get('error'):
                    chunks_retrieved = metadata.get('chunks_retrieved', 0)
                    detail_level = metadata.get('detail_level', 'auto')
                    retrieval_skipped = metadata.get('retrieval_skipped', False)
                    
                    # Clear feedback based on intent
                    if retrieval_skipped:
                        st.caption("💬 Chat message — no document search")
                    else:
                        st.caption(f"📚 Retrieved {chunks_retrieved} chunks | {detail_level.capitalize()}")
                
                # Save to history
                st.session_state.doc_mode_history.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": sources
                })
                
            except DocumentModeError as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.doc_mode_history.append({"role": "assistant", "content": error_msg, "sources": []})
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
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
