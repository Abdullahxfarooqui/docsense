"""
Document Persistence Manager

Handles persistent storage of uploaded documents in /data folder.
Automatically loads existing documents on app startup.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import streamlit as st

logger = logging.getLogger(__name__)

# Data folder path
DATA_FOLDER = Path("data")
VECTOR_STORE_PATH = DATA_FOLDER / "vector_store.pkl"


def ensure_data_folder() -> Path:
    """
    Ensure data folder exists. Create if not.
    
    Returns:
        Path to data folder
    """
    DATA_FOLDER.mkdir(exist_ok=True)
    logger.info(f"Data folder ready: {DATA_FOLDER.absolute()}")
    return DATA_FOLDER


def get_existing_documents() -> List[Path]:
    """
    Get list of existing documents in data folder.
    
    Returns:
        List of Path objects for existing PDF/TXT files
    """
    ensure_data_folder()
    documents = []
    
    for ext in ['*.pdf', '*.txt']:
        documents.extend(DATA_FOLDER.glob(ext))
    
    logger.info(f"Found {len(documents)} existing documents")
    return sorted(documents)


def save_uploaded_file(uploaded_file, overwrite: bool = True) -> Path:
    """
    Save uploaded file to data folder.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        overwrite: If True, overwrite existing file with same name
        
    Returns:
        Path to saved file
    """
    ensure_data_folder()
    
    file_path = DATA_FOLDER / uploaded_file.name
    
    # Check if file already exists
    if file_path.exists() and not overwrite:
        logger.info(f"File already exists: {uploaded_file.name}")
        return file_path
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    logger.info(f"Saved file: {uploaded_file.name} ({uploaded_file.size} bytes)")
    return file_path


def save_multiple_files(uploaded_files: List) -> List[Path]:
    """
    Save multiple uploaded files to data folder.
    
    Args:
        uploaded_files: List of Streamlit UploadedFile objects
        
    Returns:
        List of Path objects for saved files
    """
    saved_paths = []
    
    for uploaded_file in uploaded_files:
        path = save_uploaded_file(uploaded_file, overwrite=True)
        saved_paths.append(path)
    
    return saved_paths


def load_document_from_path(file_path: Path) -> Dict[str, any]:
    """
    Load document from file path and return as file-like object.
    
    Args:
        file_path: Path to document
        
    Returns:
        Dictionary with file info compatible with document processor
    """
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Create a file-like object compatible with document processor
    class FileWrapper:
        def __init__(self, name, content):
            self.name = name
            self.content = content
            self.size = len(content)
            
        def read(self):
            return self.content
            
        def seek(self, pos):
            pass  # Not needed for our use case
    
    return FileWrapper(file_path.name, content)


def get_document_stats() -> Dict[str, any]:
    """
    Get statistics about stored documents.
    
    Returns:
        Dictionary with document statistics
    """
    documents = get_existing_documents()
    
    total_size = sum(doc.stat().st_size for doc in documents)
    
    return {
        'count': len(documents),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'files': [doc.name for doc in documents]
    }


def delete_document(filename: str) -> bool:
    """
    Delete a document from data folder.
    
    Args:
        filename: Name of file to delete
        
    Returns:
        True if successful
    """
    file_path = DATA_FOLDER / filename
    
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Deleted document: {filename}")
        return True
    
    logger.warning(f"Document not found: {filename}")
    return False


def clear_all_documents() -> int:
    """
    Clear all documents from data folder.
    
    Returns:
        Number of files deleted
    """
    documents = get_existing_documents()
    count = len(documents)
    
    for doc in documents:
        doc.unlink()
    
    logger.info(f"Cleared {count} documents from data folder")
    return count


def check_vector_store_exists() -> bool:
    """
    Check if vector store file exists.
    
    Returns:
        True if vector store exists
    """
    return VECTOR_STORE_PATH.exists()


def get_vector_store_age() -> float:
    """
    Get age of vector store in seconds.
    
    Returns:
        Age in seconds, or -1 if doesn't exist
    """
    if not VECTOR_STORE_PATH.exists():
        return -1
    
    import time
    mod_time = VECTOR_STORE_PATH.stat().st_mtime
    return time.time() - mod_time


def should_rebuild_vectors(documents: List[Path]) -> bool:
    """
    Determine if vector store needs rebuilding.
    
    Args:
        documents: List of document paths
        
    Returns:
        True if vectors need rebuilding
    """
    # No documents = no need to rebuild
    if not documents:
        return False
    
    # No vector store = needs building
    if not check_vector_store_exists():
        return True
    
    # Check if any document is newer than vector store
    vector_age = get_vector_store_age()
    
    for doc in documents:
        doc_age = doc.stat().st_mtime
        if doc_age > VECTOR_STORE_PATH.stat().st_mtime:
            logger.info(f"Document {doc.name} is newer than vector store")
            return True
    
    return False
