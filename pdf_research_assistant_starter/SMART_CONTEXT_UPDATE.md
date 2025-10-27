# Smart Context & Cache Management Update

## Overview
DocSense now features **intelligent context detection** and **smart cache management** that automatically determines when to use document retrieval vs. general conversation.

---

## 🧠 Key Features

### 1. **Intelligent Document Detection**
The system automatically decides whether to use uploaded documents based on:

- **Document Availability**: Checks if any documents are loaded in ChromaDB
- **Question Analysis**: Analyzes keywords to detect document-related queries
- **Context Awareness**: Distinguishes between general chat and document-specific questions

**Example Behaviors:**
```
User: "hey" or "hello"
→ Generic chat response (no document retrieval)

User: "What does the research paper say about climate change?"
→ Document retrieval activated (keywords: "research paper", "say about")

User: "Explain quantum computing"
→ Light mode (generic knowledge, no documents needed)
```

### 2. **Smart Cache Handling**
**File Hash Tracking:**
- Computes MD5 hash of uploaded files (name + size)
- Stores hash in `st.session_state.current_doc_hash`
- Compares before reprocessing

**Benefits:**
- ✅ **No Redundant Processing**: Same files = instant load from cache
- ✅ **Automatic Invalidation**: New files = auto-clear and reprocess
- ✅ **Session Persistence**: Documents stay loaded across queries

**Visual Feedback:**
```
First Upload:    "✨ New - Processing completed successfully!"
Same Files:      "✅ Documents already processed! Using cached embeddings"
Changed Files:   "🔄 Updated - Processing completed successfully!"
```

### 3. **Context-Aware Responses**

#### Mode 1: No Documents
**Trigger**: No files uploaded, ChromaDB empty

**Behavior**:
- Skips ChromaDB retrieval entirely
- Responds conversationally like ChatGPT
- Never says "synthesizing document"

**Example:**
```
User: "What's the weather like?"
Assistant: "I'm DocSense, an AI assistant. I don't have access to real-time 
weather data, but you can check weather.com or your local weather service..."
```

#### Mode 2: Generic Chat (Documents Loaded)
**Trigger**: Documents exist but question is generic (≤3 words, no doc keywords)

**Behavior**:
- Light retrieval mode (minimal processing)
- Fast, conversational responses
- No heavy ChromaDB search

**Example:**
```
User: "hey"
Assistant: "Hello! I'm DocSense. I can help you analyze the documents you've 
uploaded or answer general questions. What would you like to know?"
```

#### Mode 3: Document-Based Q&A
**Trigger**: Document keywords detected OR specific question

**Behavior**:
- Full semantic search through ChromaDB
- Retrieves top 5 most relevant chunks
- Synthesizes answer with citations

**Example:**
```
User: "What are the main findings in the uploaded research?"
Assistant: "Based on the research documents, the main findings are:
1. [detailed synthesis with citations]
2. [Source 2, Chunk 5] shows that...
..."
```

---

## 🔧 Technical Implementation

### **ingestion.py Changes**

#### New Function: `compute_file_hash()`
```python
def compute_file_hash(uploaded_files: List[BinaryIO]) -> str:
    """Compute MD5 hash of all uploaded files for change detection"""
    hash_content = ""
    for file_obj in uploaded_files:
        filename = getattr(file_obj, 'name', 'unknown')
        file_size = getattr(file_obj, 'size', 0)
        hash_content += f"{filename}:{file_size};"
    
    return hashlib.md5(hash_content.encode()).hexdigest()
```

#### Updated Function: `ingest_documents()`
**New Signature:**
```python
def ingest_documents(
    uploaded_files: List[BinaryIO], 
    session_doc_hash: Optional[str] = None
) -> Tuple[int, int, str]:
    """Returns: (chunks, files, hash)"""
```

**Smart Logic:**
1. Compute hash of new files
2. Compare with `session_doc_hash`
3. If same → return stats from cache (no reprocessing)
4. If different → clear ChromaDB and reprocess
5. Return new hash for storage

### **query_engine.py Changes**

#### Enhanced Function: `answer_question_streaming()`
**New Parameter:**
```python
def answer_question_streaming(
    self, 
    question: str, 
    thinking_placeholder=None, 
    use_documents: bool = True  # Auto-detected
) -> Tuple[Generator, List, Dict]:
```

**Smart Decision Tree:**
```python
# Step 1: Check ChromaDB
collection_count = self.collection.count()

if collection_count == 0:
    # No documents → generic response
    return generic_chat_mode()

# Step 2: Analyze question
doc_keywords = ['document', 'pdf', 'research', 'paper', 'study', 
                'according to', 'mentions', 'states', ...]

seems_document_related = any(kw in question.lower() for kw in doc_keywords)
is_generic_chat = len(question.split()) <= 3 and not seems_document_related

if is_generic_chat:
    # Generic → light response
    return light_chat_mode()

# Step 3: Document-related → full retrieval
return full_document_retrieval()
```

### **app.py Changes**

#### Smart Status Indicator
```python
if has_documents:
    st.caption(f"📚 {doc_count} documents loaded ({chunk_count} chunks)")
else:
    st.caption("💡 Upload documents to unlock document-based Q&A, or chat normally")
```

#### Context-Aware Prompts
```python
# Dynamic chat input placeholder
prompt_placeholder = (
    "Ask a question about your documents..." if has_documents 
    else "Chat with DocSense AI..."
)
```

#### Performance Metrics (Conditional)
```python
# Only show document metrics if retrieval was used
if metrics.get('document_used', False):
    chunks_used = metrics.get('chunks_used', 0)
    if chunks_used > 0:
        st.caption(f"📚 Retrieved {chunks_used} chunks in {retrieval_time:.2f}s")
```

---

## 📊 Session State Architecture

### New State Variables
```python
st.session_state.current_doc_hash = "abc123def456..."  # MD5 hash
st.session_state.messages = [...]                      # Chat history
st.session_state.query_cache = {...}                   # Query results
st.session_state.show_sources = True/False             # UI preference
```

### Hash Lifecycle
```
1. Upload Files → compute_file_hash() → "abc123"
2. Store in session_state.current_doc_hash = "abc123"
3. Next Upload → compute_file_hash() → "abc123" (same)
4. Compare: "abc123" == "abc123" → Skip processing!
5. Different Files → "xyz789" → Clear & reprocess
```

---

## 🎯 User Experience Improvements

### Before This Update
❌ Always searched documents even for "hi" or "hello"  
❌ Reprocessed same files every time  
❌ Said "synthesizing document" when no docs uploaded  
❌ Wasted API calls on irrelevant queries  

### After This Update
✅ **Smart Mode Selection**: Generic chat vs. document search  
✅ **Instant Cache Loading**: Same files = 0s reprocessing  
✅ **Appropriate Responses**: Never claims to search non-existent docs  
✅ **Optimized API Usage**: Only retrieves when necessary  
✅ **Visual Feedback**: Shows doc status and cache hits  

---

## 🚀 Testing the New Features

### Test 1: Generic Chat (No Documents)
```
1. Start fresh session (no uploads)
2. Type: "hello"
3. ✅ Expected: Friendly greeting, no "searching documents" message
```

### Test 2: Cache Validation
```
1. Upload: research.pdf (1.2 MB)
2. Process → "✨ New - Processing completed!"
3. Upload SAME file again
4. ✅ Expected: "✅ Documents already processed! Using cached embeddings"
```

### Test 3: Document Change Detection
```
1. Upload: paper1.pdf
2. Process → Hash: "abc123"
3. Upload: paper2.pdf (different)
4. ✅ Expected: "🔄 Updated - Processing completed!"
5. ChromaDB cleared and repopulated
```

### Test 4: Smart Retrieval
```
1. Upload & process: research.pdf
2. Type: "hi" → Generic response (no retrieval)
3. Type: "What does the paper discuss?" → Document retrieval activated
4. ✅ Expected: Different response modes, metrics shown only for #3
```

---

## 🔍 Debugging

### Check Document Hash
```python
# In Streamlit app
st.write(f"Current hash: {st.session_state.current_doc_hash}")
```

### Monitor Retrieval Mode
```python
# Check logs
logger.info("Question appears generic - light retrieval mode")
logger.info("Processing question with document retrieval")
logger.info("No documents in collection - responding without retrieval")
```

### Verify Cache Hit
```python
# In ingestion.py logs
"Documents unchanged - using cached embeddings"
"Document hash changed: abc123 -> xyz789"
```

---

## 🎓 Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│                 User Question                        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Check ChromaDB Count  │
         └───────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
  count == 0              count > 0
  Generic Chat           Analyze Question
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
            Generic Keywords      Document Keywords
            (≤3 words)            (research, paper, etc.)
                    │                     │
                    ▼                     ▼
            Light Mode           Full Retrieval
            Fast Response        ChromaDB Search
                                 Top-K Chunks
                                 LLM Synthesis
```

---

## 📝 Future Enhancements

1. **Semantic Similarity Threshold**: Measure question-document relevance score
2. **Multi-Collection Support**: Separate collections for different document sets
3. **TTL-Based Cache Expiry**: Auto-expire old embeddings after X days
4. **Vector Similarity Pre-Check**: Quick relevance check before full retrieval
5. **Hybrid Search**: Combine keyword + semantic search

---

## 🎉 Summary

DocSense is now **context-aware and cache-smart**:

- 🧠 **Intelligent**: Knows when to use documents vs. general chat
- ⚡ **Fast**: Caches processed files, skips redundant work
- 🎯 **Accurate**: Only retrieves when question is document-related
- 💬 **Conversational**: Natural responses for all query types
- 📊 **Transparent**: Shows retrieval metrics only when relevant

**Result**: A smarter, faster, more ChatGPT-like research assistant! 🚀
