"""
Vector Store with TF-IDF - Enhanced Semantic Search

Uses TF-IDF embeddings (sklearn) instead of sentence-transformers to avoid PyTorch issues.
Combines semantic search with keyword boosting for optimal retrieval.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

logger = logging.getLogger(__name__)


class VectorDocumentStore:
    """
    TF-IDF based vector store with hybrid retrieval (semantic + keyword).
    Uses sklearn instead of PyTorch for compatibility.
    """
    
    def __init__(self):
        """Initialize vector store with TF-IDF vectorizer."""
        self.vectorizer = None
        self.document_vectors = None
        self.documents = []
        
    def _initialize_vectorizer(self):
        """Initialize TF-IDF vectorizer."""
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.9,
                sublinear_tf=True
            )
            logger.info("✓ TF-IDF vectorizer initialized")
    
    def add_documents(self, docs: List[Dict[str, Any]]):
        """
        Add documents and create TF-IDF vectors.
        
        Args:
            docs: List of dicts with 'text', 'source', 'page' keys
        """
        if not docs:
            return
        
        self._initialize_vectorizer()
        
        # Store documents
        self.documents.extend(docs)
        
        # Extract all texts
        all_texts = [doc['text'] for doc in self.documents]
        
        logger.info(f"Creating TF-IDF vectors for {len(self.documents)} documents...")
        
        # Create TF-IDF vectors for all documents
        self.document_vectors = self.vectorizer.fit_transform(all_texts)
        
        logger.info(f"✓ Added {len(docs)} documents to vector store (total: {len(self.documents)})")
    
    def clear(self):
        """Clear all documents and vectors."""
        self.documents = []
        self.document_vectors = None
        self.vectorizer = None
        logger.info("Vector store cleared")
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        keyword_boost: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: TF-IDF similarity + keyword matching.
        
        Args:
            query: Search query
            top_k: Number of results
            keyword_boost: Weight for keyword matching (0-1)
            
        Returns:
            List of relevant documents with scores
        """
        if not self.documents or self.document_vectors is None:
            return []
        
        # Transform query using fitted vectorizer
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top candidates (more than needed for re-ranking)
        # Use much larger pool for entity-specific queries (like "HALINI tank")
        # This ensures we don't miss chunks from later pages
        search_k = min(top_k * 20, len(self.documents))  # Increased to 20x for better coverage
        top_indices = np.argsort(similarities)[::-1][:search_k]
        
        # Collect results with scores
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Extract potential entity names - look for proper nouns and specific terms
        # Check for uppercase words OR capitalized words that might be tank names
        query_tokens = query.split()
        entity_names = []
        
        # Add uppercase words
        entity_names.extend([w for w in query_tokens if w.isupper() and len(w) > 2])
        
        # Add capitalized words (potential tank names like "Halini", "Bolan")
        entity_names.extend([w.upper() for w in query_tokens if w[0].isupper() and len(w) > 3 and not w.lower() in ['show', 'tell', 'what', 'which', 'tank', 'deliveries']])
        
        # Remove duplicates
        entity_names = list(set(entity_names))
        
        for idx in top_indices:
            doc = self.documents[idx]
            
            # TF-IDF similarity score
            tfidf_score = similarities[idx]
            
            # Keyword score
            text_lower = doc['text'].lower()
            keyword_matches = sum(1 for word in query_words if word in text_lower)
            keyword_score = keyword_matches / max(len(query_words), 1)
            
            # Entity boost: if query has specific names (like "HALINI"), strongly boost exact matches
            entity_boost = 0.0
            text_upper = doc['text'].upper()
            for entity in entity_names:
                if entity in text_upper:
                    entity_boost = 3.0  # Very strong boost for exact entity matches
                    logger.debug(f"Entity '{entity}' found in doc, boosting score")
                    break
            
            # Combined score
            final_score = ((1 - keyword_boost) * tfidf_score + keyword_boost * keyword_score) * (1 + entity_boost)
            
            # Boost priority documents
            doc_type = doc.get('type', 'text')
            if doc_type == 'summary':
                final_score *= 1.5
            elif doc_type == 'structured_data':
                final_score *= 1.3
            elif doc_type == 'tank_summary':
                final_score *= 2.0  # Strong boost for complete tank summaries
            elif doc_type == 'tank_data':
                final_score *= 1.4
            
            results.append({
                'document': doc,
                'score': final_score,
                'tfidf_score': tfidf_score,
                'keyword_score': keyword_score
            })
        
        # Sort by final score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top_k documents
        final_docs = [r['document'] for r in results[:top_k]]
        
        logger.info(f"Found {len(final_docs)} documents (TF-IDF + keyword hybrid)")
        return final_docs
    
    def save(self, filepath: str):
        """
        Save vector store to disk.
        
        Args:
            filepath: Path to save file
        """
        if self.document_vectors is None:
            logger.warning("No vectors to save")
            return
        
        # Save vectorizer, vectors, and documents
        with open(f"{filepath}.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'vectorizer': self.vectorizer,
                'document_vectors': self.document_vectors
            }, f)
        
        logger.info(f"✓ Vector store saved to {filepath}")
    
    def load(self, filepath: str):
        """
        Load vector store from disk.
        
        Args:
            filepath: Path to saved file
        """
        try:
            # Load vectorizer, vectors, and documents
            with open(f"{filepath}.pkl", 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.vectorizer = data['vectorizer']
                self.document_vectors = data['document_vectors']
            
            logger.info(f"✓ Vector store loaded from {filepath} ({len(self.documents)} docs)")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "total_documents": len(self.documents),
            "vector_count": self.document_vectors.shape[0] if self.document_vectors is not None else 0,
            "dimension": self.document_vectors.shape[1] if self.document_vectors is not None else 0,
            "vectorizer": "TF-IDF (sklearn)",
            "sources": list(set(doc.get('source', 'unknown') for doc in self.documents))
        }


def get_vector_store() -> VectorDocumentStore:
    """Get or create vector store instance (singleton pattern)."""
    import streamlit as st
    
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = VectorDocumentStore()
    
    return st.session_state.vector_store
