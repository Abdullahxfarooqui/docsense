"""
Enhanced Document Engine with Vector Embeddings

Processes PDFs → Chunks → Embeddings → Vector Store
Includes structured data extraction for production metrics.
"""

import logging
import io
from typing import List, Dict, Any, Optional, Callable
import pypdf
import pandas as pd
import streamlit as st

from vector_store import get_vector_store
from production_parser import extract_production_metrics, get_production_summary
from tank_analyzer import extract_tank_deliveries, format_tank_data_for_llm

logger = logging.getLogger(__name__)


def process_documents_with_embeddings(
    uploaded_files: List,
    progress_callback: Optional[Callable] = None
) -> bool:
    """
    Process uploaded files: extract → chunk → embed → store.
    
    Args:
        uploaded_files: List of uploaded file objects
        progress_callback: Optional progress callback(current, total, message)
        
    Returns:
        True if successful
    """
    try:
        vector_store = get_vector_store()
        vector_store.clear()
        
        logger.info(f"Starting enhanced processing of {len(uploaded_files)} files")
        
        all_docs = []
        
        for file_idx, uploaded_file in enumerate(uploaded_files):
            filename = uploaded_file.name
            logger.info(f"Processing file {file_idx + 1}/{len(uploaded_files)}: {filename}")
            
            if filename.endswith('.pdf'):
                # Extract text from PDF using pypdf
                pdf_bytes = uploaded_file.read()
                logger.info(f"Read {len(pdf_bytes)} bytes from {filename}")
                pdf_file = io.BytesIO(pdf_bytes)
                
                # Use pypdf for extraction
                pdf_reader = pypdf.PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {total_pages} pages - extracting with pypdf")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    # Update progress
                    if progress_callback:
                        progress_callback(
                            page_num + 1,
                            total_pages,
                            f"Extracting page {page_num + 1}/{total_pages} from {filename}"
                        )
                    
                    if page_num % 5 == 0:
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
                                'chunk': i + 1,
                                'type': 'text'
                            })
                
                logger.info(f"Extracted {len(all_docs)} chunks from {filename}")
                
                # Extract structured production data
                if progress_callback:
                    progress_callback(
                        total_pages,
                        total_pages,
                        "Extracting structured data..."
                    )
                
                pdf_file.seek(0)
                full_text = ""
                pdf_reader = pypdf.PdfReader(pdf_file)
                for page in pdf_reader.pages:  # Process ALL pages for tank extraction
                    full_text += page.extract_text() + "\n"
                
                # Parse production metrics
                prod_df = extract_production_metrics(full_text)
                if prod_df is not None and not prod_df.empty:
                    logger.info(f"Extracted structured data: {prod_df.shape}")
                    
                    # Store as special formatted chunk
                    table_text = "PRODUCTION DATA TABLE:\n\n" + prod_df.to_string(index=False)
                    all_docs.insert(0, {
                        'text': table_text,
                        'source': filename,
                        'page': 0,
                        'chunk': 0,
                        'type': 'structured_data'
                    })
                
                # Extract tank-specific deliveries
                tank_df = extract_tank_deliveries(full_text)
                if tank_df is not None and not tank_df.empty:
                    logger.info(f"Extracted {len(tank_df)} tank deliveries from {tank_df['Tank'].nunique()} tanks")
                    
                    # Create master summary with ALL tanks (for "show all tanks" queries)
                    summary_lines = ["COMPLETE TANK SUMMARY - ALL TANKS\n" + "="*80]
                    for tank in sorted(tank_df['Tank'].unique()):
                        tank_data = tank_df[tank_df['Tank'] == tank]
                        total_vol = tank_data['Liquid_Volume_bbl'].dropna().sum()
                        summary_lines.append(f"\nTank: {tank}")
                        summary_lines.append(f"  Deliveries: {len(tank_data)}")
                        summary_lines.append(f"  Total Volume: {total_vol:.2f} bbl")
                        if len(tank_data) > 0:
                            summary_lines.append(f"  Average Volume: {total_vol/len(tank_data):.2f} bbl/delivery")
                    
                    master_summary = "\n".join(summary_lines)
                    all_docs.insert(0, {
                        'text': master_summary,
                        'source': filename,
                        'page': 0,
                        'chunk': 0,
                        'type': 'tank_summary'
                    })
                    
                    # Format as searchable text chunks
                    tank_text = format_tank_data_for_llm(tank_df)
                    all_docs.insert(0, {
                        'text': tank_text,
                        'source': filename,
                        'page': 0,
                        'chunk': 0,
                        'type': 'tank_data'
                    })
                    
                    # Also add individual tank summaries for better search
                    for tank in tank_df['Tank'].unique():
                        tank_specific = format_tank_data_for_llm(tank_df, tank)
                        all_docs.insert(0, {
                            'text': tank_specific,
                            'source': filename,
                            'page': 0,
                            'chunk': 0,
                            'type': 'tank_data'
                        })
                
                # Create comprehensive summary
                summary = get_production_summary(full_text)
                
                products_str = ', '.join(sorted(list(summary.get('products', set())))[:5])
                tanks_list = sorted(list(summary.get('tanks', set())))[:10]
                tanks_str = '\n'.join([f"  - {tank}" for tank in tanks_list])
                
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
                        'chunk': i + 1,
                        'type': 'text'
                    })
                
                logger.info(f"Extracted {len(chunks)} chunks from {filename}")
        
        # Add all documents to vector store with embeddings
        if progress_callback:
            progress_callback(1, 1, "Creating vector embeddings...")
        
        logger.info(f"Adding {len(all_docs)} total documents to vector store")
        vector_store.add_documents(all_docs)
        
        logger.info("✓ Processing complete with vector embeddings!")
        st.success(f"✓ Processed {len(uploaded_files)} files ({len(all_docs)} chunks with embeddings)")
        return True
        
    except Exception as e:
        st.error(f"Failed to process files: {str(e)}")
        logger.error(f"File processing error: {str(e)}", exc_info=True)
        return False


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[str]:
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
            
            if break_point > chunk_size * 0.5:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks
