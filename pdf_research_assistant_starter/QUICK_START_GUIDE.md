# DocSense 2.0 - Quick Reference Guide

## 🎯 Two Isolated Modes

### 🧠 **Chat Mode**
**What it is**: Pure conversational AI, like ChatGPT  
**What it does**: General questions, explanations, brainstorming  
**What it NEVER does**: Access uploaded documents  

**Usage**:
```
1. Select "🧠 Chat Mode" at the top
2. Ask anything: "Explain quantum computing"
3. Get adaptive responses (brief or detailed)
```

**Response Types**:
- **Brief** (800 tokens): Casual queries, simple questions
- **Detailed** (2500 tokens): "Explain", "analyze", "compare" questions

---

### 📚 **Document Mode**
**What it is**: Strict RAG research assistant  
**What it does**: Answers ONLY from your uploaded PDFs/TXT  
**What it NEVER does**: Use pretrained knowledge or add external facts  

**Usage**:
```
1. Select "📚 Document Mode" at the top
2. Upload PDF/TXT files in sidebar
3. Click "🚀 Process Documents"
4. Ask questions about your files
5. Get answers with [Source 1] citations
```

**Features**:
- **Similarity Filtering**: Minimum 0.3 relevance threshold
- **Rich Citations**: [Source 1], [Source 2] with chunk numbers
- **Refuses to Answer**: If no relevant information found
- **Smart Caching**: Same files = instant reload

---

## ⚙️ Settings

### **Response Style** (Both Modes)
- **Auto (Adaptive)**: System decides based on query complexity ✅ Recommended
- **Brief**: Short, concise answers (800-1500 tokens)
- **Detailed**: Comprehensive, structured responses (2500 tokens)

### **Show Source Citations** (Document Mode Only)
- Toggle to see expandable document chunks used for answers
- Shows: Source file, chunk number, relevance score

---

## 🎨 Visual Indicators

### **Mode Selection**
```
🧭 Select Mode:
( ) 🧠 Chat Mode
( ) 📚 Document Mode
```

### **Current Mode Display**

**Chat Mode**:
```
┌────────────────────────────────┐
│ 🧠 Chat Mode Active            │
│ General AI assistant - No      │
│ document retrieval             │
└────────────────────────────────┘
(Purple gradient)
```

**Document Mode**:
```
┌────────────────────────────────┐
│ 📚 Document Mode Active        │
│ Strict RAG - Answers only from │
│ your uploaded documents        │
└────────────────────────────────┘
(Pink/red gradient)
```

---

## 📊 Status Indicators

### **Chat Mode**
```
💬 Chat Mode | brief response
💬 Chat Mode | detailed response
```

### **Document Mode**
```
No Documents:
⚠️ No documents uploaded yet

With Documents:
📊 3 document(s) loaded | 47 chunks indexed

After Query:
📚 Document Mode | Retrieved 5 chunks | detailed response
```

---

## 🚀 Quick Start

### **Scenario 1: General Chat**
```
1. Start app (defaults to Chat Mode)
2. Type: "Explain machine learning"
3. Get detailed AI response
✅ No documents needed
```

### **Scenario 2: Research Q&A**
```
1. Switch to "📚 Document Mode"
2. Upload: research.pdf in sidebar
3. Click "🚀 Process Documents"
4. Type: "What are the main findings?"
5. Get answer with [Source 1], [Source 2] citations
✅ Strict document-only answers
```

### **Scenario 3: Cache Hit**
```
1. In Document Mode with files loaded
2. Upload SAME files again
3. System detects: "✅ Documents already processed!"
4. Instant load (~0.1s)
✅ 500x faster than reprocessing
```

---

## ⚡ Performance

### **Chat Mode**
| Query | Response Time |
|-------|---------------|
| "hello" | 5-10s |
| "Explain X" (brief) | 8-15s |
| "Analyze Y" (detailed) | 15-30s |

### **Document Mode**
| Action | Time |
|--------|------|
| Document upload + processing | 30-60s |
| Cache hit (same files) | 0.1s ✅ |
| Document retrieval | 0.3-0.5s |
| Answer generation | 10-40s |

---

## 🧪 Test Cases

### **Test 1: Chat Mode Isolation**
```
Input: "What is AI?"
Expected: General explanation, NO document access
Logs: No ChromaDB queries ✅
```

### **Test 2: Document Mode Strict RAG**
```
Input: Question about content NOT in docs
Expected: "❌ No relevant information found..."
Logs: Low similarity scores, refusal ✅
```

### **Test 3: Mode Switching**
```
Chat Mode: Ask 3 questions
Switch to Doc Mode: Ask 2 questions
Switch back to Chat: Still shows only original 3
Expected: Separate histories ✅
```

### **Test 4: Smart Caching**
```
Upload: paper.pdf
Process: 76 chunks created, hash stored
Re-upload: Same file
Expected: "✅ Documents already processed!" ✅
```

---

## 🎯 Best Practices

### **Use Chat Mode For:**
- ✅ Learning new concepts
- ✅ Brainstorming ideas
- ✅ General knowledge questions
- ✅ "Explain", "what is", "how does" questions
- ✅ Casual conversation

### **Use Document Mode For:**
- ✅ Analyzing uploaded research papers
- ✅ Extracting specific facts from PDFs
- ✅ Comparing information across documents
- ✅ Questions requiring exact citations
- ✅ When you need source transparency

### **Response Style Tips:**
- **Auto** (default): Let system adapt to query complexity
- **Brief**: When you want quick, concise answers
- **Detailed**: For comprehensive analysis and deep dives

---

## 🔧 Troubleshooting

### **Problem: "No relevant information found" in Document Mode**
**Cause**: Documents don't contain info about that topic  
**Solution**:
1. Upload more relevant documents
2. Rephrase question to match document content
3. Check what topics your docs actually cover

### **Problem: Response too long/short**
**Cause**: Auto-detection chose wrong level  
**Solution**: Manually set Response Style to "Brief" or "Detailed"

### **Problem: Chat Mode using old conversation context**
**Cause**: History persists across queries  
**Solution**: Click "🗑️ Clear Chat History" in sidebar

### **Problem: Document processing failed**
**Cause**: Unsupported file type or corrupted file  
**Solution**:
1. Ensure files are PDF or TXT format
2. Check file isn't password-protected
3. Try re-uploading

---

## 📚 Technical Details

### **Chat Mode**
```
File: chat_mode.py
Session State: st.session_state.chat_mode_history
Tokens: 800 (brief) | 2500 (detailed)
Temperature: 0.8 (brief) | 0.7 (detailed)
Features: Adaptive depth, no document access
```

### **Document Mode**
```
File: document_mode.py
Session State: st.session_state.doc_mode_history
RAG Settings:
  - TOP_K: 5 chunks
  - CHUNK_SIZE: 1500
  - CHUNK_OVERLAP: 200
  - SIMILARITY_THRESHOLD: 0.3
Tokens: 1500 (brief) | 2500 (detailed)
Temperature: 0.7
Features: Strict RAG, [Source X] citations, similarity filtering
```

---

## 🎉 Summary

**DocSense 2.0** provides two completely isolated AI modes:

1. **🧠 Chat Mode**: Free conversation, no documents
2. **📚 Document Mode**: Strict document-only research

**Key Features**:
- ✅ Adaptive response depth (auto-detect + manual control)
- ✅ Smart caching (500x faster re-uploads)
- ✅ Rich citations with source transparency
- ✅ Strict RAG (refuses when no relevant info)
- ✅ Separate histories (no cross-mode leakage)

**Running on**: http://localhost:8506

---

**Version**: 2.0  
**Status**: ✅ Production Ready  
**Last Updated**: October 23, 2025
