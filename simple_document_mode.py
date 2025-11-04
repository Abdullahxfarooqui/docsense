"""
Simple Document Mode - Without ChromaDB Dependency

This version uses in-memory document storage and simple text matching
for retrieval instead of vector embeddings, avoiding the ChromaDB compilation issue.

Author: AI Assistant
Created: November 2025
"""

import logging
import os
from typing import List, Dict, Any, Optional
import re
from difflib import SequenceMatcher

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class SimpleDocumentStore:
    """In-memory document storage with simple text-based retrieval."""
    
    def __init__(self):
        """Initialize document store."""
        self.documents: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_documents(self, docs: List[Dict[str, Any]]):
        """
        Add documents to the store.
        
        Args:
            docs: List of dicts with 'text', 'source', 'page' keys
        """
        self.documents.extend(docs)
        logger.info(f"Added {len(docs)} documents to store")
    
    def clear(self):
        """Clear all documents."""
        self.documents = []
        self.metadata = {}
        logger.info("Document store cleared")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search with priority for structured data.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        if not self.documents:
            return []
        
        # Extract keywords from query
        keywords = set(re.findall(r'\w+', query.lower()))
        
        # Detect if query is asking for metrics/summary
        summary_keywords = {'total', 'summary', 'all', 'overall', 'volume', 'production', 'metrics'}
        is_summary_query = bool(keywords & summary_keywords)
        
        # Score each document
        scored_docs = []
        for doc in self.documents:
            text_lower = doc['text'].lower()
            
            # Give priority to summary and structured data
            doc_type = doc.get('type', 'text')
            type_boost = 50 if doc_type == 'summary' else (30 if doc_type == 'structured_data' else 0)
            
            # Extra boost for summary queries
            if is_summary_query and doc_type in ['summary', 'structured_data']:
                type_boost += 100
            
            # Count keyword matches
            keyword_score = sum(1 for kw in keywords if kw in text_lower)
            
            # Calculate text similarity
            similarity = SequenceMatcher(None, query.lower(), text_lower[:500]).ratio()
            
            # Combined score with type priority
            total_score = keyword_score * 2 + similarity * 10 + type_boost
            
            if total_score > 0:
                scored_docs.append((total_score, doc))
        
        # Sort by score and return top k
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        results = [doc for _, doc in scored_docs[:top_k]]
        
        logger.info(f"Found {len(results)} relevant documents for query (summary query: {is_summary_query})")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "total_documents": len(self.documents),
            "total_chars": sum(len(doc['text']) for doc in self.documents),
            "sources": list(set(doc.get('source', 'unknown') for doc in self.documents))
        }


def get_simple_document_store() -> SimpleDocumentStore:
    """Get or create document store instance."""
    if 'simple_doc_store' not in st.session_state:
        st.session_state.simple_doc_store = SimpleDocumentStore()
    return st.session_state.simple_doc_store


def is_text_garbled(text: str, threshold: float = 0.3) -> bool:
    """
    Detect if extracted text is garbled/obfuscated.
    
    Args:
        text: Text to check
        threshold: Ratio of repeated chars that indicates garbled text
        
    Returns:
        True if text appears garbled
    """
    if not text or len(text) < 50:
        return False
    
    # Check for excessive character repetition
    sample = text[:500]  # Check first 500 chars
    
    # Count consecutive repeated characters
    repeat_count = 0
    prev_char = None
    repeat_sequences = 0
    
    for char in sample:
        if char == prev_char and char.isalpha():
            repeat_count += 1
            if repeat_count > 5:  # More than 5 consecutive same chars
                repeat_sequences += 1
        else:
            repeat_count = 0
        prev_char = char
    
    # Calculate ratio of garbled content
    ratio = repeat_sequences / max(len(sample), 1)
    
    # Also check for lack of spaces/words
    word_count = len(re.findall(r'\b\w+\b', sample))
    char_count = len(sample.replace(' ', ''))
    
    if char_count > 0:
        avg_word_length = char_count / max(word_count, 1)
        if avg_word_length > 20:  # Words too long = likely garbled
            return True
    
    return ratio > threshold


def process_uploaded_files(uploaded_files, progress_callback=None) -> bool:
    """
    Process uploaded files and add to document store.
    
    Args:
        uploaded_files: List of uploaded file objects
        progress_callback: Optional callback(current, total, message)
        
    Returns:
        True if successful
    """
    try:
        import pdfplumber
        import pypdf
        import io
        import pandas as pd
        from production_parser import extract_production_metrics, get_production_summary
        
        logger.info(f"Starting to process {len(uploaded_files)} files")
        
        doc_store = get_simple_document_store()
        doc_store.clear()
        
        all_docs = []
        
        for file_idx, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.name
            logger.info(f"Processing file {file_idx + 1}/{len(uploaded_files)}: {filename}")
            
            if filename.endswith('.pdf'):
                # Extract text from PDF using pypdf (primary method - faster and works better)
                pdf_bytes = uploaded_file.read()
                logger.info(f"Read {len(pdf_bytes)} bytes from {filename}")
                pdf_file = io.BytesIO(pdf_bytes)
                
                # Use pypdf as primary extraction method
                pdf_reader = pypdf.PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {total_pages} pages - using pypdf extraction")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    # Update progress
                    if progress_callback:
                        progress_callback(
                            page_num + 1, 
                            total_pages, 
                            f"Extracting page {page_num + 1}/{total_pages} from {filename}"
                        )
                    
                    if page_num % 5 == 0:  # Log every 5 pages
                        logger.info(f"Processing page {page_num + 1}/{total_pages}")
                    
                    text = page.extract_text()
                    
                    if text and text.strip():
                        # Split into chunks
                        chunks = split_text_into_chunks(text, chunk_size=1000, overlap=200)
                        for i, chunk in enumerate(chunks):
                            all_docs.append({
                                'text': chunk,
                                'source': filename,
                                'page': page_num + 1,
                                'chunk': i + 1
                            })
                
                logger.info(f"pypdf extracted {len(all_docs)} chunks from {filename}")
                
                # Try to extract structured production data
                pdf_file.seek(0)
                full_text = ""
                pdf_reader = pypdf.PdfReader(pdf_file)
                for page in pdf_reader.pages[:3]:  # Check first 3 pages for structure
                    full_text += page.extract_text() + "\n"
                
                # Parse production metrics
                prod_df = extract_production_metrics(full_text)
                if prod_df is not None and not prod_df.empty:
                    logger.info(f"Extracted structured data: {prod_df.shape}")
                    
                    # Store as special formatted chunk
                    table_text = "PRODUCTION DATA TABLE:\n\n" + prod_df.to_string(index=False)
                    all_docs.insert(0, {  # Insert at beginning for higher priority
                        'text': table_text,
                        'source': filename,
                        'page': 0,
                        'chunk': 0,
                        'type': 'structured_data'
                    })
                    
                    # Also store comprehensive summary
                    summary = get_production_summary(full_text)
                    
                    # Format products and tanks nicely
                    products_str = ', '.join(sorted(list(summary.get('products', set())))[:5])
                    tanks_list = sorted(list(summary.get('tanks', set())))[:10]
                    tanks_str = '\n'.join([f"  - {tank}" for tank in tanks_list])
                    
                    # Format volume breakdown
                    volume_breakdown = ""
                    if 'liq_volume_bbl' in summary:
                        volume_breakdown = f"""
Volume Breakdown:
  Liquid Volume (LIQ_VOL): {summary.get('liq_volume_bbl', 0):.2f} bbl
  Oil Volume (OIL_VOL): {summary.get('oil_volume_bbl', 0):.2f} bbl
  Water Volume (WATER_VOL): {summary.get('water_volume_bbl', 0):.2f} bbl
"""
                    else:
                        volume_breakdown = f"\nTotal Volume: {summary.get('total_volume_bbl', 0):.2f} bbl"
                    
                    summary_text = f"""PRODUCTION DATA SUMMARY

Total Deliveries/Tickets: {summary.get('total_tickets', 0)}
{volume_breakdown}
Total Measurements: {summary.get('volume_count', 0)}
Average Temperature: {summary.get('avg_temp', 0):.1f} degF
Average Pressure: {summary.get('avg_pressure', 0):.1f} psi

Products: {products_str}

Storage Tanks:
{tanks_str}

This data represents condensate and oil deliveries from various storage tanks.
All volumes are measured in barrels (bbl).
"""
                    all_docs.insert(0, {
                        'text': summary_text,
                        'source': filename,
                        'page': 0,
                        'chunk': -1,
                        'type': 'summary'
                    })
                
            elif filename.endswith('.txt'):
                # Process text file
                logger.info(f"Processing text file: {filename}")
                text = uploaded_file.read().decode('utf-8')
                chunks = split_text_into_chunks(text, chunk_size=1000, overlap=200)
                
                for i, chunk in enumerate(chunks):
                    all_docs.append({
                        'text': chunk,
                        'source': filename,
                        'page': 1,
                        'chunk': i + 1
                    })
                
                logger.info(f"Extracted {len(chunks)} chunks from {filename}")
        
        # Add all documents to store
        logger.info(f"Adding {len(all_docs)} total chunks to document store")
        doc_store.add_documents(all_docs)
        
        logger.info("Processing complete!")
        st.success(f"✓ Processed {len(uploaded_files)} files ({len(all_docs)} chunks)")
        return True
        
    except Exception as e:
        st.error(f"Failed to process files: {str(e)}")
        logger.error(f"File processing error: {str(e)}")
        return False


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to end at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if reasonably far in
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks
