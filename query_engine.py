"""
Query Engine Module with OpenRouter Integration - OPTIMIZED VERSION

This module handles vector database querying, context retrieval, and LLM prompting
for the DocSense Research Assistant. Enhanced with:
- Streaming responses for better UX
- Improved chunking with overlap
- Better prompt engineering
- File hashing for cache optimization
- Retry logic with exponential backoff
- Performance monitoring

Author: AI Assistant
Created: August 2025
Last Updated: October 2025
"""

import logging
import os
from typing import List, Tuple, Dict, Any, Optional, Generator
import time
from datetime import datetime, timedelta
import hashlib

import streamlit as st
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np

from ingestion import get_collection, DocumentIngestionError

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants - OPTIMIZED VALUES
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "tngtech/deepseek-r1t2-chimera:free")
DEFAULT_TEMPERATURE = 0.1
MAX_RETRIES = 3  # Retry attempts with exponential backoff
TOP_K_RESULTS = 5  # Retrieve more chunks for better context (increased from 3)
CHUNK_SIZE = 1000  # Optimal chunk size for processing
CHUNK_OVERLAP = 200  # Overlap between chunks to maintain context continuity
CACHE_EXPIRY_MINUTES = 30
CHUNK_SEPARATOR = "\n---\n"  # Clear separator between document chunks


class QueryEngineError(Exception):
    """Custom exception for query engine errors."""
    pass


class QueryEngine:
    """
    OPTIMIZED query engine for semantic search and question answering.
    
    Enhancements:
    - Streaming responses for progressive UI updates
    - File hashing for intelligent caching
    - Improved chunking with overlap
    - Better prompt engineering for detailed answers
    - Retry logic with exponential backoff
    - Performance monitoring and logging
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
        """
        Initialize the QueryEngine with optimized configuration.
        
        Args:
            model_name: OpenRouter model to use for answer generation
            temperature: Sampling temperature for response generation (0.0 to 1.0)
            
        Raises:
            QueryEngineError: If initialization fails
        """
        try:
            self._validate_environment()
            
            self.model_name = model_name
            self.temperature = temperature
            
            # Get API configuration from environment
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
            self.site_url = os.getenv("SITE_URL", "http://localhost:8501")
            self.site_name = os.getenv("SITE_NAME", "DocSense Research Assistant")
            
            # Initialize OpenRouter client
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            # Test the connection with retry logic
            self._test_connection()
            
            # Get ChromaDB collection
            self.collection = get_collection()
            
            # Initialize caches in session state
            if 'query_cache' not in st.session_state:
                st.session_state.query_cache = {}
            if 'file_hashes' not in st.session_state:
                st.session_state.file_hashes = {}  # Track processed files by hash
            
            logger.info(f"✓ QueryEngine initialized with model: {model_name}, temperature: {temperature}")
            logger.info(f"✓ Using TOP_K={TOP_K_RESULTS}, CHUNK_SIZE={CHUNK_SIZE}, OVERLAP={CHUNK_OVERLAP}")
            
        except Exception as e:
            logger.error(f"Failed to initialize QueryEngine: {str(e)}")
            raise QueryEngineError(f"QueryEngine initialization failed: {str(e)}")
    
    def _validate_environment(self) -> None:
        """
        Validate that required environment variables are set.
        
        Raises:
            QueryEngineError: If required environment variables are missing
        """
        if not os.getenv("OPENAI_API_KEY"):
            raise QueryEngineError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set your OpenRouter API key before using the application."
            )
    
    def _test_connection(self) -> None:
        """
        Test the OpenRouter API connection with exponential backoff retry logic.
        
        Raises:
            QueryEngineError: If connection test fails after all retries
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": self.site_url,
                        "X-Title": self.site_name,
                    },
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Connection test"}],
                    max_tokens=5
                )
                logger.info("✓ OpenRouter API connection test successful")
                return
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Connection attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {MAX_RETRIES} connection attempts failed")
                    raise QueryEngineError(f"Failed to connect to OpenRouter API: {str(e)}")
    
    def compute_file_hash(self, file_content: bytes) -> str:
        """
        Compute MD5 hash of file content for intelligent caching.
        
        Args:
            file_content: Binary content of the file
            
        Returns:
            MD5 hash as hexadecimal string
        """
        return hashlib.md5(file_content).hexdigest()
    
    def is_file_cached(self, file_hash: str) -> bool:
        """
        Check if a file's embeddings are already in ChromaDB cache.
        
        Args:
            file_hash: MD5 hash of the file
            
        Returns:
            True if file is cached, False otherwise
        """
        return file_hash in st.session_state.file_hashes
    
    def normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """
        Normalize embeddings for consistent cosine similarity search.
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            Normalized embedding vectors (L2 normalization)
        """
        try:
            embeddings_array = np.array(embeddings)
            norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
            # Avoid division by zero
            norms[norms == 0] = 1
            normalized = embeddings_array / norms
            return normalized.tolist()
        except Exception as e:
            logger.warning(f"Embedding normalization failed: {str(e)}. Using original embeddings.")
            return embeddings
    
    @st.cache_data(ttl=1800, show_spinner=False)  # Cache for 30 minutes
    def retrieve_relevant_chunks(_self, user_query: str) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant document chunks from ChromaDB.
        CACHED to avoid re-searching identical queries.
        
        Args:
            user_query: The user's question
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            retrieval_start = time.time()
            
            # Get collection count
            collection_count = _self.collection.count()
            logger.info(f"📊 Searching through {collection_count} document chunks")
            
            if collection_count == 0:
                logger.warning("No documents in collection")
                return []
            
            # Use ChromaDB's query method for fast text-based search
            results = _self.collection.query(
                query_texts=[user_query],
                n_results=min(TOP_K_RESULTS, collection_count)
            )
            
            # Format results into structured chunks
            relevant_chunks = []
            if results and results.get('documents') and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    chunk = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'distance': results['distances'][0][i] if results.get('distances') else 0.0,
                        'id': results['ids'][0][i] if results.get('ids') else f'chunk_{i}'
                    }
                    relevant_chunks.append(chunk)
            
            retrieval_time = time.time() - retrieval_start
            logger.info(f"✓ Retrieved {len(relevant_chunks)} chunks in {retrieval_time:.3f}s")
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Chunk retrieval failed: {str(e)}")
            raise QueryEngineError(f"Failed to retrieve relevant chunks: {str(e)}")
    
    def build_prompt(self, user_query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Build an optimized, detailed prompt for the LLM with proper structure.
        
        Args:
            user_query: The user's question
            retrieved_chunks: List of relevant document chunks
            
        Returns:
            Formatted prompt string
        """
        # Format chunks with clear separators and source information
        formatted_excerpts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            metadata = chunk.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            chunk_index = metadata.get('chunk_index', 'N/A')
            content = chunk.get('content', '')
            
            formatted_excerpts.append(
                f"[Source {i}: {source}, Chunk {chunk_index}]\n{content}"
            )
        
        # Join with clear separator
        context = CHUNK_SEPARATOR.join(formatted_excerpts)
        
        # Build the optimized prompt with detailed instructions
        prompt = f"""You are DocSense, an intelligent research assistant that answers questions using the provided document excerpts.

INSTRUCTIONS:
• Give a detailed, contextually rich, and accurate answer
• Use bullet points and short paragraphs for clarity
• Include document citations in format: [Source X] or [Source X, Chunk Y]
• If the excerpts don't fully answer the question, acknowledge this
• Structure your response logically with clear sections if needed
• Be comprehensive but concise

QUESTION:
{user_query}

RELEVANT DOCUMENT EXCERPTS:
{context}

ANSWER:"""
        
        return prompt
    
    def stream_answer(self, prompt: str, thinking_placeholder=None) -> Generator[str, None, None]:
        """
        Stream the answer from OpenRouter API with retry logic and UX feedback.
        
        Args:
            prompt: The formatted prompt for the LLM
            thinking_placeholder: Streamlit placeholder to clear when streaming starts
            
        Yields:
            Text chunks as they arrive from the API
        """
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"🤖 Generating answer using {self.model_name} (streaming mode)")
                
                # Track time to first token
                api_call_start = time.time()
                
                # Create streaming completion
                stream = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": self.site_url,
                        "X-Title": self.site_name,
                    },
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=1500,
                    stream=True
                )
                
                # Track if first token received
                first_token_received = False
                first_token_time = None
                
                # Stream the response
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        # Clear thinking placeholder on first token
                        if not first_token_received:
                            first_token_time = time.time() - api_call_start
                            logger.info(f"⚡ First token received in {first_token_time:.2f}s")
                            if thinking_placeholder:
                                thinking_placeholder.empty()
                            first_token_received = True
                        
                        yield chunk.choices[0].delta.content
                
                return  # Successful streaming, exit retry loop
                
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"Streaming attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {MAX_RETRIES} streaming attempts failed")
                    if thinking_placeholder:
                        thinking_placeholder.empty()
                    yield f"\n\n❌ Error: Failed to generate answer after {MAX_RETRIES} attempts. Please try again."
    
    def query_documents(self, user_query: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, float]]:
        """
        Main query function - retrieve relevant chunks and generate streaming answer.
        
        Args:
            user_query: The user's question
            
        Returns:
            Tuple of (answer, source_chunks, performance_metrics)
        """
        try:
            total_start = time.time()
            
            # Step 1: Retrieve relevant chunks
            logger.info(f"📝 Processing query: {user_query[:100]}...")
            retrieval_start = time.time()
            relevant_chunks = self.retrieve_relevant_chunks(user_query)
            retrieval_time = time.time() - retrieval_start
            
            if not relevant_chunks:
                logger.warning("No relevant chunks found")
                return (
                    "I couldn't find any relevant information in the uploaded documents to answer your question. Please upload relevant documents or try rephrasing your question.",
                    [],
                    {'retrieval_time': retrieval_time, 'generation_time': 0, 'total_time': time.time() - total_start, 'chunks_used': 0}
                )
            
            # Step 2: Build optimized prompt
            prompt = self.build_prompt(user_query, relevant_chunks)
            
            # Step 3: Generate answer (will be streamed in the UI)
            # For now, return empty string as answer will be streamed separately
            performance_metrics = {
                'retrieval_time': retrieval_time,
                'chunks_used': len(relevant_chunks),
                'total_time': time.time() - total_start
            }
            
            logger.info(f"✓ Query processed in {performance_metrics['total_time']:.3f}s")
            logger.info(f"  └─ Retrieval: {retrieval_time:.3f}s, Chunks: {len(relevant_chunks)}")
            
            return (prompt, relevant_chunks, performance_metrics)
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            raise QueryEngineError(f"Failed to process query: {str(e)}")
    
    def answer_question_streaming(self, question: str, thinking_placeholder=None, use_documents: bool = True) -> Tuple[Generator[str, None, None], List[Dict[str, Any]], Dict[str, float]]:
        """
        Answer a question with streaming response and intelligent context handling.
        
        ENHANCED with smart document detection:
        - Checks if documents are available
        - Responds without retrieval if no documents or question is generic
        - Only uses ChromaDB when relevant to uploaded documents
        
        Args:
            question: The user's question
            thinking_placeholder: Streamlit placeholder for "thinking" message
            use_documents: Whether to attempt document retrieval (auto-detected)
            
        Returns:
            Tuple of (answer_generator, source_chunks, performance_metrics)
        """
        try:
            total_start = time.time()
            
            # Check if documents are available in ChromaDB
            collection_count = self.collection.count()
            
            # SMART DECISION: Should we use documents?
            if collection_count == 0:
                # No documents uploaded - respond generically
                logger.info("No documents in collection - responding without retrieval")
                if thinking_placeholder:
                    thinking_placeholder.empty()
                
                def generic_response():
                    generic_prompt = f"""You are DocSense, a helpful AI assistant. The user hasn't uploaded any documents yet.

INSTRUCTIONS:
• Answer the question naturally and helpfully
• If the question requires documents, politely inform them to upload relevant files
• Be conversational and friendly
• Provide useful information when possible

QUESTION:
{question}

ANSWER:"""
                    
                    yield from self.stream_answer(generic_prompt, None)
                
                metrics = {'retrieval_time': 0, 'chunks_used': 0, 'total_time': time.time() - total_start, 'document_used': False}
                return (generic_response(), [], metrics)
            
            # Documents exist - check if question is document-related
            # Simple heuristic: keywords that suggest document reference
            doc_keywords = [
                'document', 'pdf', 'file', 'paper', 'research', 'study', 'report',
                'article', 'text', 'uploaded', 'provided', 'according to', 'mentioned',
                'states', 'shows', 'describes', 'explains', 'discusses', 'analyzes'
            ]
            
            question_lower = question.lower()
            seems_document_related = any(keyword in question_lower for keyword in doc_keywords)
            
            # Also check if question is very short/generic (likely not document-specific)
            is_generic_chat = len(question.split()) <= 3 and not seems_document_related
            
            if is_generic_chat and not seems_document_related:
                # Generic chat question - respond without heavy retrieval
                logger.info(f"Question appears generic - light retrieval mode: {question[:50]}")
                if thinking_placeholder:
                    thinking_placeholder.empty()
                
                def light_response():
                    light_prompt = f"""You are DocSense, a helpful AI assistant.

QUESTION:
{question}

ANSWER (be brief and friendly):"""
                    
                    yield from self.stream_answer(light_prompt, None)
                
                metrics = {'retrieval_time': 0, 'chunks_used': 0, 'total_time': time.time() - total_start, 'document_used': False}
                return (light_response(), [], metrics)
            
            # Question seems document-related OR documents exist - do full retrieval
            logger.info(f"📝 Processing question with document retrieval: {question[:100]}...")
            prompt, chunks, metrics = self.query_documents(question)
            
            if not chunks:
                # No relevant chunks found - inform user
                if thinking_placeholder:
                    thinking_placeholder.empty()
                    
                def no_chunks_response():
                    yield "I searched through the uploaded documents but couldn't find relevant information to answer your question. The documents might not contain information on this topic, or you may need to rephrase your question."
                
                metrics['document_used'] = True
                return (no_chunks_response(), [], metrics)
            
            # Stream the answer with document context
            generation_start = time.time()
            answer_stream = self.stream_answer(prompt, thinking_placeholder)
            
            # Update metrics
            metrics['generation_start'] = generation_start
            metrics['document_used'] = True
            
            return (answer_stream, chunks, metrics)
            
        except Exception as e:
            logger.error(f"Question answering failed: {str(e)}")
            if thinking_placeholder:
                thinking_placeholder.empty()
            def error_generator():
                yield f"❌ Error: {str(e)}"
            return (error_generator(), [], {'retrieval_time': 0, 'chunks_used': 0, 'total_time': 0, 'document_used': False})


# Cached factory function for Streamlit
@st.cache_resource
def get_query_engine(model_name: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> QueryEngine:
    """
    Get or create a cached QueryEngine instance.
    
    Args:
        model_name: OpenRouter model to use
        temperature: Sampling temperature
        
    Returns:
        QueryEngine instance
    """
    return QueryEngine(model_name=model_name, temperature=temperature)
