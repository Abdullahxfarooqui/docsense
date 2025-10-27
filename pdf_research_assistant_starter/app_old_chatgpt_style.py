"""
Research Assistant - Main Streamlit Application

A production-grade, modular Research Assistant web application with
professional UI and seamless user experience. This application allows users
to upload PDF and TXT documents, process them into a vector database, and ask
questions with AI-powered answers that include proper source citations.

Features:
- Multi-file upload with size validation (PDF/TXT)
- Robust text extraction and chunking
- Vector-based semantic search
- OpenRouter API powered question answering with citations
- Professional UI with error handling and caching
- Responsive design and accessibility

Author: AI Assistant
Created: August 2025
"""

import logging
import os
import sys
import time
from typing import List, Optional, Dict, Any
import traceback

import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import custom modules
try:
    from ingestion import ingest_documents, get_ingestion_stats, clear_vector_store, DocumentIngestionError
    from query_engine import get_query_engine, QueryEngineError
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
SUPPORTED_FORMATS = ["pdf", "txt"]  # Supported file formats

# Page configuration
st.set_page_config(
    page_title="Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "A professional Research Assistant built with Streamlit, LangChain, and OpenRouter API"
    }
)

# Custom CSS for professional styling
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    
    /* Dark mode support for upload info */
    @media (prefers-color-scheme: dark) {
        .upload-info {
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
    }
    
    .stats-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    
    .error-container {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    .success-container {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
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
    
    .answer-container {
        background-color: #ffffff;
        color: #212529;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        line-height: 1.6;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .answer-container {
            background-color: #343a40;
            color: #f8f9fa;
            border: 1px solid #6c757d;
        }
        .source-chunk {
            background-color: #495057;
            color: #f8f9fa;
            border-left: 3px solid #adb5bd;
        }
        .chunk-metadata {
            color: #adb5bd;
        }
        .stats-container {
            background-color: #495057;
            color: #f8f9fa;
            border: 1px solid #6c757d;
        }
    }
    
    .source-chunk {
        background-color: #f8f9fa;
        color: #212529;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #6c757d;
        margin: 0.5rem 0;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    .chunk-metadata {
        color: #495057;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .ask-button {
        background: linear-gradient(90deg, #1f77b4, #2e86de);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .ask-button:hover {
        background: linear-gradient(90deg, #1e6ba8, #2874c7);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)


def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        bool: True if environment is valid, False otherwise
    """
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
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size = size_bytes
    i = 0
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def display_upload_info(uploaded_files: List) -> bool:
    """
    Display upload information and validate file constraints.
    ENHANCED: Professional, centered, highly visible styling.
    
    Args:
        uploaded_files: List of uploaded files
        
    Returns:
        bool: True if upload is valid, False otherwise
    """
    if not uploaded_files:
        st.markdown("""
        <div class="upload-info">
            <strong>📄 No Documents Uploaded</strong>
            <div style="margin-top: 1rem;">
                Upload up to 5 PDF or TXT files<br>
                <span style="font-size: 0.9rem; opacity: 0.9;">Maximum 50MB total</span>
            </div>
            <div style="margin-top: 1.5rem; font-size: 0.95rem; opacity: 0.85;">
                👈 Use the sidebar to get started
            </div>
        </div>
        """, unsafe_allow_html=True)
        return False
    
    # Validate file count
    if len(uploaded_files) > MAX_FILES:
        st.markdown(f"""
        <div class="error-container">
            ❌ <strong>Too many files</strong><br>
            You uploaded {len(uploaded_files)} files, but the maximum is {MAX_FILES}.
            Please remove some files and try again.
        </div>
        """, unsafe_allow_html=True)
        return False
    
    # Calculate total size
    total_size = sum(file.size for file in uploaded_files)
    
    # Validate total size
    if total_size > MAX_TOTAL_SIZE_BYTES:
        st.markdown(f"""
        <div class="error-container">
            ❌ <strong>Upload size too large</strong><br>
            Total size: {format_file_size(total_size)} (limit: {MAX_TOTAL_SIZE_MB}MB)<br>
            Please reduce the total file size and try again.
        </div>
        """, unsafe_allow_html=True)
        return False
    
    # Display file information
    st.markdown(f"""
    <div class="success-container">
        ✅ <strong>Upload validated successfully</strong><br>
        Files: {len(uploaded_files)} / {MAX_FILES}<br>
        Total size: {format_file_size(total_size)} / {MAX_TOTAL_SIZE_MB}MB
    </div>
    """, unsafe_allow_html=True)
    
    # Show individual file details
    with st.expander("📋 View uploaded files", expanded=False):
        for i, file in enumerate(uploaded_files, 1):
            st.write(f"**{i}.** {file.name} ({format_file_size(file.size)})")
    
    return True


def display_ingestion_stats():
    """Display current ingestion statistics in the sidebar."""
    try:
        stats = get_ingestion_stats()
        
        if stats["total_chunks"] == 0:
            st.markdown("""
            <div class="stats-container">
                <strong>📊 Vector Store Status</strong><br>
                No documents processed yet
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="stats-container">
                <strong>📊 Vector Store Status</strong><br>
                📄 Files: {stats["total_files"]}<br>
                🔢 Chunks: {stats["total_chunks"]}<br>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ Clear Vector Store", help="Remove all processed documents"):
                try:
                    clear_vector_store()
                    st.success("Vector store cleared successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear vector store: {str(e)}")
                    
    except Exception as e:
        logger.error(f"Failed to get ingestion stats: {str(e)}")
        st.error("Unable to load vector store statistics")


def process_uploaded_files(uploaded_files: List) -> bool:
    """
    Process uploaded document files and ingest them into the vector store.
    
    ENHANCED with smart cache handling:
    - Computes file hash to detect changes
    - Only reprocesses if documents changed
    - Stores hash in session state
    
    Args:
        uploaded_files: List of uploaded files
        
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        # Get current session document hash (if any)
        session_doc_hash = st.session_state.get('current_doc_hash', None)
        
        with st.spinner("🔄 Processing documents and generating embeddings..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Update progress
            status_text.text("Checking for document changes...")
            progress_bar.progress(15)
            
            # Compute hash first to check if we need to reprocess
            from ingestion import compute_file_hash
            current_hash = compute_file_hash(uploaded_files)
            
            if session_doc_hash and session_doc_hash == current_hash:
                # Documents unchanged - skip processing
                status_text.text("Documents unchanged - using cached embeddings...")
                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                st.markdown("""
                <div class="success-container">
                    ✅ <strong>Documents already processed!</strong><br>
                    Using cached embeddings from previous upload.<br>
                    🎯 Ready for questions!
                </div>
                """, unsafe_allow_html=True)
                return True
            
            # Documents changed or first upload - process them
            status_text.text("Extracting text from documents...")
            progress_bar.progress(25)
            
            # Process files with hash tracking
            total_chunks, files_processed, doc_hash = ingest_documents(uploaded_files, session_doc_hash)
            
            # Store hash in session state
            st.session_state.current_doc_hash = doc_hash
            
            progress_bar.progress(75)
            status_text.text("Finalizing vector store...")
            
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            change_indicator = "🔄 Updated" if session_doc_hash else "✨ New"
            
            st.markdown(f"""
            <div class="success-container">
                ✅ <strong>{change_indicator} - Processing completed successfully!</strong><br>
                📄 Files processed: {files_processed}<br>
                🔢 Text chunks created: {total_chunks}<br>
                🎯 Ready for questions!
            </div>
            """, unsafe_allow_html=True)
            
            return True
            
    except DocumentIngestionError as e:
        logger.error(f"Document ingestion error: {str(e)}")
        st.markdown(f"""
        <div class="error-container">
            ❌ <strong>Processing failed</strong><br>
            {str(e)}
        </div>
        """, unsafe_allow_html=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during processing: {str(e)}")
        logger.error(traceback.format_exc())
        st.markdown(f"""
        <div class="error-container">
            ❌ <strong>Unexpected error occurred</strong><br>
            Please try again or contact support if the problem persists.
        </div>
        """, unsafe_allow_html=True)
        return False


def display_answer_and_sources(answer: str, sources: List, show_sources: bool):
    """
    Display the generated answer and optionally the source chunks.
    
    Args:
        answer: Generated answer text
        sources: List of source chunks with metadata
        show_sources: Whether to display source chunks
    """
    # Display answer with performance indicator
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### 🤖 Answer")
    with col2:
        # Show performance indicator if available in session state
        if 'last_search_time' in st.session_state:
            search_time = st.session_state.last_search_time
            if search_time < 3:
                st.success(f"⚡ {search_time:.1f}s")
            elif search_time < 5:
                st.warning(f"⏱️ {search_time:.1f}s")
            else:
                st.error(f"🐌 {search_time:.1f}s")
    
    st.markdown(f"""
    <div class="answer-container">
        {answer}
    </div>
    """, unsafe_allow_html=True)
    
    # Display sources if requested
    if show_sources and sources:
        st.markdown("### 📚 Source Chunks")
        
        for idx, (source_name, chunk_content, metadata) in enumerate(sources, 1):
            chunk_index = metadata.get('chunk_index', idx - 1)
            similarity_score = metadata.get('similarity_score', 0.0)
            
            with st.expander(
                f"📄 {source_name} - Chunk {chunk_index + 1} (Similarity: {similarity_score:.3f})",
                expanded=False
            ):
                st.markdown(f"""
                <div class="source-chunk">
                    <div class="chunk-metadata">
                        Source: {source_name} | Chunk: {chunk_index + 1} | 
                        Similarity: {similarity_score:.3f} | 
                        Length: {len(chunk_content)} chars
                    </div>
                    {chunk_content}
                </div>
                """, unsafe_allow_html=True)


def handle_question_answering():
    """Handle the question answering interface and logic."""
    try:
        # Get ingestion stats to check if documents are available
        stats = get_ingestion_stats()
        
        if stats["total_chunks"] == 0:
            st.markdown("""
            <div class="warning-container">
                ⚠️ <strong>No documents available</strong><br>
                Please upload and process some PDF files before asking questions.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Question input
        st.markdown("### 💬 Ask Your Question")
        question = st.text_input(
            label="Enter your question here...",
            placeholder="e.g., What are the main findings discussed in the research?",
            label_visibility="collapsed",
            key="user_question"
        )
        
        # Ask button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            ask_button = st.button(
                "🔍 Ask",
                disabled=not question.strip(),
                help="Click to search documents and generate an answer",
                use_container_width=True
            )
        
        # Process question if submitted
        if ask_button and question.strip():
            try:
                # IMMEDIATE FEEDBACK - Show thinking message instantly
                thinking_placeholder = st.empty()
                with thinking_placeholder.container():
                    st.markdown("### 💭 ")
                    st.markdown("🤖 **Analyzing your question and searching document context...**")
                
                # Get query engine
                query_engine = get_query_engine()
                
                # STEP 1: Retrieve chunks with visible spinner
                with st.spinner("� Retrieving relevant sections from your documents..."):
                    answer_stream, sources, metrics = query_engine.answer_question_streaming(
                        question.strip(),
                        thinking_placeholder=thinking_placeholder
                    )
                
                # STEP 2: Prepare for streaming
                # If retrieval took time but model not started yet, show different message
                if thinking_placeholder:
                    with thinking_placeholder.container():
                        st.markdown("### 💭 ")
                        st.markdown("🧩 **Deep model reasoning in progress...**")
                        st.caption("_Synthesizing information from multiple sources_")
                
                # STEP 3: Stream the answer with live updates
                st.markdown("### 💬 Answer")
                answer_placeholder = st.empty()
                full_answer = ""
                
                # Stream response in real-time (thinking placeholder cleared on first token)
                for chunk in answer_stream:
                    full_answer += chunk
                    # Update with cursor to show it's live
                    answer_placeholder.markdown(full_answer + "▌")
                
                # Remove cursor and show final answer
                answer_placeholder.markdown(full_answer)
                
                # Display performance metrics
                st.caption(f"⚡ Retrieved {metrics.get('chunks_used', 0)} chunks in {metrics.get('retrieval_time', 0):.2f}s")
                
                # Get show sources preference
                show_sources = st.session_state.get('show_sources', False)
                
                # Display sources if available and requested
                if show_sources and sources:
                    st.markdown("---")
                    st.markdown("### 📚 Sources")
                    for i, chunk in enumerate(sources, 1):
                        metadata = chunk.get('metadata', {})
                        source_name = metadata.get('source', 'Unknown')
                        chunk_index = metadata.get('chunk_index', 'N/A')
                        content = chunk.get('content', '')[:300]  # Preview
                        
                        with st.expander(f"📄 Source {i}: {source_name} (Chunk {chunk_index})"):
                            st.markdown(f"```\n{content}...\n```")
                    
            except QueryEngineError as e:
                logger.error(f"Query engine error: {str(e)}")
                st.markdown(f"""
                <div class="error-container">
                    ❌ <strong>Question processing failed</strong><br>
                    {str(e)}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                logger.error(f"Unexpected error during question answering: {str(e)}")
                logger.error(traceback.format_exc())
                st.markdown("""
                <div class="error-container">
                    ❌ <strong>An unexpected error occurred</strong><br>
                    Please try again or rephrase your question.
                </div>
                """, unsafe_allow_html=True)
                
    except Exception as e:
        logger.error(f"Error in question answering interface: {str(e)}")
        st.error("Failed to load question answering interface")


def render_sidebar():
    """Render the sidebar with upload controls and settings."""
    with st.sidebar:
        st.markdown("## 📁 Document Upload")
        
        # File uploader
        uploaded_files = st.file_uploader(
            label="Upload Documents (PDF/TXT)",
            type=SUPPORTED_FORMATS,
            accept_multiple_files=True,
            help=f"Upload up to {MAX_FILES} PDF or TXT files, maximum {MAX_TOTAL_SIZE_MB}MB total",
            key="document_uploader"
        )
        
        # Display upload validation
        is_upload_valid = display_upload_info(uploaded_files)
        
        # Process button
        if uploaded_files and is_upload_valid:
            if st.button("🚀 Process Documents", use_container_width=True):
                if process_uploaded_files(uploaded_files):
                    st.rerun()
        
        st.markdown("---")
        
        # Settings section
        st.markdown("## ⚙️ Settings")
        
        # Show sources toggle
        show_sources = st.checkbox(
            "Show Source Chunks in Answers",
            value=st.session_state.get('show_sources', False),
            help="Display the original document chunks that were used to generate the answer",
            key="show_sources_checkbox"
        )
        st.session_state['show_sources'] = show_sources
        
        st.markdown("---")
        
        # Statistics and management
        st.markdown("## 📊 Status")
        display_ingestion_stats()
        
        # Clear session button
        if st.button("🔄 Reset Session", help="Clear all uploaded files and cached data"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Session reset successfully!")
            st.rerun()


def main() -> None:
    """
    Main Streamlit application entrypoint.
    
    ChatGPT-STYLE CONVERSATION MODE:
    - Persistent chat history
    - Multi-turn conversations
    - Streaming responses
    - Document persistence across queries
    """
    try:
        # INITIALIZE SESSION STATE - ChatGPT style
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'query_cache' not in st.session_state:
            st.session_state.query_cache = {}
        if 'show_sources' not in st.session_state:
            st.session_state.show_sources = False
        if 'documents_processed' not in st.session_state:
            st.session_state.documents_processed = False
        if 'current_doc_hash' not in st.session_state:
            st.session_state.current_doc_hash = None  # Track document changes
            
        # Validate environment
        if not validate_environment():
            st.stop()
        
        # Main header
        st.markdown("""
        <div class="main-header">
            📚 DocSense: ChatGPT for Your Research Documents
        </div>
        """, unsafe_allow_html=True)
        
        # Render sidebar
        render_sidebar()
        
        # MAIN CHAT INTERFACE
        st.markdown("### 💬 Conversation")
        
        # Check if documents are processed
        try:
            stats = get_ingestion_stats()
            has_documents = stats["total_chunks"] > 0
        except:
            has_documents = False
        
        # Smart status indicator
        if has_documents:
            doc_count = stats.get('total_files', 0)
            chunk_count = stats.get('total_chunks', 0)
            st.caption(f"📚 {doc_count} document{'s' if doc_count != 1 else ''} loaded ({chunk_count} chunks)")
        else:
            st.caption("💡 Upload documents to unlock document-based Q&A, or chat normally")
        
        # Display chat history (ChatGPT style)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                # Show sources if available and user wants them
                if message["role"] == "assistant" and "sources" in message and st.session_state.show_sources:
                    if message["sources"]:
                        with st.expander("📚 View Sources"):
                            for i, source in enumerate(message["sources"], 1):
                                metadata = source.get('metadata', {})
                                st.caption(f"**Source {i}**: {metadata.get('source', 'Unknown')} (Chunk {metadata.get('chunk_index', 'N/A')})")
                                st.code(source.get('content', '')[:300] + "...")
        
        # Chat input (always visible, like ChatGPT)
        prompt_placeholder = "Ask a question about your documents..." if has_documents else "Chat with DocSense AI..."
        
        if prompt := st.chat_input(prompt_placeholder):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate assistant response
            with st.chat_message("assistant"):
                thinking_placeholder = st.empty()
                
                try:
                    # SMART MODE: Detect if documents should be used
                    # Show appropriate thinking message based on context
                    if has_documents:
                        with thinking_placeholder.container():
                            st.markdown("🤖 **Analyzing your question...**")
                    else:
                        with thinking_placeholder.container():
                            st.markdown("🤖 **Thinking...**")
                    
                    # Get query engine
                    query_engine = get_query_engine()
                    
                    # Build context from recent messages (last 3-5 for memory)
                    context_messages = st.session_state.messages[-6:-1] if len(st.session_state.messages) > 1 else []
                    context_text = ""
                    if context_messages:
                        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context_messages[-3:]])
                    
                    # Add context to query if available
                    enhanced_query = prompt
                    if context_text:
                        enhanced_query = f"Previous context:\n{context_text}\n\nCurrent question: {prompt}"
                    
                    # SMART RETRIEVAL: Let query engine decide whether to use documents
                    answer_stream, sources, metrics = query_engine.answer_question_streaming(
                        enhanced_query,
                        thinking_placeholder=thinking_placeholder
                    )
                    
                    # Stream the response
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    for chunk in answer_stream:
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    # Final answer
                    response_placeholder.markdown(full_response)
                    
                    # Performance metrics (only if documents were used)
                    if metrics.get('document_used', False):
                        chunks_used = metrics.get('chunks_used', 0)
                        retrieval_time = metrics.get('retrieval_time', 0)
                        if chunks_used > 0:
                            st.caption(f"📚 Retrieved {chunks_used} document chunks in {retrieval_time:.2f}s")
                    
                    # Save assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources if sources else []
                    })
                    
                except QueryEngineError as e:
                    error_msg = f"❌ Query failed: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })
                except Exception as e:
                    logger.error(f"Unexpected error: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_msg = "❌ An unexpected error occurred. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })
        
        # Clear chat button (top right)
        if len(st.session_state.messages) > 0:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col3:
                if st.button("🗑️ Clear Chat", help="Clear conversation history"):
                    st.session_state.messages = []
                    st.rerun()
        
        # Footer information
        st.markdown("---")
        with st.expander("ℹ️ About DocSense", expanded=False):
            st.markdown("""
            **DocSense** - ChatGPT-style Research Assistant for Your Documents
            
            **Features:**
            - 💬 **Multi-Turn Conversations**: Ask follow-up questions naturally
            - � **Persistent Documents**: Upload once, query multiple times
            - ⚡ **Streaming Responses**: See answers appear in real-time
            - 🎯 **Context Awareness**: Remembers recent conversation for better answers
            - 🔍 **Smart Retrieval**: Cached searches for lightning-fast responses
            - � **Source Citations**: See exactly where information comes from
            
            **Technologies:**
            - DeepSeek R1T2 Chimera (via OpenRouter)
            - ChromaDB Vector Database
            - Streamlit UI Framework
            - LangChain Document Processing
            """)
            
    except Exception as e:
        logger.error(f"Critical error in main application: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("""
        🚨 **Critical Application Error**
        
        The application encountered a critical error and cannot continue.
        Please check the logs and restart the application.
        """)
        st.stop()


if __name__ == "__main__":
    main()