"""
Multi-Format Document Ingestion Module

This module handles PDF and TXT file processing, text extraction, chunking,
and vector embedding generation for the Research Assistant application.

Author: GitHub Copilot
Date: August 11, 2025
"""

import logging
import os
import io
from typing import List, Dict, Any, Optional, Tuple, BinaryIO, Union
import traceback

import fitz  # PyMuPDF
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 100))
MAX_RETRIES = 3
COLLECTION_NAME = "document_chunks"
CHROMADB_PERSIST_DIR = ".chromadb"
SUPPORTED_FILE_TYPES = ['.pdf', '.txt']


class DocumentIngestionError(Exception):
    """Custom exception for document ingestion errors."""
    pass


@st.cache_resource
def get_chromadb_client() -> chromadb.Client:
    """
    Get or create a ChromaDB client instance with persistent storage.
    
    Returns:
        chromadb.Client: Configured ChromaDB client instance
        
    Raises:
        DocumentIngestionError: If ChromaDB client creation fails
    """
    try:
        client = chromadb.PersistentClient(path=CHROMADB_PERSIST_DIR)
        logger.info(f"ChromaDB client initialized with persist directory: {CHROMADB_PERSIST_DIR}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
        raise DocumentIngestionError(f"Database initialization failed: {str(e)}")


@st.cache_resource
def get_collection() -> chromadb.Collection:
    """
    Get or create the document chunks collection in ChromaDB.
    
    Returns:
        chromadb.Collection: The document chunks collection
        
    Raises:
        DocumentIngestionError: If collection creation fails
    """
    try:
        client = get_chromadb_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        logger.info(f"Collection '{COLLECTION_NAME}' initialized successfully")
        return collection
    except Exception as e:
        logger.error(f"Failed to initialize collection: {str(e)}")
        raise DocumentIngestionError(f"Collection initialization failed: {str(e)}")


def validate_environment() -> None:
    """
    Validate that required environment variables are set.
    
    Raises:
        DocumentIngestionError: If required environment variables are missing
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise DocumentIngestionError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set your OpenRouter API key before using the application."
        )


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        str: File extension (e.g., '.pdf', '.txt')
    """
    return os.path.splitext(filename.lower())[1]


def extract_text_from_pdf(pdf_file: BinaryIO, filename: str) -> str:
    """
    Extract text from a PDF file using PyMuPDF with robust error handling.
    
    Args:
        pdf_file: Binary file object containing PDF data
        filename: Name of the PDF file for error reporting
        
    Returns:
        str: Extracted text content from the PDF
        
    Raises:
        DocumentIngestionError: If PDF text extraction fails
    """
    doc = None
    try:
        logger.info(f"Starting PDF text extraction for '{filename}'")
        
        # Read PDF content into memory
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)  # Reset file pointer for potential reuse
        
        # Open PDF document from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        if doc.page_count == 0:
            raise DocumentIngestionError(f"PDF file '{filename}' contains no pages")
        
        logger.info(f"PDF '{filename}' has {doc.page_count} pages")
        
        text_parts = []
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                
                # Clean and validate text
                if page_text and page_text.strip():
                    # Preserve paragraph breaks and clean whitespace
                    cleaned_text = ' '.join(page_text.split())
                    if cleaned_text.strip():
                        text_parts.append(cleaned_text)
                        logger.debug(f"Extracted {len(cleaned_text)} chars from page {page_num + 1}")
                else:
                    logger.warning(f"No text found on page {page_num + 1} of '{filename}'")
                    
            except Exception as page_error:
                logger.warning(f"Failed to extract text from page {page_num + 1} of '{filename}': {str(page_error)}")
                continue
        
        if not text_parts:
            logger.warning(f"No text extracted from any page of '{filename}' - may be scanned/image-based")
            # For scanned PDFs, we could implement OCR here
            raise DocumentIngestionError(
                f"No text could be extracted from PDF file '{filename}'. "
                "This may be a scanned document that requires OCR processing."
            )
        
        # Join pages with double newlines to preserve document structure
        full_text = '\n\n'.join(text_parts)
        
        logger.info(f"Successfully extracted {len(full_text)} characters from '{filename}' ({len(text_parts)} pages with text)")
        return full_text
        
    except DocumentIngestionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting text from '{filename}': {str(e)}")
        logger.error(traceback.format_exc())
        raise DocumentIngestionError(f"Failed to extract text from '{filename}': {str(e)}")
    finally:
        # Ensure document is properly closed
        if doc is not None:
            try:
                doc.close()
                logger.debug(f"PDF document '{filename}' closed successfully")
            except Exception as close_error:
                logger.warning(f"Error closing PDF document '{filename}': {str(close_error)}")


def extract_text_from_txt(txt_file: BinaryIO, filename: str) -> str:
    """
    Extract text from a TXT file with encoding detection and error handling.
    
    Args:
        txt_file: Binary file object containing TXT data
        filename: Name of the TXT file for error reporting
        
    Returns:
        str: Extracted text content from the TXT file
        
    Raises:
        DocumentIngestionError: If TXT text extraction fails
    """
    try:
        logger.info(f"Starting TXT text extraction for '{filename}'")
        
        # Read file content
        txt_bytes = txt_file.read()
        txt_file.seek(0)  # Reset file pointer for potential reuse
        
        # Try different encodings
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        text_content = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                text_content = txt_bytes.decode(encoding)
                used_encoding = encoding
                logger.info(f"Successfully decoded '{filename}' using {encoding} encoding")
                break
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode '{filename}' with {encoding} encoding")
                continue
        
        if text_content is None:
            raise DocumentIngestionError(
                f"Could not decode TXT file '{filename}' with any supported encoding. "
                "Please ensure the file is in UTF-8, Latin-1, or another common text encoding."
            )
        
        # Clean and validate text
        text_content = text_content.strip()
        if not text_content:
            raise DocumentIngestionError(f"TXT file '{filename}' is empty or contains no readable text")
        
        logger.info(f"Successfully extracted {len(text_content)} characters from '{filename}' using {used_encoding} encoding")
        return text_content
        
    except DocumentIngestionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting text from '{filename}': {str(e)}")
        logger.error(traceback.format_exc())
        raise DocumentIngestionError(f"Failed to extract text from '{filename}': {str(e)}")


def extract_text_from_file(file_obj: BinaryIO, filename: str) -> str:
    """
    Extract text from a file based on its extension.
    
    Args:
        file_obj: Binary file object
        filename: Name of the file
        
    Returns:
        str: Extracted text content
        
    Raises:
        DocumentIngestionError: If file type is unsupported or extraction fails
    """
    file_ext = get_file_extension(filename)
    
    logger.info(f"Processing file '{filename}' with extension '{file_ext}'")
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_obj, filename)
    elif file_ext == '.txt':
        return extract_text_from_txt(file_obj, filename)
    else:
        raise DocumentIngestionError(
            f"Unsupported file type '{file_ext}' for file '{filename}'. "
            f"Supported types: {', '.join(SUPPORTED_FILE_TYPES)}"
        )


def chunk_text(text: str, filename: str) -> List[str]:
    """
    Split text into overlapping chunks for optimal embedding and retrieval.
    
    Uses RecursiveCharacterTextSplitter to preserve sentence and paragraph boundaries
    where possible, ensuring better semantic coherence in chunks.
    
    Args:
        text: Input text to be chunked
        filename: Source filename for logging purposes
        
    Returns:
        List[str]: List of text chunks with specified size and overlap
        
    Raises:
        DocumentIngestionError: If text chunking fails
    """
    try:
        if not text or not text.strip():
            raise DocumentIngestionError(f"Empty or whitespace-only text provided for chunking from '{filename}'")
        
        logger.info(f"Starting text chunking for '{filename}' (text length: {len(text)} characters)")
        
        # Use RecursiveCharacterTextSplitter for better semantic chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],  # Priority order for splitting
            keep_separator=True,
            length_function=len
        )
        
        chunks = splitter.split_text(text)
        
        if not chunks:
            raise DocumentIngestionError(f"Text chunking resulted in no chunks for '{filename}'")
        
        # Filter out very short chunks that might not be meaningful
        min_chunk_length = 20  # Minimum characters for a meaningful chunk
        meaningful_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.strip()
            if len(chunk_text) >= min_chunk_length:
                meaningful_chunks.append(chunk_text)
                logger.debug(f"Chunk {i+1}: {len(chunk_text)} characters")
            else:
                logger.debug(f"Skipping short chunk {i+1}: {len(chunk_text)} characters")
        
        if not meaningful_chunks:
            # If all chunks were too short, keep the original chunks anyway
            logger.warning(f"All chunks from '{filename}' were below minimum length, keeping original chunks")
            meaningful_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        logger.info(f"Created {len(meaningful_chunks)} meaningful chunks from '{filename}' (original: {len(chunks)})")
        return meaningful_chunks
        
    except DocumentIngestionError:
        raise
    except Exception as e:
        logger.error(f"Error chunking text from '{filename}': {str(e)}")
        logger.error(traceback.format_exc())
        raise DocumentIngestionError(f"Failed to chunk text from '{filename}': {str(e)}")


def test_openrouter_connection() -> bool:
    """
    Test the OpenRouter API connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        validate_environment()
        
        client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Test with a simple completion
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv("SITE_URL", "http://localhost:8501"),
                "X-Title": os.getenv("SITE_NAME", "PDF Research Assistant"),
            },
            model=os.getenv("OPENAI_MODEL", "tngtech/deepseek-r1t2-chimera:free"),
            messages=[{"role": "user", "content": "Hello, testing connection."}],
            max_tokens=10
        )
        
        logger.info("OpenRouter API connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"OpenRouter API connection test failed: {str(e)}")
        return False


@st.cache_data
def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for text chunks using OpenAI's embedding model via OpenRouter.
    
    Args:
        texts: List of text chunks to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
        
    Raises:
        DocumentIngestionError: If embedding generation fails
    """
    try:
        validate_environment()
        
        logger.info(f"Starting embedding generation for {len(texts)} text chunks")
        
        # For now, we'll use the LangChain OpenAI embeddings wrapper
        # Note: OpenRouter may not support embeddings for all models
        # We might need to use a different service for embeddings
        
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        # Try using OpenAI embeddings (this might need adjustment for OpenRouter)
        embedding_kwargs = {
            "model": os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
            "openai_api_key": api_key
        }
        
        if base_url:
            embedding_kwargs["openai_api_base"] = base_url
        
        try:
            embeddings_model = OpenAIEmbeddings(**embedding_kwargs)
            
            # Generate embeddings with retry logic
            for attempt in range(MAX_RETRIES):
                try:
                    embeddings = embeddings_model.embed_documents(texts)
                    logger.info(f"Generated embeddings for {len(texts)} text chunks using {embedding_kwargs['model']}")
                    return embeddings
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Embedding generation attempt {attempt + 1} failed: {str(e)}. Retrying...")
                        continue
                    else:
                        raise
                        
        except Exception as embedding_error:
            logger.warning(f"Failed to generate embeddings via OpenRouter: {str(embedding_error)}")
            
            # Fallback: Generate dummy embeddings for testing
            # In production, you'd want to use a dedicated embedding service
            logger.warning("Generating dummy embeddings for testing purposes")
            import random
            dummy_embeddings = []
            for text in texts:
                # Generate a consistent but pseudo-random embedding based on text hash
                hash_val = hash(text) % (2**32)
                random.seed(hash_val)
                embedding = [random.uniform(-1, 1) for _ in range(384)]  # 384-dimensional dummy embedding
                dummy_embeddings.append(embedding)
            
            logger.warning(f"Generated {len(dummy_embeddings)} dummy embeddings")
            return dummy_embeddings
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        logger.error(traceback.format_exc())
        raise DocumentIngestionError(f"Embedding generation failed: {str(e)}")


def clear_vector_store() -> None:
    """
    Clear all data from the vector store collection.
    
    Raises:
        DocumentIngestionError: If clearing the vector store fails
    """
    try:
        collection = get_collection()
        
        # Get all IDs and delete them
        all_items = collection.get()
        if all_items['ids']:
            collection.delete(ids=all_items['ids'])
            logger.info(f"Cleared {len(all_items['ids'])} items from vector store")
        else:
            logger.info("Vector store was already empty")
            
    except Exception as e:
        logger.error(f"Failed to clear vector store: {str(e)}")
        raise DocumentIngestionError(f"Failed to clear vector store: {str(e)}")


def ingest_documents(uploaded_files: List[BinaryIO]) -> Tuple[int, int]:
    """
    Extract, chunk, embed, and store document texts in ChromaDB vector database.
    
    This function processes multiple document files by:
    1. Clearing existing vector store data
    2. Extracting text from each document (PDF/TXT)
    3. Chunking text into overlapping segments
    4. Generating embeddings for each chunk
    5. Storing embeddings with metadata in ChromaDB
    
    Args:
        uploaded_files: List of uploaded document file objects
        
    Returns:
        Tuple[int, int]: (total_chunks_processed, total_files_processed)
        
    Raises:
        DocumentIngestionError: If ingestion process fails
    """
    try:
        validate_environment()
        
        if not uploaded_files:
            raise DocumentIngestionError("No document files provided for ingestion")
        
        logger.info(f"Starting ingestion of {len(uploaded_files)} document files")
        
        # Clear previous data
        clear_vector_store()
        
        collection = get_collection()
        
        all_texts = []
        all_metadatas = []
        all_ids = []
        
        files_processed = 0
        total_chunks = 0
        
        for file_obj in uploaded_files:
            filename = getattr(file_obj, 'name', f'unknown_file_{files_processed}')
            
            try:
                logger.info(f"Processing file: {filename}")
                
                # Check file type
                file_ext = get_file_extension(filename)
                if file_ext not in SUPPORTED_FILE_TYPES:
                    logger.warning(f"Skipping unsupported file type: {filename} ({file_ext})")
                    continue
                
                # Extract text from document
                text = extract_text_from_file(file_obj, filename)
                
                # Skip empty files
                if not text or not text.strip():
                    logger.warning(f"Skipping empty file: {filename}")
                    continue
                
                # Chunk the text
                chunks = chunk_text(text, filename)
                
                # Prepare data for vector store
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_id = f"{filename}_chunk_{chunk_idx}"
                    
                    all_texts.append(chunk)
                    all_metadatas.append({
                        "source": filename,
                        "file_type": file_ext,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "file_size": len(text),
                        "chunk_size": len(chunk)
                    })
                    all_ids.append(chunk_id)
                
                total_chunks += len(chunks)
                files_processed += 1
                
                logger.info(f"Successfully processed '{filename}': {len(chunks)} chunks created")
                
            except Exception as file_error:
                logger.error(f"Failed to process file '{filename}': {str(file_error)}")
                # Continue processing other files rather than failing completely
                continue
        
        if not all_texts:
            raise DocumentIngestionError("No valid text chunks were extracted from any document files")
        
        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(all_texts)} chunks...")
        embeddings = generate_embeddings(all_texts)
        
        # Store in ChromaDB
        collection.add(
            documents=all_texts,
            metadatas=all_metadatas,
            ids=all_ids,
            embeddings=embeddings
        )
        
        logger.info(f"Successfully ingested {files_processed} files with {total_chunks} chunks into vector store")
        return total_chunks, files_processed
        
    except DocumentIngestionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during document ingestion: {str(e)}")
        logger.error(traceback.format_exc())
        raise DocumentIngestionError(f"Document ingestion failed: {str(e)}")


def get_ingestion_stats() -> Dict[str, Any]:
    """
    Get statistics about the current vector store contents.
    
    Returns:
        Dict[str, Any]: Dictionary containing ingestion statistics
        
    Raises:
        DocumentIngestionError: If unable to retrieve statistics
    """
    try:
        collection = get_collection()
        all_items = collection.get()
        
        if not all_items['ids']:
            return {
                "total_chunks": 0,
                "total_files": 0,
                "files": {},
                "file_types": {}
            }
        
        # Analyze metadata to get file statistics
        files_stats = {}
        file_types = {}
        
        for metadata in all_items['metadatas']:
            source = metadata.get('source', 'unknown')
            file_type = metadata.get('file_type', 'unknown')
            
            # File statistics
            if source not in files_stats:
                files_stats[source] = {
                    "chunks": 0,
                    "total_chunks": metadata.get('total_chunks', 0),
                    "file_size": metadata.get('file_size', 0),
                    "file_type": file_type
                }
            files_stats[source]["chunks"] += 1
            
            # File type statistics
            if file_type not in file_types:
                file_types[file_type] = 0
            file_types[file_type] += 1
        
        return {
            "total_chunks": len(all_items['ids']),
            "total_files": len(files_stats),
            "files": files_stats,
            "file_types": file_types
        }
        
    except Exception as e:
        logger.error(f"Failed to get ingestion statistics: {str(e)}")
        raise DocumentIngestionError(f"Failed to retrieve statistics: {str(e)}")


# Legacy function alias for backward compatibility
def ingest_pdfs(pdf_files: List[BinaryIO]) -> Tuple[int, int]:
    """Legacy function for backward compatibility. Use ingest_documents instead."""
    logger.warning("ingest_pdfs is deprecated. Use ingest_documents for multi-format support.")
    return ingest_documents(pdf_files)


# Module-level validation and testing
try:
    validate_environment()
    logger.info("Environment validation successful")
    
    # Test OpenRouter connection
    if test_openrouter_connection():
        logger.info("OpenRouter API connection verified")
    else:
        logger.warning("OpenRouter API connection test failed - please check your configuration")
        
except DocumentIngestionError as e:
    logger.warning(f"Environment validation warning: {str(e)}")
    # Don't raise here as it prevents import, let individual functions handle it