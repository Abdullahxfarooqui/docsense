"""
Robust ChromaDB Management Module

Handles ChromaDB client initialization, error recovery, and automatic index rebuilding.
Eliminates "ef/M too small" and "database error" issues through intelligent fallback strategies.

Author: GitHub Copilot
Date: October 24, 2025
"""

import logging
import os
import shutil
import time
from typing import Optional, List, Dict, Any, Callable
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import streamlit as st

logger = logging.getLogger(__name__)

# Constants
CHROMADB_PERSIST_DIR = ".chromadb"
COLLECTION_NAME = "document_chunks"
MAX_QUERY_RETRIES = 3
LARGE_FILE_THRESHOLD = 10_000_000  # 10MB


class ChromaDBManager:
    """
    Fault-tolerant ChromaDB manager with automatic error recovery.
    """
    
    def __init__(self, persist_dir: str = CHROMADB_PERSIST_DIR, collection_name: str = COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[Collection] = None
        self._rebuild_callback: Optional[Callable] = None
        
    def set_rebuild_callback(self, callback: Callable):
        """Set callback function to rebuild documents after reset."""
        self._rebuild_callback = callback
        
    def get_client(self, force_rebuild: bool = False) -> chromadb.Client:
        """
        Get or create ChromaDB client with fault-tolerant initialization.
        
        Args:
            force_rebuild: Force rebuild the client
            
        Returns:
            chromadb.Client: Configured client instance
        """
        if self._client and not force_rebuild:
            return self._client
            
        try:
            # Try standard initialization
            self._client = self._init_client()
            
            # Sanity check - try to list collections
            _ = self._client.list_collections()
            logger.info("✓ ChromaDB client initialized successfully")
            return self._client
            
        except Exception as e:
            logger.error(f"⚠️ ChromaDB initialization failed: {type(e).__name__}: {str(e)}")
            logger.warning("Attempting to rebuild vector store...")
            
            # Remove corrupted database
            if os.path.exists(self.persist_dir):
                try:
                    shutil.rmtree(self.persist_dir)
                    logger.info(f"Removed corrupted database at {self.persist_dir}")
                except Exception as rm_error:
                    logger.error(f"Failed to remove corrupted database: {rm_error}")
            
            # Reinitialize with fresh database
            self._client = self._init_client()
            logger.info("✓ ChromaDB client rebuilt successfully")
            return self._client
    
    def _init_client(self) -> chromadb.Client:
        """
        Initialize ChromaDB client with optimal settings.
        
        Returns:
            chromadb.Client: Configured client
        """
        # Use the new PersistentClient API (not deprecated Settings)
        client = chromadb.PersistentClient(
            path=self.persist_dir
        )
        
        return client
    
    def get_collection(self, force_rebuild: bool = False) -> Collection:
        """
        Get or create collection with fault tolerance.
        
        Args:
            force_rebuild: Force rebuild the collection
            
        Returns:
            Collection: ChromaDB collection
        """
        if self._collection and not force_rebuild:
            return self._collection
        
        try:
            client = self.get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # More stable for embeddings
            )
            logger.info(f"✓ Collection '{self.collection_name}' initialized")
            return self._collection
            
        except Exception as e:
            logger.error(f"Failed to get collection: {str(e)}")
            # Try with fresh client
            self._collection = self.get_client(force_rebuild=True).get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return self._collection
    
    def verify_index_integrity(self) -> bool:
        """
        Verify that the ChromaDB index is healthy and usable.
        
        Returns:
            bool: True if index is healthy, False otherwise
        """
        try:
            collection = self.get_collection()
            count = collection.count()
            
            if count == 0:
                logger.warning("Collection is empty - may need to reprocess documents")
                return True  # Empty is valid, just needs documents
            
            # Try a simple query to verify HNSW index works
            try:
                collection.query(
                    query_texts=["test query"],
                    n_results=min(1, count)
                )
                logger.info(f"✓ Index integrity verified ({count} documents)")
                return True
            except Exception as query_error:
                logger.error(f"Index query test failed: {str(query_error)}")
                return False
                
        except Exception as e:
            logger.error(f"Index integrity check failed: {str(e)}")
            return False
    
    def safe_query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query with automatic error recovery and fallback strategies.
        
        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Metadata filter
            retry_count: Current retry attempt
            
        Returns:
            Query results or None if all attempts fail
        """
        if retry_count >= MAX_QUERY_RETRIES:
            logger.error("Max query retries reached")
            return None
        
        try:
            collection = self.get_collection()
            count = collection.count()
            
            if count == 0:
                logger.warning("Collection is empty - no documents to query")
                return None
            
            # Adjust n_results if it exceeds collection size
            safe_n_results = min(n_results, count)
            
            # Execute query
            results = collection.query(
                query_texts=query_texts,
                n_results=safe_n_results,
                where=where
            )
            
            return results
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for HNSW-related errors
            if any(keyword in error_msg for keyword in [
                "contiguous 2d array",
                "ef or m is too small",
                "hnsw",
                "database error"
            ]):
                logger.warning(f"HNSW error detected (attempt {retry_count + 1}): {str(e)}")
                
                # Strategy 1: Try with smaller n_results
                if n_results > 1:
                    logger.info(f"Retry with smaller n_results: {n_results} → {max(1, n_results // 2)}")
                    return self.safe_query(
                        query_texts=query_texts,
                        n_results=max(1, n_results // 2),
                        where=where,
                        retry_count=retry_count + 1
                    )
                
                # Strategy 2: Rebuild index if all else fails
                if retry_count == 0:
                    logger.warning("Rebuilding ChromaDB index...")
                    self.rebuild_index()
                    return self.safe_query(
                        query_texts=query_texts,
                        n_results=n_results,
                        where=where,
                        retry_count=retry_count + 1
                    )
            
            logger.error(f"Query failed: {str(e)}")
            return None
    
    def safe_add(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        retry_count: int = 0
    ) -> bool:
        """
        Add documents with automatic error recovery.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of document IDs
            retry_count: Current retry attempt
            
        Returns:
            bool: True if successful, False otherwise
        """
        if retry_count >= MAX_QUERY_RETRIES:
            logger.error("Max add retries reached")
            return False
        
        try:
            collection = self.get_collection()
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✓ Added {len(documents)} documents to collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents (attempt {retry_count + 1}): {str(e)}")
            
            if retry_count == 0:
                logger.warning("Rebuilding index and retrying...")
                self.rebuild_index()
                return self.safe_add(documents, metadatas, ids, retry_count + 1)
            
            return False
    
    def rebuild_index(self):
        """
        Rebuild the ChromaDB index from scratch.
        """
        try:
            logger.warning("🔄 Rebuilding ChromaDB index...")
            
            # Reset client
            client = self.get_client()
            client.reset()
            logger.info("✓ ChromaDB reset complete")
            
            # Clear cached objects
            self._client = None
            self._collection = None
            
            # Reinitialize
            self.get_collection(force_rebuild=True)
            
            # Trigger document reprocessing if callback is set
            if self._rebuild_callback:
                logger.info("Triggering document reprocessing...")
                self._rebuild_callback()
            else:
                logger.warning("No rebuild callback set - please re-upload documents")
            
        except Exception as e:
            logger.error(f"Index rebuild failed: {str(e)}")
            raise
    
    def reset(self):
        """
        Complete reset of ChromaDB - removes all data.
        """
        try:
            if self._client:
                self._client.reset()
            self._client = None
            self._collection = None
            
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)
            
            logger.info("✓ ChromaDB completely reset")
            
        except Exception as e:
            logger.error(f"Reset failed: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics for debugging.
        
        Returns:
            Dict with collection stats
        """
        try:
            collection = self.get_collection()
            count = collection.count()
            
            # Try to get a sample
            sample = None
            if count > 0:
                try:
                    sample = collection.peek(limit=1)
                except:
                    pass
            
            return {
                "count": count,
                "healthy": self.verify_index_integrity(),
                "has_sample": sample is not None,
                "collection_name": self.collection_name
            }
        except Exception as e:
            return {
                "error": str(e),
                "healthy": False
            }


# Global singleton instance
@st.cache_resource
def get_chromadb_manager() -> ChromaDBManager:
    """
    Get or create the global ChromaDB manager instance.
    
    Returns:
        ChromaDBManager: Singleton instance
    """
    return ChromaDBManager()


def is_large_file(file_path: str) -> bool:
    """
    Check if file exceeds size threshold for special handling.
    
    Args:
        file_path: Path to file
        
    Returns:
        bool: True if file is large
    """
    try:
        return os.path.getsize(file_path) > LARGE_FILE_THRESHOLD
    except:
        return False
