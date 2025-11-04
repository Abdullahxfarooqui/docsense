"""
Hybrid Query Engine - DocSense with Dual-Model Architecture

Architecture:
- Mistral (OpenRouter): Document retrieval and context analysis
- GROQ (Llama 3.3): Natural language answer generation

This module implements a two-stage pipeline:
1. Mistral analyzes the query and retrieves relevant document chunks
2. GROQ generates natural, well-formatted answers from the context

Author: AI Assistant
Created: November 2025
"""

import logging
import os
from typing import List, Tuple, Dict, Any, Optional, Generator
import time

from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
from vector_store import get_vector_store

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
TOP_K_RESULTS = 5
MAX_RETRIES = 3


class HybridQueryEngineError(Exception):
    """Custom exception for hybrid query engine errors."""
    pass


class HybridQueryEngine:
    """
    Dual-model query engine using Mistral for retrieval and GROQ for answering.
    
    Pipeline:
    1. User query → Mistral (analyzes intent, retrieves context)
    2. Query + Context → GROQ (generates natural answer)
    """
    
    def __init__(self):
        """Initialize both Mistral (OpenRouter) and GROQ clients."""
        try:
            # Validate environment
            self._validate_environment()
            
            # Initialize Mistral client (OpenRouter) for retrieval
            self.mistral_client = OpenAI(
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            # Initialize GROQ client for answer generation
            self.groq_client = OpenAI(
                base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
                api_key=os.getenv("GROQ_API_KEY")
            )
            
            logger.info("✓ Hybrid Query Engine initialized (Mistral + GROQ)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hybrid Query Engine: {str(e)}")
            raise HybridQueryEngineError(f"Initialization failed: {str(e)}")
    
    def _validate_environment(self):
        """Validate required environment variables."""
        required_vars = ["GROQ_API_KEY", "OPENROUTER_API_KEY"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise HybridQueryEngineError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing database IDs and other noise.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        import re
        # Remove long hex strings (database IDs like 282f84480b804f7db96ddbe04f91870e)
        text = re.sub(r'\b[a-f0-9]{24,}\b', '[ID]', text, flags=re.IGNORECASE)
        # Remove shorter hex patterns that look like UUIDs
        text = re.sub(r'\b[a-f0-9]{8,16}\b', '[ID]', text, flags=re.IGNORECASE)
        return text
    
    def retrieve_context_with_mistral(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> str:
        """
        Use Mistral to analyze query and select relevant document chunks.
        
        Args:
            query: User's question
            documents: List of document chunks from vector DB
            
        Returns:
            Formatted context string with relevant chunks
        """
        try:
            # Format documents for Mistral (with cleaning)
            doc_text = "\n\n".join([
                f"[Chunk {i+1}]\n{self._clean_text(doc['text'])}\nSource: {doc['source']}"
                for i, doc in enumerate(documents[:TOP_K_RESULTS])
            ])
            
            # Use Mistral to analyze and filter relevant context
            system_prompt = """You are a document retrieval agent. Your job is to:
1. Analyze the user's query
2. Extract the most relevant information from the provided document chunks
3. Return ONLY the relevant excerpts with their source citations
4. Keep the context concise but complete

Format: Return relevant text with [Source: filename] citations."""

            response = self.mistral_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nDocuments:\n{doc_text}\n\nExtract relevant context:"}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            context = response.choices[0].message.content
            logger.info(f"✓ Mistral retrieved context ({len(context)} chars)")
            return context
            
        except Exception as e:
            logger.error(f"Mistral retrieval failed: {str(e)}")
            # Fallback: return original documents
            return doc_text
    
    def answer_with_groq(
        self,
        query: str,
        context: str,
        detail_level: str = "detailed"
    ) -> Generator[str, None, None]:
        """
        Use GROQ to generate a natural answer based on retrieved context.
        
        Args:
            query: User's question
            context: Retrieved document context from Mistral
            detail_level: "brief" or "detailed"
            
        Yields:
            Streamed answer chunks
        """
        try:
            # Adjust prompt based on detail level
            if detail_level == "brief":
                system_prompt = """You are DocSense, an AI research assistant. Answer questions concisely using ONLY the provided context.

CRITICAL RULES - NO EXCEPTIONS:
- NEVER make up data or facts not in the context
- If the context lacks relevant information, state: "The provided document does not contain information about [topic]"
- DO NOT generate fake data or hypothetical examples
- ONLY use actual data from the context

Rules:
- Use 2-3 paragraphs maximum
- Include [Source: filename] citations
- If context is insufficient, say so clearly
- Be direct and factual
- When data is numerical/tabular, present it in table format with | delimiters"""
                max_tokens = 800
            else:
                system_prompt = """You are DocSense, an AI research assistant specialized in production and numerical data. Provide comprehensive, well-structured answers using ONLY the provided context.

CRITICAL RULES - NO EXCEPTIONS:
- NEVER make up data, numbers, or facts not in the context
- If the context does not contain relevant information, explicitly state: "The provided document does not contain information about [topic]"
- DO NOT generate plausible-sounding fake data or examples
- DO NOT use placeholder numbers or hypothetical scenarios
- ONLY use actual data from the context provided

Data Presentation Rules:
- ALWAYS present numerical/production data in table format using | (pipe) delimiters
- Example table format:
Metric | Value | Unit
Production | 1000 | units
Efficiency | 95 | %

- For time-series data, include dates/timestamps in first column
- Include summary statistics when relevant (totals, averages, trends)
- Use clear section headings
- Cite sources as [Source: filename]
- If context is insufficient, explain what specific information is missing
- Be thorough but organized"""
                max_tokens = 2000
            
            # Generate answer with GROQ
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"}
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True
            )
            
            # Stream response
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
            logger.info("✓ GROQ completed answer generation")
            
        except Exception as e:
            logger.error(f"GROQ generation failed: {str(e)}")
            yield f"\n\n⚠️ Error generating answer: {str(e)}"
    
    def query(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        detail_level: str = "detailed"
    ) -> Generator[str, None, None]:
        """
        Main query pipeline: Mistral retrieves → GROQ answers.
        
        Args:
            question: User's question
            documents: Document chunks from vector DB
            detail_level: "brief" or "detailed"
            
        Yields:
            Streamed answer chunks
        """
        try:
            # Stage 1: Retrieve context with Mistral
            with st.spinner("🔍 Analyzing documents with Mistral..."):
                context = self.retrieve_context_with_mistral(question, documents)
            
            # Stage 2: Generate answer with GROQ
            with st.spinner("💬 Generating answer with GROQ..."):
                yield from self.answer_with_groq(question, context, detail_level)
                
        except Exception as e:
            logger.error(f"Query pipeline failed: {str(e)}")
            yield f"\n\n❌ Query failed: {str(e)}"


def get_hybrid_query_engine() -> HybridQueryEngine:
    """
    Factory function to get or create HybridQueryEngine instance.
    
    Returns:
        Initialized HybridQueryEngine
    """
    try:
        if 'hybrid_query_engine' not in st.session_state:
            st.session_state.hybrid_query_engine = HybridQueryEngine()
        return st.session_state.hybrid_query_engine
    except Exception as e:
        raise HybridQueryEngineError(f"Failed to create query engine: {str(e)}")
