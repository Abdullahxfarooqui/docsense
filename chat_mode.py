"""
Chat Mode Module - Pure Conversational AI

This module handles general conversational AI interactions without any document retrieval.
Completely isolated from document mode - no ChromaDB, no embeddings, no RAG.

Features:
- Adaptive response depth based on query complexity
- Short responses for casual queries
- Detailed, structured responses for analytical questions
- User-controlled detail level (Brief/Detailed)
- Session-based chat history

Author: AI Assistant
Created: October 2025
"""

import logging
import os
from typing import Generator, Dict, Any, Tuple
import time

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 3

# Response depth settings - GROQ OPTIMIZED FOR CHATGPT-LIKE QUALITY
BRIEF_MAX_TOKENS = 800  # Brief: Concise but insightful
DETAILED_MAX_TOKENS = 4096  # Detailed: Deep, ChatGPT-like analysis
BRIEF_TEMPERATURE = 0.7
DETAILED_TEMPERATURE = 0.65  # Balanced for analytical reasoning
TOP_P = 0.9
FREQUENCY_PENALTY = 0.3
PRESENCE_PENALTY = 0.3


class ChatModeError(Exception):
    """Custom exception for chat mode errors."""
    pass


class ChatMode:
    """
    Pure conversational AI mode - no document retrieval.
    
    Handles general questions with adaptive response depth:
    - Brief mode: Quick, concise answers
    - Detailed mode: Comprehensive, structured responses
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize Chat Mode.
        
        Args:
            model_name: OpenRouter model to use
        """
        try:
            self.model_name = model_name
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
            self.site_url = os.getenv("SITE_URL", "http://localhost:8501")
            self.site_name = os.getenv("SITE_NAME", "DocSense - Chat Mode")
            
            if not self.api_key:
                raise ChatModeError("OPENAI_API_KEY not set")
            
            # Initialize OpenRouter client
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            logger.info(f"✓ Chat Mode initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chat Mode: {str(e)}")
            raise ChatModeError(f"Chat Mode initialization failed: {str(e)}")
    
    def detect_query_complexity(self, query: str) -> str:
        """
        Detect if query requires detailed or brief response.
        
        Args:
            query: User's question
            
        Returns:
            'detailed' or 'brief'
        """
        query_lower = query.lower().strip()
        
        # Casual/greeting keywords → brief
        casual_patterns = [
            'hello', 'hi', 'hey', 'thanks', 'thank you', 'bye',
            'good morning', 'good evening', 'how are you',
            'what\'s up', 'whats up', 'sup'
        ]
        
        if any(pattern in query_lower for pattern in casual_patterns):
            return 'brief'
        
        # Very short queries (≤5 words) → brief unless analytical
        if len(query.split()) <= 5:
            analytical_keywords = [
                'why', 'how', 'explain', 'compare', 'analyze',
                'discuss', 'describe', 'elaborate'
            ]
            if not any(kw in query_lower for kw in analytical_keywords):
                return 'brief'
        
        # Analytical keywords → detailed
        detailed_triggers = [
            'why', 'how does', 'how can', 'how to', 'explain',
            'compare', 'contrast', 'analyze', 'discuss', 'describe',
            'elaborate', 'detail', 'comprehensive', 'in depth',
            'what are the implications', 'what factors', 'reasoning',
            'pros and cons', 'advantages and disadvantages'
        ]
        
        if any(trigger in query_lower for trigger in detailed_triggers):
            return 'detailed'
        
        # Default to brief for efficiency
        return 'brief'
    
    def build_prompt(self, query: str, detail_level: str, conversation_history: list = None) -> list:
        """
        Build conversation messages - simple and context-aware.
        
        Args:
            query: User's current question
            detail_level: 'brief' or 'detailed'
            conversation_history: Previous messages
            
        Returns:
            List of message dicts for OpenAI API
        """
        # Conditional system message
        if detail_level == 'detailed':
            system_message = """You are a helpful, intelligent AI assistant — like ChatGPT.

**Your Purpose:**
- Provide clear, informative, and well-reasoned responses
- Think deeply and explain concepts thoroughly when asked
- Be conversational yet professional
- Use natural language without robotic patterns

**Important:**
- You are in CHAT MODE (no document access)
- If asked about uploaded files or documents, respond:
  "You're in Chat Mode — switch to Document Mode to analyze your uploaded files."
- Answer general knowledge questions naturally and comprehensively
- Structure detailed responses with clear paragraphs and logical flow"""
        else:
            system_message = """You are a helpful AI assistant in CHAT MODE.

Be concise, friendly, and to the point. If asked about documents, remind the user to switch to Document Mode."""
        
        # Build message list
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history (last 5 exchanges)
        if conversation_history:
            messages.extend(conversation_history[-10:])
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def stream_response(
        self,
        query: str,
        detail_level: str = 'auto',
        conversation_history: list = None,
        thinking_placeholder=None
    ) -> Generator[str, None, None]:
        """
        Stream conversational response from the LLM.
        
        Args:
            query: User's question
            detail_level: 'auto', 'brief', or 'detailed'
            conversation_history: Previous conversation messages
            thinking_placeholder: Streamlit placeholder to clear on first token
            
        Yields:
            Text chunks as they arrive
        """
        try:
            # Auto-detect complexity if needed
            if detail_level == 'auto':
                detected_level = self.detect_query_complexity(query)
                logger.info(f"Auto-detected complexity: {detected_level} for query: {query[:50]}...")
            else:
                detected_level = detail_level
            
            # Set generation parameters based on detail level
            if detected_level == 'detailed':
                max_tokens = DETAILED_MAX_TOKENS
                temperature = DETAILED_TEMPERATURE
            else:
                max_tokens = BRIEF_MAX_TOKENS
                temperature = BRIEF_TEMPERATURE
            
            # Build messages
            messages = self.build_prompt(query, detected_level, conversation_history)
            
            logger.info(f"🧠 Chat Mode: {detected_level} response (max_tokens={max_tokens})")
            
            # Track first token timing
            start_time = time.time()
            first_token_received = False
            
            # Create streaming completion
            stream = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=TOP_P,
                frequency_penalty=FREQUENCY_PENALTY,
                presence_penalty=PRESENCE_PENALTY,
                stream=True
            )
            
            # Stream the response
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    # Clear thinking placeholder on first token
                    if not first_token_received:
                        first_token_time = time.time() - start_time
                        logger.info(f"⚡ First token in {first_token_time:.2f}s")
                        if thinking_placeholder:
                            thinking_placeholder.empty()
                        first_token_received = True
                    
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'rate limit' in error_str.lower():
                logger.error(f"⚠️ Rate limit exceeded: {error_str}")
                if thinking_placeholder:
                    thinking_placeholder.empty()
                yield "\n\n⚠️ **Rate Limit Exceeded**\n\nThe free model has reached its rate limit. Please:\n1. Wait a few minutes and try again\n2. Or switch to a different model in the .env file\n3. Or add credits to your OpenRouter account"
            else:
                logger.error(f"Chat Mode streaming failed: {error_str}")
                if thinking_placeholder:
                    thinking_placeholder.empty()
                yield f"\n\n❌ Error: Failed to generate response. Please try again."
    
    def generate_response(
        self,
        query: str,
        detail_level: str = 'auto',
        conversation_history: list = None,
        thinking_placeholder=None
    ) -> Tuple[Generator[str, None, None], Dict[str, Any]]:
        """
        Generate a conversational response.
        
        Args:
            query: User's question
            detail_level: 'auto', 'brief', or 'detailed'
            conversation_history: Previous conversation messages
            thinking_placeholder: Streamlit placeholder
            
        Returns:
            Tuple of (response_generator, metadata)
        """
        start_time = time.time()
        
        # Auto-detect if needed
        if detail_level == 'auto':
            detected_level = self.detect_query_complexity(query)
        else:
            detected_level = detail_level
        
        # Stream the response
        response_stream = self.stream_response(
            query,
            detected_level,
            conversation_history,
            thinking_placeholder
        )
        
        # Metadata
        metadata = {
            'mode': 'chat',
            'detail_level': detected_level,
            'model': self.model_name,
            'start_time': start_time
        }
        
        return response_stream, metadata


def get_chat_mode(model_name: str = DEFAULT_MODEL) -> ChatMode:
    """
    Factory function to get ChatMode instance.
    
    Args:
        model_name: OpenRouter model to use
        
    Returns:
        ChatMode instance
    """
    return ChatMode(model_name=model_name)
