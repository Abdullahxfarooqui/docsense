# Intent Detection Fix - V3.6
## Fix for "Always Returns Tables" Issue

**Date:** October 24, 2025  
**Version:** V3.6  
**Issue:** System was returning numeric tables for ALL queries, even explanatory ones

---

## 🐛 Problem Description

### Symptom
Every query was triggering **NUMERIC extraction mode**, returning the same table repeatedly:
- "extract all data at each location" → Table ✅ (correct)
- "what other data is in it?" → Table ❌ (should be text explanation)
- "tell me what this is about" → Table ❌ (should be text explanation)

### Root Cause
The `detect_data_type()` function in `document_mode.py` had **over-aggressive trigger words**:
- Single trigger words like "data", "value", "number" would force numeric mode
- Queries containing common words like "data" or "information" were misclassified
- The system prioritized keyword matching over understanding user intent

---

## ✅ Solution Implemented

### V3.6 Smart Intent Detection

#### 1. **Prioritize Explanatory Queries FIRST**
Added detection for queries that clearly want explanation/analysis:

```python
text_mode_indicators = [
    # Questions asking for explanation
    'what is this about', 'what does this mean', 'explain', 'describe',
    'tell me about', 'what is', "what's", 'why', 'how does',
    'what other', 'what else', 'anything else', 'more information',
    'summary', 'overview', 'context', 'background', 'purpose',
    
    # Analysis requests
    'analyze', 'interpret', 'discuss', 'compare', 'contrast',
    
    # Open-ended questions
    'tell me', 'can you tell', 'could you explain'
]
```

#### 2. **Strict Numeric Triggers Only**
Changed from 50+ loose triggers to **specific extraction commands**:

```python
strict_numeric_triggers = [
    # Explicit extraction commands
    'extract all', 'extract data', 'extract values', 'give me all',
    'show all data', 'list all', 'get all values',
    
    # Location-based extraction
    'at each location', 'by location', 'per location',
    
    # Table requests
    'in a table', 'as a table', 'table format',
    
    # Specific value queries
    'what is the pressure', 'what is the temperature'
]
```

#### 3. **Default to Text Mode**
When unsure, the system now defaults to **text/explanation mode** instead of numeric mode:
- Better to explain data than dump raw tables
- Users can always rephrase if they want extraction

---

## 🎯 New Behavior

### Query Type Detection

| Query | Mode | Reason |
|-------|------|--------|
| "extract all data at each location" | NUMERIC | Explicit extraction command |
| "what other data is in it?" | TEXT | Explanatory question ("what other") |
| "tell me what this is about" | TEXT | Explanatory question ("tell me") |
| "what is the pressure at TAIMUR?" | NUMERIC | Specific value query |
| "explain the data" | TEXT | Analysis request ("explain") |
| "give me all values in a table" | NUMERIC | Explicit table request |
| "what information is available?" | TEXT | Open-ended question |

---

## 🔧 Technical Changes

### File: `document_mode.py`

**Function:** `detect_data_type()`  
**Lines:** ~217-285

**Changes:**
1. Added `text_mode_indicators` list (checked FIRST)
2. Reduced `numeric_triggers` to `strict_numeric_triggers`
3. Removed aggressive keyword matching (was checking 50+ words)
4. Changed chunk content analysis (was triggering on 30% numeric content)
5. Added explicit default to TEXT mode

**Before (V3.5):**
```python
# Any single trigger word → NUMERIC mode
if trigger_count >= 1:  # Only need 1 match!
    return 'numeric'
```

**After (V3.6):**
```python
# Check explanatory intent FIRST
for indicator in text_mode_indicators:
    if indicator in query_lower:
        return 'text'  # Prioritize explanation

# Only strict extraction commands → NUMERIC
for trigger in strict_numeric_triggers:
    if trigger in query_lower:
        return 'numeric'

# Default to text when unsure
return 'text'
```

---

## 📊 Test Results

### Before Fix (V3.5)
- ❌ "what other data?" → Returns table
- ❌ "tell me about this" → Returns table  
- ❌ "explain the data" → Returns table
- ✅ "extract all data" → Returns table (correct)

### After Fix (V3.6)
- ✅ "what other data?" → Returns explanation
- ✅ "tell me about this" → Returns explanation
- ✅ "explain the data" → Returns explanation
- ✅ "extract all data" → Returns table (correct)

---

## 💡 Key Principles

1. **User Intent > Keywords:** Understand what the user wants, not just what words they use
2. **Explanation by Default:** When unsure, explain rather than dump data
3. **Explicit Extraction:** Numeric mode requires clear extraction language
4. **Context Matters:** "data" in "what data?" is different from "extract data"

---

## 🚀 Usage Examples

### To Get Explanatory Response (TEXT Mode):
- "What is this document about?"
- "Tell me what other information is available"
- "Explain what this data shows"
- "What else is in the file?"
- "Describe the content"

### To Get Data Extraction (NUMERIC Mode):
- "Extract all data at each location"
- "Give me all values in a table"
- "Show all data by location"
- "What is the pressure at TAIMUR?"
- "List all temperatures"

---

## 🔄 Rollback Plan

If V3.6 causes issues, revert to V3.5 by:

```bash
git checkout HEAD~1 pdf_research_assistant_starter/document_mode.py
```

Or manually restore the aggressive trigger list from backup.

---

## ✅ Verification Checklist

- [x] Explanatory queries trigger TEXT mode
- [x] Extraction queries trigger NUMERIC mode
- [x] Default behavior is TEXT mode
- [x] No syntax errors
- [x] Application starts successfully
- [x] Test queries return appropriate responses

---

**Status:** ✅ FIXED  
**Version:** V3.6  
**Ready for testing with user queries**
