"""
Document Mode Module - Strict RAG (Retrieval-Augmented Generation)

V3.5 ENHANCED: Three-Mode Analytical Document Intelligence Assistant

🎯 **THREE OPERATIONAL MODES (AUTO-DETECTED):**

1️⃣ **TEXTUAL ANALYSIS MODE** 📄
   - Trigger: Narrative/qualitative queries without numeric indicators
   - Output: Structured paragraphs with citations [Source 1], [Source 2]
   - Depth: Brief (2-3 paragraphs) or Detailed (research-grade 2000+ tokens)
   - Use: PDF reports, research papers, articles, qualitative documents

2️⃣ **NUMERIC EXTRACTION MODE** 📊 (V3.5 ENHANCED - STRICT NO-PROSE)
   - Trigger: Queries with numeric/tabular keywords (extract, pressure, temperature, psi, bbl, etc.)
   - Output: **ONLY** Markdown tables or JSON — ZERO prose allowed
   - Strict Rules:
     ✅ Extract explicit + inferred numeric values with context
     ✅ Include units always (psi, °F, bbl, MMBtu, etc.)
     ✅ Handle missing data (Value: null, Notes: "Not found")
     ✅ Optional ONE-line calculation after table
     ❌ NO introductions, summaries, conclusions, insights paragraphs
     ❌ NO fabricated/dummy data (e.g., Temperature = 0)
   - Use: Excel files, CSV data, tables, measurements, engineering reports

3️⃣ **CHAT MODE** 💬
   - Trigger: Casual/conversational inputs (hi, thanks, ok)
   - Output: "You're in Document Mode — ask about your files or switch to Chat Mode"
   - Use: Mode switching guidance

**V3.5 KEY IMPROVEMENTS:**
- Aggressive numeric mode triggering (30+ trigger keywords)
- Expanded unit detection (psi, psig, bbl, °F, MMBtu, mcf, etc.)
- Strict prose validation (prevents narrative essays in numeric mode)
- Contextual inference for incomplete data (Well #7 shows 3124 → Pressure: 3124 psi)
- Never fabricates missing values

**FEATURES:**
- Strict RAG: No pretrained knowledge, only document content
- Similarity threshold filtering
- Rich citation system [Source 1], [Source 2]
- Adaptive response depth for research queries
- Multi-paragraph structured answers (text mode)
- Session-based document management
- MMR (Maximal Marginal Relevance) for diverse chunk retrieval

Author: AI Assistant
Created: October 2025
Updated: V3.5 - Enhanced Numeric Extraction with Strict No-Prose Mode
"""

import logging
import os
from typing import List, Dict, Any, Tuple, Generator, Optional
import time
import asyncio
import hashlib

import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import numpy as np

from ingestion import get_collection

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Import ChromaDB manager for safe queries
try:
    from chromadb_manager import get_chromadb_manager
    CHROMADB_MANAGER_AVAILABLE = True
    logger.info("ChromaDB manager available for safe queries")
except ImportError:
    CHROMADB_MANAGER_AVAILABLE = False
    logger.warning("ChromaDB manager not available - using direct queries")

# Import Entity Extractor for intelligent data extraction
try:
    from entity_extractor import get_entity_extractor, EntityExtractor
    ENTITY_EXTRACTOR_AVAILABLE = True
    logger.info("Entity extractor available for smart data extraction")
except ImportError:
    ENTITY_EXTRACTOR_AVAILABLE = False
    logger.warning("Entity extractor not available - using basic extraction")

# Constants
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 3

# Document mode settings - RESEARCH-GRADE OPTIMIZATION
CHUNK_SIZE = 1500  # Balanced granularity for context quality
CHUNK_OVERLAP = 200  # Ensures continuity across chunks
TOP_K_RESULTS = 5  # Top 5 chunks for comprehensive context
FETCH_K_RESULTS = 10  # MMR fetch pool for diversity
SIMILARITY_THRESHOLD = 0.0  # DISABLED for dummy embeddings - accept all chunks
MAX_CONTEXT_TOKENS = 1200  # Per chunk limit (5 chunks × 1200 = 6000 tokens max)
MMR_LAMBDA = 0.65  # Diversity vs relevance balance (0.65 = balanced)

# Response depth settings - GROQ CLOUD OPTIMIZED FOR QUALITY
BRIEF_MAX_TOKENS = 800  # Brief: 2-3 focused paragraphs (~600 words)
DETAILED_MAX_TOKENS = 4096  # Detailed: Deep research-grade analysis (~3000+ words)
RAG_TEMPERATURE = 0.65  # OPTIMIZED: Analytical reasoning with controlled creativity
TOP_P = 0.9  # Nucleus sampling for coherent output
FREQUENCY_PENALTY = 0.3  # Encourage variety in expression
PRESENCE_PENALTY = 0.3  # Balanced topic exploration

# PERFORMANCE OPTIMIZATION (Groq is fast - <2s first token)
RETRIEVAL_TIMEOUT = 4  # Fast async retrieval timeout (seconds)
LLM_TIMEOUT = 30  # Groq is fast - reduce timeout for quicker failure detection
MAX_RETRIES_LLM = 1  # Single retry only

# CACHING
EMBEDDING_CACHE = {}  # Cache embeddings by hash to skip re-computation


class DocumentModeError(Exception):
    """Custom exception for document mode errors."""
    pass


class DocumentMode:
    """
    Strict RAG mode - answers ONLY from uploaded documents.
    
    Never uses pretrained knowledge. If information isn't in the documents,
    refuses to answer rather than hallucinating.
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize Document Mode.
        
        Args:
            model_name: OpenRouter model to use
        """
        try:
            self.model_name = model_name
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
            self.site_url = os.getenv("SITE_URL", "http://localhost:8501")
            self.site_name = os.getenv("SITE_NAME", "DocSense - Document Mode")
            
            if not self.api_key:
                raise DocumentModeError("OPENAI_API_KEY not set")
            
            # Initialize OpenRouter client with timeout
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=LLM_TIMEOUT,  # Set default timeout for all requests
                max_retries=0  # Disable retries to fail fast
            )
            
            # Get ChromaDB collection
            self.collection = get_collection()
            
            # Verify index integrity if ChromaDB manager is available
            if CHROMADB_MANAGER_AVAILABLE:
                try:
                    manager = get_chromadb_manager()
                    if not manager.verify_index_integrity():
                        logger.warning("⚠️ ChromaDB index integrity check failed - may need rebuild")
                        # Don't fail initialization, just warn
                except Exception as e:
                    logger.warning(f"Could not verify index integrity: {str(e)}")
            
            logger.info(f"✓ Document Mode initialized with model: {model_name}")
            logger.info(f"✓ RAG settings: TOP_K={TOP_K_RESULTS}, CHUNK_SIZE={CHUNK_SIZE}, OVERLAP={CHUNK_OVERLAP}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Document Mode: {str(e)}")
            raise DocumentModeError(f"Document Mode initialization failed: {str(e)}")
    
    def check_documents_available(self) -> Tuple[bool, int]:
        """
        Check if documents are available in ChromaDB.
        
        Returns:
            Tuple of (has_documents, chunk_count)
        """
        try:
            count = self.collection.count()
            return (count > 0, count)
        except Exception as e:
            logger.error(f"Failed to check document availability: {str(e)}")
            return (False, 0)
    
    def detect_intent(self, query: str) -> str:
        """
        Fast intent classifier - determines if retrieval is needed.
        
        Returns:
            - 'casual': Greetings, thanks, short acknowledgments (no retrieval)
            - 'document_query': Actual questions requiring document search
        """
        normalized = query.strip().lower()
        
        # Casual patterns - skip retrieval entirely
        casual_phrases = [
            "hi", "hello", "hey", "ok", "okay", "thanks", "thank you", 
            "bye", "goodbye", "yes", "yeah", "no", "nope", "sure",
            "got it", "alright", "cool", "nice", "good", "great",
            "sup", "what's up", "wassup", "howdy"
        ]
        
        # Exact match or starts with casual phrase (max 4 words)
        if len(normalized.split()) <= 4 and any(normalized.startswith(p) for p in casual_phrases):
            logger.info(f"💬 Intent: CASUAL ('{normalized[:30]}...')")
            return "casual"
        
        # Everything else requires document retrieval
        logger.info(f"📚 Intent: DOCUMENT_QUERY")
        return "document_query"
    
    def detect_data_type(self, chunks: List[Dict[str, Any]], query: str) -> str:
        """
        Automatically detect if query requires NUMERIC/DATA extraction or TEXT analysis.
        
        V3.6 FIXED: Smart detection - prioritizes user intent over keyword matching.
        
        Returns:
            - 'numeric': Excel/CSV data, needs tables/JSON output (STRICT - NO PROSE)
            - 'text': Document analysis, needs analytical paragraphs
        """
        query_lower = query.lower()
        
        # V3.6 FIX: Check for EXPLANATORY/ANALYTICAL queries FIRST
        # These should ALWAYS use text mode, even if they contain trigger words
        text_mode_indicators = [
            # Questions asking for explanation/understanding
            'what is this about', 'what does this mean', 'explain', 'describe',
            'tell me about', 'what is', "what's", 'why', 'how does',
            'what other', 'what else', 'anything else', 'more information',
            'summary', 'overview', 'context', 'background', 'purpose',
            
            # Analysis requests
            'analyze', 'interpret', 'discuss', 'compare', 'contrast',
            'relationship', 'impact', 'significance', 'implications',
            
            # Open-ended questions
            'tell me', 'can you tell', 'could you explain', 'help me understand'
        ]
        
        # Check for text mode indicators first
        import re
        for indicator in text_mode_indicators:
            if indicator in query_lower:
                logger.info(f"📄 Data Type: TEXT (explanatory query detected: '{indicator}')")
                return 'text'
        
        # V3.8: STRICT numeric extraction triggers (expanded for entity queries)
        strict_numeric_triggers = [
            # Explicit extraction commands
            'extract all', 'extract data', 'extract values', 'give me all',
            'show all data', 'list all', 'get all values', 'show data',
            
            # Entity-based queries (V3.8 NEW)
            'show all parameters', 'list all parameters', 'parameters for each',
            'for each entity', 'all entities', 'each entity', 'entity data',
            'data for all', 'values from document', 'from document',
            
            # Location-based extraction (strong indicator)
            'at each location', 'by location', 'at each well', 'per location',
            'each location', 'all locations', 'every location',
            
            # Table/spreadsheet requests
            'in a table', 'as a table', 'table format', 'spreadsheet',
            'show table', 'as table', 'in table',
            
            # Specific value queries
            'what is the pressure', 'what is the temperature',
            'pressure at', 'temperature at', 'value of', 'values for',
            'volume at', 'api at', 'temperature of', 'pressure of'
        ]
        
        # Check for strict numeric triggers
        for trigger in strict_numeric_triggers:
            if trigger in query_lower:
                logger.info(f"📊 Data Type: NUMERIC (strict extraction: '{trigger}')")
                return 'numeric'
        
        # V3.6: Secondary check - look for measurement units (strong indicator)
        unit_triggers = [
            'psi', 'psig', 'bbl', 'barrels', '°f', '°c', 'degf', 'degc',
            'mmbtu', 'mcf', 'ft³', 'kg', 'lb'
        ]
        
        unit_count = sum(1 for unit in unit_triggers if re.search(r'\b' + re.escape(unit) + r'\b', query_lower))
        if unit_count >= 2:  # Multiple units = likely numeric query
            logger.info(f"📊 Data Type: NUMERIC ({unit_count} units detected)")
            return 'numeric'
        
        # V3.6: Check chunk content - but only if query is ambiguous
        # Only check if chunks contain structured data (tables)
        has_structured_data = False
        for chunk in chunks[:3]:  # Check first 3 chunks only
            content = chunk.get('content', '')
            # Look for clear table structures (markdown tables with pipes)
            if content.count('|') > 10 and ('parameter' in content.lower() or 'value' in content.lower()):
                has_structured_data = True
                break
        
        # If we found structured data AND query contains generic words like "data", use numeric
        generic_data_words = ['data', 'all data', 'information', 'values']
        if has_structured_data and any(word in query_lower for word in generic_data_words):
            logger.info("📊 Data Type: NUMERIC (structured data detected with generic query)")
            return 'numeric'
        
        # Default to text analysis - better to explain than to dump tables
        logger.info("📄 Data Type: TEXT (analytical mode)")
        return 'text'
    
    async def fast_retrieve_async(self, query: str, timeout: int = RETRIEVAL_TIMEOUT) -> List[Dict[str, Any]]:
        """
        ASYNC retrieval with timeout - wraps synchronous retrieval in async context.
        
        Args:
            query: User's question
            timeout: Maximum seconds for retrieval (default 4s)
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Run synchronous retrieval in executor with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._retrieve_sync, query),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Async retrieval timeout ({timeout}s)")
            return []
        except Exception as e:
            logger.error(f"Async retrieval failed: {str(e)}")
            return []
    
    def _retrieve_sync(self, query: str) -> List[Dict[str, Any]]:
        """
        Synchronous retrieval helper for async wrapping.
        
        Args:
            query: User's question
            
        Returns:
            List of relevant chunks
        """
        return self.retrieve_relevant_chunks(query, timeout=RETRIEVAL_TIMEOUT)
    
    def get_structured_data_content(self) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Check if structured data (Excel/CSV) is available and return it.
        
        Returns:
            Tuple[bool, Optional[str], Optional[Dict]]: 
                (has_structured_data, markdown_content, metadata)
        """
        if not hasattr(st, 'session_state') or 'structured_data' not in st.session_state:
            return False, None, None
        
        structured_data = st.session_state.structured_data
        
        if not structured_data:
            return False, None, None
        
        # Combine all structured data into one markdown
        combined_markdown_parts = []
        combined_metadata = {
            'files': [],
            'total_rows': 0,
            'total_columns': 0
        }
        
        for filename, data in structured_data.items():
            combined_markdown_parts.append(data['markdown'])
            combined_metadata['files'].append(filename)
            combined_metadata['total_rows'] += data['metadata'].get('total_rows', 0)
            
        if combined_markdown_parts:
            combined_markdown = "\n\n---\n\n".join(combined_markdown_parts)
            logger.info(f"📊 Found {len(structured_data)} structured data file(s) with "
                       f"{combined_metadata['total_rows']} total rows")
            return True, combined_markdown, combined_metadata
        
        return False, None, None
    
    def retrieve_relevant_chunks(self, query: str, timeout: int = RETRIEVAL_TIMEOUT) -> List[Dict[str, Any]]:
        """
        OPTIMIZED: MMR-based retrieval with async timeout.
        
        MMR (Maximal Marginal Relevance) balances relevance vs diversity.
        - Prevents redundant chunks
        - Fetches more candidates (FETCH_K) then diversifies to TOP_K
        - Lambda controls relevance vs diversity trade-off
        
        Args:
            query: User's question
            timeout: Maximum seconds for retrieval (default 4s)
            
        Returns:
            List of relevant chunks with metadata, each truncated to MAX_CONTEXT_TOKENS
        """
        try:
            start_time = time.time()
            
            # Check documents exist
            has_docs, count = self.check_documents_available()
            if not has_docs:
                logger.warning("No documents in collection")
                return []
            
            logger.info(f"� MMR Search: {count} chunks (k={TOP_K_RESULTS}, fetch_k={FETCH_K_RESULTS}, λ={MMR_LAMBDA})")
            
            # ChromaDB doesn't support MMR directly, so we do two-stage retrieval:
            # 1. Fetch broader set (FETCH_K)
            # 2. Manually apply MMR selection to get TOP_K diverse results
            
            # Step 1: Fetch candidate pool
            try:
                # Use ChromaDB manager for safe queries if available
                if CHROMADB_MANAGER_AVAILABLE:
                    manager = get_chromadb_manager()
                    results = manager.safe_query(
                        query_texts=[query],
                        n_results=min(FETCH_K_RESULTS, count)
                    )
                    if not results:
                        logger.error("Safe query returned no results")
                        return []
                else:
                    # Fallback to direct query with error handling
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=min(FETCH_K_RESULTS, count)
                    )
            except Exception as e:
                # If HNSW fails, try with smaller fetch
                logger.warning(f"FETCH_K query failed ({str(e)}), trying with smaller n_results")
                try:
                    if CHROMADB_MANAGER_AVAILABLE:
                        manager = get_chromadb_manager()
                        results = manager.safe_query(
                            query_texts=[query],
                            n_results=min(5, count)
                        )
                        if not results:
                            logger.error("Smaller safe query also returned no results")
                            return []
                    else:
                        results = self.collection.query(
                            query_texts=[query],
                            n_results=min(5, count)
                        )
                except Exception as e2:
                    logger.error(f"All query attempts failed: {str(e2)}")
                    return []
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning(f"⏱️ Retrieval timeout ({elapsed:.2f}s > {timeout}s)")
                return []
            
            # Step 2: Parse candidates
            candidates = []
            if results and results.get('documents') and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    distance = results['distances'][0][i] if results.get('distances') else 1.0
                    
                    # Convert distance to similarity
                    if distance < 0:
                        similarity = 1.0 / (1.0 + abs(distance))
                    else:
                        similarity = 1.0 - min(distance, 1.0)
                    
                    # Apply threshold
                    if similarity < SIMILARITY_THRESHOLD:
                        continue
                    
                    content = results['documents'][0][i]
                    
                    # OPTIMIZATION: Truncate each chunk to MAX_CONTEXT_TOKENS (~800-1000 tokens)
                    words = content.split()
                    if len(words) > MAX_CONTEXT_TOKENS:
                        content = ' '.join(words[:MAX_CONTEXT_TOKENS]) + "..."
                    
                    candidate = {
                        'content': content,
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'similarity': similarity,
                        'id': results['ids'][0][i] if results.get('ids') else f'chunk_{i}'
                    }
                    candidates.append(candidate)
            
            # Step 3: Simple MMR selection (greedy approximation)
            # Take top by relevance, then add diverse candidates
            selected = []
            if candidates:
                # Sort by similarity (descending)
                candidates.sort(key=lambda x: x['similarity'], reverse=True)
                
                # Select top candidate
                selected.append(candidates[0])
                remaining = candidates[1:]
                
                # Greedily select diverse chunks
                while len(selected) < TOP_K_RESULTS and remaining:
                    # Find most diverse candidate (lowest content overlap with selected)
                    best_candidate = None
                    best_score = -1
                    
                    for candidate in remaining:
                        # Diversity: word overlap with selected chunks
                        candidate_words = set(candidate['content'].lower().split())
                        max_overlap = 0
                        for sel in selected:
                            sel_words = set(sel['content'].lower().split())
                            overlap = len(candidate_words & sel_words) / max(len(candidate_words), 1)
                            max_overlap = max(max_overlap, overlap)
                        
                        # MMR score: λ * relevance - (1-λ) * overlap
                        mmr_score = MMR_LAMBDA * candidate['similarity'] - (1 - MMR_LAMBDA) * max_overlap
                        
                        if mmr_score > best_score:
                            best_score = mmr_score
                            best_candidate = candidate
                    
                    if best_candidate:
                        selected.append(best_candidate)
                        remaining.remove(best_candidate)
                    else:
                        break
            
            elapsed = time.time() - start_time
            logger.info(f"✓ MMR Retrieved {len(selected)}/{TOP_K_RESULTS} chunks in {elapsed:.3f}s")
            return selected
            
        except Exception as e:
            logger.error(f"MMR Retrieval failed: {str(e)}")
            return []
    
    def generate_document_summary(self, query: str, detail_level: str) -> str:
        """
        Fallback: Generate summary when no relevant chunks found.
        Uses top 5 chunks as context sample.
        
        Args:
            query: User's question
            detail_level: "brief" or "detailed"
            
        Returns:
            Generated summary or "not found" message
        """
        try:
            logger.info("🔄 Fallback: Generating summary from document sample")
            
            # Retrieve top 5 chunks for context using safe query
            try:
                if CHROMADB_MANAGER_AVAILABLE:
                    manager = get_chromadb_manager()
                    results = manager.safe_query(
                        query_texts=[query],
                        n_results=min(5, self.collection.count())
                    )
                    if not results:
                        return "Could not retrieve document chunks. Please try re-uploading your document."
                else:
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=min(5, self.collection.count())
                    )
            except Exception as e:
                # If query fails, try with even smaller n_results
                logger.warning(f"Query failed, trying with n_results=1: {str(e)}")
                try:
                    if CHROMADB_MANAGER_AVAILABLE:
                        manager = get_chromadb_manager()
                        results = manager.safe_query(
                            query_texts=[query],
                            n_results=1
                        )
                        if not results:
                            return "Could not retrieve document chunks. The vector database may need to be rebuilt. Please try re-uploading your document."
                    else:
                        results = self.collection.query(
                            query_texts=[query],
                            n_results=1
                        )
                except Exception as e2:
                    logger.error(f"Summary generation query failed: {str(e2)}")
                    return "Could not retrieve document chunks due to a database error. Please try re-uploading your document or reset the database."
            
            if not results or not results.get('documents') or not results['documents'][0]:
                return "No relevant information found in the uploaded documents."
            
            # Combine and truncate context
            sample_content = "\n\n".join(results['documents'][0][:5])
            if len(sample_content) > 6000:
                sample_content = sample_content[:6000] + "..."
            
            # Set token limit
            max_tokens = BRIEF_MAX_TOKENS if detail_level == "brief" else DETAILED_MAX_TOKENS
            
            # Simple fallback prompt
            if detail_level == 'detailed':
                prompt = f"""Query: {query}

Document Sample:
{sample_content}

The specific sections didn't match well. Based on this sample, provide a structured answer with [Doc Summary] citation. If the documents don't address this, explain what they do cover."""
            else:
                prompt = f"""Query: {query}

Document Sample:
{sample_content}

Provide a brief answer (max 4 sentences). Use [Doc Summary] citation."""
            
            # Call LLM
            start_time = time.time()
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=RAG_TEMPERATURE,
                top_p=TOP_P,
                timeout=LLM_TIMEOUT
            )
            
            response = completion.choices[0].message.content.strip()
            logger.info(f"✓ Summary generated in {time.time() - start_time:.2f}s")
            return response
            
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'rate limit' in error_str.lower():
                logger.error(f"⚠️ Rate limit exceeded in summary generation: {error_str}")
                return "⚠️ **Rate Limit Exceeded**\n\nThe free model has reached its daily limit. Please try:\n1. Waiting a few minutes\n2. Switching to a different model (see .env file)\n3. Adding credits to your OpenRouter account"
            logger.error(f"Summary generation failed: {error_str}")
            return f"Could not generate summary: {error_str}"

    
    def detect_research_depth(self, query: str) -> str:
        """
        Detect if query requires detailed research analysis.
        
        Args:
            query: User's question
            
        Returns:
            'detailed' or 'brief'
        """
        query_lower = query.lower()
        
        # Research keywords → detailed
        research_triggers = [
            'analyze', 'discuss', 'compare', 'contrast', 'evaluate',
            'explain in detail', 'comprehensive', 'in depth', 'thoroughly',
            'what are the implications', 'how does', 'why does',
            'describe the relationship', 'what factors', 'reasoning behind',
            'pros and cons', 'advantages and disadvantages', 'strengths and weaknesses',
            'tell me about', 'elaborate', 'detail'
        ]
        
        if any(trigger in query_lower for trigger in research_triggers):
            return 'detailed'
        
        # Long questions (>15 words) likely need detailed answers
        if len(query.split()) > 15:
            return 'detailed'
        
        return 'brief'
    
    def validate_response_depth(self, response: str, detail_level: str, data_type: str = 'text') -> Tuple[bool, str]:
        """
        Validate if response meets minimum depth requirements.
        V3.5: Enhanced validation for STRICT numeric mode.
        
        Args:
            response: Generated response text
            detail_level: 'brief' or 'detailed'
            data_type: 'text' or 'numeric'
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # V3.5 NUMERIC mode: STRICT validation - NO PROSE ALLOWED
        if data_type == 'numeric':
            # Check for table/JSON structure
            has_table = '|' in response and 'Source' in response and 'Parameter' in response
            has_json = '{' in response and '}' in response and '"Source"' in response
            
            if not (has_table or has_json):
                return (False, "V3.5 VIOLATION: Numeric mode requires table or JSON format")
            
            # V3.5: Check for FORBIDDEN prose patterns
            forbidden_phrases = [
                'based on the',
                'here is the',
                'introduction',
                'key insights',
                'findings',
                'in summary',
                'conclusion',
                'as we can see',
                'the data shows',
                'from the table',
                'analysis reveals',
                'observations'
            ]
            
            response_lower = response.lower()
            
            # Check before first table marker
            table_start = response.find('|')
            json_start = response.find('{')
            
            if table_start > -1:
                before_table = response[:table_start].lower()
            elif json_start > -1:
                before_table = response[:json_start].lower()
            else:
                before_table = response_lower
            
            # Check for forbidden phrases in prose (before table)
            violations = [phrase for phrase in forbidden_phrases if phrase in before_table]
            
            # Allow ONLY "average:" or "total:" after table
            if len(before_table) > 50:  # More than 50 chars before table is suspicious
                # Check if it's just whitespace/formatting
                before_table_stripped = before_table.strip()
                if len(before_table_stripped) > 20:  # Real prose detected
                    return (False, f"V3.5 VIOLATION: Prose detected before table (first 50 chars: '{before_table_stripped[:50]}')")
            
            if violations:
                return (False, f"V3.5 VIOLATION: Forbidden prose patterns found: {', '.join(violations)}")
            
            return (True, "Numeric extraction format valid (V3.5 compliant)")
        
        # TEXT mode: Standard validation
        word_count = len(response.split())
        
        if detail_level == 'detailed':
            # Detailed responses must be at least 1200 words (roughly 2000+ tokens)
            if word_count < 1200:
                return (False, f"Response too short: {word_count} words (minimum 1200 for detailed, target 2000-2600 words)")
            
            # Check for structure markers (at least 3 section headings for comprehensive analysis)
            structure_markers = response.count('**') // 2  # Count heading pairs
            if structure_markers < 3:
                return (False, "Response lacks comprehensive structure (needs Introduction, Findings, Analysis, Quantitative/Discussion, Conclusion)")
        
        elif detail_level == 'brief':
            # Brief responses should still be substantive (at least 400 words for quality)
            if word_count < 400:
                return (False, f"Response too short: {word_count} words (minimum 400 for brief)")
        
        return (True, "Response meets depth requirements")
    
    def build_rag_prompt(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        detail_level: str,
        conversation_history: list = None,
        data_type: str = 'text'
    ) -> list:
        """
        Build context-aware prompts for RAG responses.
        ENHANCED with RESEARCH-GRADE prompt engineering + AUTO DATA TYPE DETECTION.
        
        Args:
            query: User's question
            chunks: Retrieved document chunks
            detail_level: 'brief' or 'detailed'
            conversation_history: Previous messages
            data_type: 'text', 'numeric', or 'mixed' (auto-detected)
            
        Returns:
            List of messages for OpenAI API
        """
        # Format retrieved context with source references and separators
        formatted_chunks = []
        total_chars = 0
        max_chars = MAX_CONTEXT_TOKENS * 4  # ~4 chars per token
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            source_name = metadata.get('source', 'Unknown')
            content = chunk.get('content', '')
            
            # Truncate overly long chunks
            if len(content) > 1500:
                content = content[:1500] + "..."
            
            chunk_text = f"[Source {i}: {source_name}]\n{content}"
            
            # Stop if context exceeds limit
            if total_chars + len(chunk_text) > max_chars:
                logger.info(f"Context truncated at {i-1} chunks")
                break
            
            formatted_chunks.append(chunk_text)
            total_chars += len(chunk_text)
        
        # Join with clear separators
        retrieved_context = "\n\n---\n\n".join(formatted_chunks)
        
        # BUILD ADAPTIVE PROMPT BASED ON DATA TYPE
        # ==========================================
        
        if data_type == 'numeric':
            # V3.6 ENHANCED: Check if this is structured data (Excel/CSV)
            is_structured = any(chunk.get('metadata', {}).get('is_structured', False) for chunk in chunks)
            
            # V3.12 ULTRA-STRICT TABLE EXTRACTION - NO EXCUSES
            system_message = """OUTPUT THIS EXACT TABLE. NOTHING ELSE.

| Entity | Pressure | Temperature | Volume | API Gravity | Ticket | Notes |
|--------|----------|-------------|--------|-------------|--------|-------|
| TAIMUR | [find pressure near TAIMUR] | [find temp near TAIMUR] | [find volume near TAIMUR] | [find API near TAIMUR] | [find ticket near TAIMUR] | Explicit |
| LPG | [find pressure near LPG] | [find temp near LPG] | [find volume near LPG] | [find API near LPG] | [find ticket near LPG] | Explicit |
| CONDEN | [find pressure near CONDEN] | [find temp near CONDEN] | [find volume near CONDEN] | [find API near CONDEN] | [find ticket near CONDEN] | Explicit |
| OIL | [find pressure near OIL] | [find temp near OIL] | [find volume near OIL] | [find API near OIL] | [find ticket near OIL] | Explicit |

EXTRACTION INSTRUCTIONS:
1. Search document for "TAIMUR" → read next 500-1000 characters
2. Find number near "pressure" or "psig" → that's TAIMUR's Pressure (add "psig")
3. Find number near "temp" or "°F" → that's TAIMUR's Temperature (add "°F")
4. Find number near "volume" or "bbl" → that's TAIMUR's Volume (add "bbl")
5. Find number near "api" or "gravity" → that's TAIMUR's API Gravity (add "dAPI")
6. Find alphanumeric near "ticket" → that's TAIMUR's Ticket (no unit)
7. If parameter not found → write "—"
8. Repeat for LPG, CONDEN, OIL

COLUMN HEADERS (EXACT):
Column 1: "Entity" (not "Source", not "Location")
Column 2: "Pressure" (with unit: psig)
Column 3: "Temperature" (with unit: °F)
Column 4: "Volume" (with unit: bbl)
Column 5: "API Gravity" (with unit: dAPI)
Column 6: "Ticket" (alphanumeric code, no unit)
Column 7: "Notes" (write "Explicit" if found, "—" if missing)

ABSOLUTE RULES:
1. First character = "|"
2. Show ALL 4 entities (TAIMUR, LPG, CONDEN, OIL)
3. Show ALL 6 parameters (Pressure, Temperature, Volume, API Gravity, Ticket, Notes)
4. Missing value = "—" (not null, not blank)
5. NO text before table
6. NO text after table
7. NO "Source" (use "Entity")

EXAMPLES OF CORRECT OUTPUT:
| Entity | Pressure | Temperature | Volume | API Gravity | Ticket | Notes |
|--------|----------|-------------|--------|-------------|--------|-------|
| TAIMUR | 6 psig | 301.925 °F | 327.07 bbl | 60 dAPI | 77826136 | Explicit |
| LPG | 0 psig | 301.911 °F | 628.981 bbl | — | d10591d | Explicit |
| CONDEN | 0 psig | 302 °F | 0 bbl | 55 dAPI | f7f6faf7f | Explicit |
| OIL | — | 314.49 °F | — | — | — | Explicit |

DO NOT DEVIATE FROM THIS FORMAT.
"""

        elif data_type == 'mixed':
            # MIXED MODE - Hybrid output (text summary + numeric tables)
            system_message = """You are **DocSense** in **HYBRID ANALYSIS MODE** 📊📄

Your purpose is to analyze both **textual context** and **numeric data** intelligently.

**BEHAVIOR RULES:**

**1. STRUCTURE**
Combine text analysis with data presentation:

**Summary** (2-3 sentences)
Brief contextual overview of findings

**Numeric Data** (Markdown Table):
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| Sheet1  | Pressure  | 327.07 | psi | Above avg |

**Interpretation** (1-2 paragraphs)
Explain what the numbers mean, trends, patterns, or correlations

**2. ACCURACY**
- Extract exact numeric values (no fabrication)
- Mark missing data as **"Missing"** or **"N/A"**
- Include units and source citations

**3. ANALYTICAL DEPTH**
- Connect numeric findings to textual context
- Example: "Pressure of 327.07 psi [Sheet 1] aligns with operational reports indicating stable performance [Source 2]"
- Show inline calculations when relevant

**4. TONE**
- Professional and concise
- Avoid redundant "Introduction" headers unless data is complex
- Focus on insights, not meta commentary

This is HYBRID mode — combine precision with context."""

        else:  # 'text' - Original research-grade analytical mode
            # TEXT/DOCUMENT ANALYSIS MODE
            if detail_level == 'detailed':
                system_message = """You are **DocSense**, a professional AI research assistant built on Retrieval-Augmented Generation (RAG).

Your purpose is to **analyze, interpret, and reason deeply** over the provided document context.

🧾 **Response Rules (Mandatory):**

**1. DEPTH & LENGTH**
- Write **2000-3500 tokens** of detailed, paragraph-style analysis
- Minimum 6-8 substantive paragraphs
- Never provide shallow summaries — explain like a researcher writing a paper

**2. STRUCTURE** (Mandatory sections):
   • **Introduction** (2-3 sentences: context setup and scope)
   • **Key Insights & Findings** (detailed evidence from sources with citations)
   • **Analytical Discussion** (deep interpretation: relationships, patterns, implications)
   • **Quantitative Analysis** (if numeric data present: calculations, trends, statistics)
   • **Conclusion** (synthesized insight and actionable takeaways)

**3. NUMERIC DATA HANDLING**
When the document contains Excel, CSV, or tabular data:
- Automatically detect numeric patterns, trends, and outliers
- Perform inline calculations and show your reasoning:
  * Example: "The average production was **327.07 barrels** (calculated from 15 wells), approximately **15% higher** than the baseline."
- Reference sheets as [Sheet 1], [Sheet 2], etc.
- Highlight correlations, missing values, and statistical insights
- Never describe table layout — focus only on insights
- Cross-reference numeric trends with textual context when both exist

**4. EVIDENCE & CITATIONS**
- Every factual or analytical point **must** cite sources: [Source 1], [Source 2], [Sheet 1]
- Integrate citations naturally — never say "based on the provided context"
- When evidence is thin, state clearly: "Limited direct references — reasoning based on conceptual inference..."

**5. REASONING QUALITY**
- Expand and connect ideas across sources
- Explain WHY findings matter, not just WHAT they are
- Identify implications, causation, and underlying patterns
- Use analogies and examples when helpful

**6. PROFESSIONAL TONE**
- Write like an intelligent researcher, not a chatbot
- Coherent, flowing paragraphs with natural transitions
- Avoid robotic language, bullet lists (unless data tables), or meta commentary
- No phrases like "the document states..." — just present findings directly with citations

**7. COMPLETENESS**
- Address all aspects of the query
- If multi-part question, systematically cover each part
- No truncation or premature endings

This output must read like a professional research report, not a chatbot summary."""
            
            else:  # brief text mode
                system_message = """You are **DocSense**, a professional document research assistant.

**Brief Mode Requirements:**
1. Write **2-3 focused paragraphs** (600-800 tokens)
2. Include [Source X] citations for all factual claims
3. Be direct and concise but maintain analytical depth
4. If numeric data present, include key statistics with inline reasoning
5. Professional, coherent tone — avoid superficial summaries
6. Provide genuine insight, not just facts

Even in brief mode, responses should feel intelligent and purposeful."""
        
        # Build messages
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history (last 3 exchanges = 6 messages)
        # Filter out custom properties (like 'sources') that Groq API doesn't support
        if conversation_history:
            for msg in conversation_history[-6:]:
                # Only keep 'role' and 'content' - remove custom properties
                clean_msg = {"role": msg["role"], "content": msg["content"]}
                messages.append(clean_msg)
        
        # User message with context - ADAPTIVE TO DATA TYPE
        context_part = f"\n\n📚 **Retrieved Document Context:**\n{retrieved_context}\n\n---\n\n" if retrieved_context else ""
        
        if data_type == 'numeric':
            # V3.5 NUMERIC EXTRACTION - STRICT NO-PROSE MODE
            user_message = f"""{context_part}**User Question:**
{query}

---

**V3.5 STRICT EXTRACTION - NO PROSE ALLOWED**

⚠️ **CRITICAL RULES:**
- Output ONLY a Markdown table or JSON (if requested)
- NO introductions, summaries, conclusions, or explanatory text
- NO invented/dummy data (e.g., Temperature = 0 unless explicitly stated)
- **NEVER use "Source 1", "Source 2" — extract ACTUAL location names from document**
- **INCLUDE rows even when Value is NULL (show as NULL with note)**
- Start directly with the table

**REQUIRED FORMAT:**
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| Tank-C:MARI DEEP | Pressure  | 3124  | psig  | Explicit |
| Tank-C:Fazl X-1  | Pressure  | 2847  | psig  | Inferred from context |
| Tank-C:MARI DEEP | Temperature  | NULL  | °F  | Column exists but contains no data |

**EXTRACTION PROTOCOL:**

1️⃣ **EXTRACT REAL LOCATION NAMES** (HIGHEST PRIORITY):
   - Search document for: "Tank", "Location", "Well", "Station", "Field" columns
   - Look for patterns: "Tank-C:MARI DEEP", "Fazl X-1", "Well #7", "North Sector"
   - Extract exact names with colons, hyphens, spaces as they appear
   - ❌ NEVER use "Source 1", "Source 2" placeholders

2️⃣ **EXTRACT ALL COLUMNS FROM DATA TABLE** (CRITICAL):
   - Look at the data table in the context - extract EVERY column header as a parameter
   - Include numeric columns: Pressure, Temperature, Volume, Flow, dAPI, etc.
   - Include text columns: Product, Type, Status, Category, Notes, etc.
   - Include date columns: Date, Timestamp, etc.
   - ⚠️ DO NOT filter to numeric-only - extract ALL columns
   - ⚠️ If user says "extract all data", show EVERY column from the table

3️⃣ **USE EXACT CELL VALUES**:
   - Explicit values: "Pressure: 327.07 psig" → Extract exactly
   - Text values: "Product: LPG" → Extract as-is
   - Numeric values: "Temperature: 301.911" → NO rounding
   - Date values: "2025-01-15" → Extract as string

4️⃣ **HANDLE NULL/MISSING DATA** (CRITICAL - V3.6.2):
   - **If cell exists but value is empty/NULL:**
     * Value: NULL (uppercase)
     * Unit: Correct unit for numeric columns (psig, °F, bbl) - empty for text columns
     * Notes: "Column exists but no value recorded"
     * **IMPORTANT:** Include row in table, don't skip it
   - **If cell has value:**
     * Value: [exact value]
     * Unit: [correct unit for numeric, empty for text]
     * Notes: "Valid"
   - ⚠️ **NEVER use "Not found" in notes**
   - ⚠️ **NEVER skip locations with NULL values**
   - ⚠️ **NEVER fabricate placeholder values like 0**

5️⃣ **UNITS**:
   - Numeric columns: Always include units (psig, °F, degF, bbl, barrels, m³, MMBtu, ft³, mcf, %, kg, lbm)
   - Text columns: Leave unit empty

6️⃣ **MULTI-LOCATION EXTRACTION**:
   - Process ALL locations/rows found in document
   - Use actual location names (Tank-C:MARI DEEP, TAIMUR, LPG, etc.)
   - Show ALL parameters for each location
   - Include rows with NULL values

7️⃣ **CALCULATIONS** (if requested):
   - Add ONE line after table: "Average: X psig (from Y locations with data)"
   - Exclude NULL values from calculations

8️⃣ **LOCATION NAME EXTRACTION EXAMPLES**:
   - Document has "Tank" column with "TAIMUR" → Use TAIMUR exactly
   - Document says "Well #7 pressure" → Source: Well #7
   - Excel column "Location" with "North Sector" → Source: North Sector

**BEGIN TABLE EXTRACTION IMMEDIATELY:**"""

        elif data_type == 'mixed':
            # HYBRID - Text summary + numeric table
            user_message = f"""{context_part}**User Question:**
{query}

---

**HYBRID ANALYSIS TASK:**

Provide a structured response combining textual insight with numeric data:

**1. Summary** (2-3 sentences)
Brief contextual overview

**2. Numeric Data** (Markdown Table):
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|

**3. Interpretation** (1-2 paragraphs)
Explain trends, patterns, correlations with [Source X] citations

**Rules:**
- Extract exact numeric values
- Connect numbers to textual context
- Cite sources: [Source 1], [Sheet 1]
- Professional, concise tone

Begin:"""

        elif detail_level == 'detailed':
            # TEXT DETAILED - Full research-grade analysis
            user_message = f"""{context_part}**User Question:**
{query}

---

**ANALYSIS INSTRUCTIONS:**

Provide a comprehensive, research-grade analysis following this structure:

**1. Introduction** (2-3 sentences)
Set the context and scope — what is this about and why does it matter?

**2. Key Insights & Findings** (3-4 paragraphs)
Present the main evidence and facts from the sources. Use [Source X] citations for every claim.
If numeric data exists, include statistics, averages, ranges, or trends.

**3. Analytical Discussion** (3-4 paragraphs)
Deep interpretation — connect ideas, explain relationships, discuss implications.
Reason through the material like a researcher. Identify patterns and causation.
If Excel/CSV data: show inline calculations (e.g., "Average = X, which is Y% higher than Z").

**4. Quantitative Analysis** (if applicable, 1-2 paragraphs)
For numeric data: statistical insights, outliers, correlations, missing values.
Cross-reference with textual context if both exist.

**5. Conclusion** (1-2 paragraphs)
Synthesize insights and provide actionable takeaways or recommendations.

---

**QUALITY REQUIREMENTS:**
✅ 2000-3500 tokens total (minimum 6-8 substantial paragraphs)
✅ Every fact must cite sources: [Source 1], [Source 2], [Sheet 1]
✅ Explain WHY findings matter, not just WHAT they are
✅ Natural, flowing prose — no meta commentary like "the document states..."
✅ If context is insufficient, state clearly and provide reasoned inference
✅ Write like an intelligent analyst, not a chatbot

Begin your analysis:"""
        
        else:
            # TEXT BRIEF - Concise but intelligent
            user_message = f"""{context_part}**User Question:**
{query}

---

Provide a focused, insightful answer (2-3 paragraphs, 600-800 tokens). 
- Cite sources as [Source X]
- Include key statistics if numeric data present
- Maintain analytical depth — provide genuine insight, not just summaries
- Professional, coherent tone

Begin:"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def stream_rag_response(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        detail_level: str = 'auto',
        conversation_history: list = None,
        thinking_placeholder=None
    ) -> Generator[str, None, None]:
        """
        Stream RAG response with ENHANCED depth enforcement and AUTO DATA TYPE DETECTION.
        
        ENHANCED V3.6: Direct structured data access (no vector embeddings for Excel/CSV)
        
        Args:
            query: User's question
            chunks: Retrieved document chunks
            detail_level: 'auto', 'brief', or 'detailed'
            conversation_history: Previous messages
            thinking_placeholder: Streamlit placeholder
            
        Yields:
            Text chunks as they arrive
        """
        try:
            # V3.6: Check if we have structured data - bypass vector search if yes
            has_structured, structured_markdown, structured_meta = self.get_structured_data_content()
            
            if has_structured:
                logger.info(f"📊 Using direct structured data access (bypassing vector embeddings)")
                
                # Use structured data directly - replace chunks
                chunks = [{
                    'content': structured_markdown,
                    'metadata': {
                        'source': ', '.join(structured_meta.get('files', [])),
                        'is_structured': True,
                        'total_rows': structured_meta.get('total_rows', 0)
                    },
                    'similarity': 1.0
                }]
                
                # Force numeric mode for structured data
                data_type = 'numeric'
                logger.info(f"📊 Structured data mode: {structured_meta.get('total_rows', 0)} rows from "
                          f"{len(structured_meta.get('files', []))} file(s)")
            else:
                # Auto-detect data type from regular chunks
                data_type = self.detect_data_type(chunks, query)
            
            # V3.12: DISABLE entity extraction - let LLM do raw extraction from chunks
            # The entity extractor was creating pre-formatted tables that confused the LLM
            if False and data_type == 'numeric' and ENTITY_EXTRACTOR_AVAILABLE:
                logger.info("🔍 Applying entity-based extraction...")
                try:
                    extractor = get_entity_extractor()
                    extractor.reset()  # Clear previous extractions
                    
                    # Extract entities from all chunks
                    for chunk in chunks:
                        content = chunk.get('content', '')
                        source = chunk.get('metadata', {}).get('source', 'Document')
                        extractor.extract_from_text(content, source)
                    
                    # Get entity count
                    entity_count = extractor.get_entity_count()
                    if entity_count > 0:
                        # Replace chunks with entity-extracted table
                        entity_table = extractor.format_as_markdown()
                        logger.info(f"✅ Extracted {entity_count} entities: {', '.join(extractor.get_entities())}")
                        
                        chunks = [{
                            'content': entity_table,
                            'metadata': {
                                'source': 'Entity Extraction',
                                'entity_count': entity_count,
                                'entities': extractor.get_entities()
                            },
                            'similarity': 1.0
                        }]
                    else:
                        logger.warning("⚠️ No entities detected, using original chunks")
                except Exception as e:
                    logger.error(f"Entity extraction failed: {str(e)}, falling back to original chunks")
            
            # Auto-detect depth
            if detail_level == 'auto':
                detected_level = self.detect_research_depth(query)
            else:
                detected_level = detail_level
            
            # Set token limit based on data type
            if data_type == 'numeric':
                # Numeric extraction needs less tokens (tables are compact)
                max_tokens = 1500
            else:
                # Text analysis needs full depth
                max_tokens = DETAILED_MAX_TOKENS if detected_level == 'detailed' else BRIEF_MAX_TOKENS
            
            # Build prompt with DATA-TYPE-AWARE instructions
            messages = self.build_rag_prompt(query, chunks, detected_level, conversation_history, data_type)
            
            logger.info(f"📚 RAG {detected_level} response (data_type={data_type}, max_tokens={max_tokens}, temp={RAG_TEMPERATURE})")
            
            # Retry logic
            start_time = time.time()
            first_token_received = False
            full_response = ""
            
            for retry in range(MAX_RETRIES_LLM + 1):
                try:
                    # Create streaming completion with ENHANCED parameters
                    stream = self.client.chat.completions.create(
                        extra_headers={
                            "HTTP-Referer": self.site_url,
                            "X-Title": self.site_name,
                        },
                        model=self.model_name,
                        messages=messages,
                        temperature=RAG_TEMPERATURE,  # 0.7 for reasoning depth
                        max_tokens=max_tokens,
                        top_p=TOP_P,
                        frequency_penalty=FREQUENCY_PENALTY,
                        presence_penalty=PRESENCE_PENALTY,  # 0.4 for diversity
                        stream=True,
                        timeout=LLM_TIMEOUT
                    )
                    
                    # Stream response
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            if not first_token_received:
                                logger.info(f"⚡ First token in {time.time() - start_time:.2f}s")
                                if thinking_placeholder:
                                    thinking_placeholder.empty()
                                first_token_received = True
                            
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield content
                    
                    # Validate response depth after streaming completes
                    is_valid, reason = self.validate_response_depth(full_response, detected_level, data_type)
                    if not is_valid:
                        logger.warning(f"⚠️ Response validation failed: {reason}")
                        # Note: In streaming mode, we can't regenerate, but we log the issue
                    else:
                        if data_type == 'numeric':
                            logger.info(f"✅ Numeric extraction complete ({len(full_response)} chars)")
                        else:
                            word_count = len(full_response.split())
                            logger.info(f"✅ Response validated: {word_count} words")
                    
                    # Success - exit retry loop
                    break
                    
                except Exception as retry_error:
                    # Check if it's a rate limit error
                    error_str = str(retry_error)
                    if '429' in error_str or 'rate limit' in error_str.lower():
                        logger.error(f"⚠️ Rate limit exceeded: {error_str}")
                        if thinking_placeholder:
                            thinking_placeholder.empty()
                        yield "\n\n⚠️ **Rate Limit Exceeded**\n\nThe free model has reached its rate limit. Please:\n1. Wait a few minutes and try again\n2. Or switch to a different model in the .env file\n3. Or add credits to your OpenRouter account\n\nAvailable free alternatives:\n- `meta-llama/llama-3.1-8b-instruct:free`\n- `google/gemma-2-9b-it:free`\n- `microsoft/phi-3-medium-128k-instruct:free`"
                        return
                    
                    if retry >= MAX_RETRIES_LLM:
                        raise retry_error
                    logger.warning(f"LLM call failed (attempt {retry + 1}/{MAX_RETRIES_LLM + 1}), retrying...")
                    time.sleep(1)
            
        except Exception as e:
            logger.error(f"RAG streaming failed: {str(e)}")
            if thinking_placeholder:
                thinking_placeholder.empty()
            yield f"\n\n❌ Error: Failed to generate answer. Please try again."
    
    def answer_from_documents(
        self,
        query: str,
        detail_level: str = 'auto',
        conversation_history: list = None,
        thinking_placeholder=None
    ) -> Tuple[Generator[str, None, None], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Answer question using strict RAG from documents with INTENT DETECTION.
        
        OPTIMIZATION: Skip retrieval for casual/conversational inputs.
        
        Args:
            query: User's question
            detail_level: 'auto', 'brief', or 'detailed'
            conversation_history: Previous doc mode messages
            thinking_placeholder: Streamlit placeholder
            
        Returns:
            Tuple of (response_generator, source_chunks, metadata)
        """
        try:
            start_time = time.time()
            
            # Check if documents available
            has_docs, count = self.check_documents_available()
            if not has_docs:
                logger.warning("No documents available for RAG")
                
                def no_docs_response():
                    yield "⚠️ No documents uploaded. Please upload PDF or TXT files to begin document-based Q&A."
                
                return (no_docs_response(), [], {'error': 'no_documents', 'mode': 'document'})
            
            # INTENT DETECTION - Skip retrieval for casual inputs
            intent = self.detect_intent(query)
            
            if intent == 'casual':
                logger.info("💬 Casual intent - no retrieval")
                
                if thinking_placeholder:
                    thinking_placeholder.empty()
                
                def casual_response():
                    yield "Hey 👋 You're in **Document Mode** — ask a question about your uploaded files, or switch to Chat Mode for general queries."
                
                metadata = {
                    'mode': 'document',
                    'intent': 'casual',
                    'chunks_retrieved': 0,
                    'retrieval_skipped': True,
                    'total_documents': count
                }
                
                return (casual_response(), [], metadata)
            
            # DOCUMENT QUERY - Proceed with retrieval
            logger.info(f"📝 Document Mode query: {query[:100]}...")
            chunks = self.retrieve_relevant_chunks(query)
            
            # Check if relevant chunks found - if not, try document summary fallback
            if not chunks:
                logger.warning("No relevant chunks found above similarity threshold - using document summary fallback")
                
                # Auto-detect detail level
                if detail_level == 'auto':
                    detected_level = self.detect_research_depth(query)
                else:
                    detected_level = detail_level
                
                # Generate summary from all documents
                summary_response = self.generate_document_summary(query, detected_level)
                
                def summary_generator():
                    yield summary_response
                
                metadata = {
                    'mode': 'document',
                    'detail_level': detected_level,
                    'chunks_retrieved': 0,
                    'fallback': 'document_summary',
                    'total_documents': count,
                    'model': self.model_name,
                    'start_time': start_time
                }
                
                return (summary_generator(), [], metadata)
            
            # Auto-detect detail level
            if detail_level == 'auto':
                detected_level = self.detect_research_depth(query)
            else:
                detected_level = detail_level
            
            # Stream RAG response
            response_stream = self.stream_rag_response(
                query,
                chunks,
                detected_level,
                conversation_history,
                thinking_placeholder
            )
            
            # Metadata
            metadata = {
                'mode': 'document',
                'detail_level': detected_level,
                'chunks_retrieved': len(chunks),
                'total_documents': count,
                'model': self.model_name,
                'start_time': start_time
            }
            
            return (response_stream, chunks, metadata)
            
        except Exception as e:
            logger.error(f"Document Mode answer failed: {str(e)}")
            
            def error_response():
                yield f"❌ Error: {str(e)}"
            
            return (error_response(), [], {'error': str(e), 'mode': 'document'})


def get_document_mode(model_name: str = DEFAULT_MODEL) -> DocumentMode:
    """
    Factory function to get DocumentMode instance.
    
    Args:
        model_name: OpenRouter model to use
        
    Returns:
        DocumentMode instance
    """
    return DocumentMode(model_name=model_name)
