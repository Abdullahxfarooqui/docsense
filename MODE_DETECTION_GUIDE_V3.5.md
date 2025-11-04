# 🎯 DocSense V3.5: Three-Mode Analytical Document Intelligence

**Last Updated:** October 24, 2025  
**Version:** 3.5 - Enhanced Numeric Extraction with Strict No-Prose Mode

---

## 📋 OVERVIEW

DocSense operates in **THREE STRICT MODES** with automatic detection:

| Mode | Icon | Trigger | Output Format | Use Case |
|------|------|---------|---------------|----------|
| **Textual Analysis** | 📄 | Narrative/qualitative queries | Structured paragraphs with citations | PDF reports, research papers, articles |
| **Numeric Extraction** | 📊 | Numeric/tabular keywords | **ONLY** tables/JSON — NO PROSE | Excel, CSV, tables, measurements |
| **Chat** | 💬 | Casual phrases (hi, thanks) | Mode switching message | Conversational guidance |

---

## 1️⃣ TEXTUAL ANALYSIS MODE 📄

### **Triggers:**
- Narrative questions without numeric indicators
- Queries asking for analysis, discussion, explanation
- Document content is primarily text-based

### **Output Format:**
```markdown
**Introduction** (2-3 sentences)
Context and scope setup

**Key Insights & Findings** (detailed evidence)
Main points with [Source 1], [Source 2] citations

**Analytical Discussion** (deep interpretation)
Relationships, patterns, implications

**Conclusion** (synthesized insights)
Actionable takeaways
```

### **Response Depths:**
- **Brief Mode:** 2-3 focused paragraphs (600-800 tokens, ≥400 words)
- **Detailed Mode:** Research-grade analysis (2000-3500 tokens, ≥1200 words)

### **Example Query:**
```
"Explain the methodology used in the research paper"
"What are the implications of climate change mentioned?"
"Summarize the key findings from the report"
```

### **Example Output:**
```
**Introduction**
The research paper employs a mixed-methods approach combining quantitative surveys with qualitative interviews [Source 1].

**Key Insights & Findings**
The study surveyed 500 participants across three regions, finding a 34% increase in awareness levels [Source 1]. Interview data revealed that educational interventions were the primary driver [Source 2]...

**Analytical Discussion**
The correlation between education and awareness suggests that targeted programs could yield significant improvements. The 34% increase aligns with previous studies showing similar trends [Source 3]...

**Conclusion**
The findings support implementing educational programs as a cost-effective strategy, with measurable impact demonstrated across diverse populations.
```

---

## 2️⃣ NUMERIC EXTRACTION MODE 📊 (V3.5 ENHANCED)

### **🚨 V3.5 CRITICAL CHANGE: STRICT NO-PROSE MODE**

**New Behavior:**
- **ZERO narrative text** allowed before or after tables
- **NO introductions, summaries, conclusions, or insights paragraphs**
- **NO fabricated/dummy data** (e.g., Temperature = 0 when not in source)
- Output **ONLY**: Markdown table or JSON + optional ONE calculation line

### **Aggressive Triggers (30+ keywords):**

| Category | Keywords |
|----------|----------|
| **Extraction** | extract, value, number, data, list, show, give me, find, get |
| **Parameters** | pressure, temperature, rate, flow, volume, depth, production, yield, capacity, efficiency |
| **Units** | psi, psig, bbl, barrels, °F, °C, MMBtu, ft, gal, m³, kg, lb, bar, Pa, kPa, ft³, mcf |
| **Data Formats** | table, spreadsheet, excel, csv, worksheet, sheet |
| **Quantitative** | how much, how many, quantity, amount, count, metric, measurement, statistics, calculation |
| **Location-based** | at each, by location, by well, by site, per location, each location, all locations |
| **Aggregation** | breakdown, summary, all values, all data, all numbers |
| **Industry** | oil, gas, well, reservoir, field, readings |

### **Output Format (MANDATORY):**

**Markdown Table (default):**
```markdown
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| Well-7  | Pressure  | 3124  | psi  | Explicit |
| Well-12 | Pressure  | 2847  | psi  | Inferred from context |
| Well-4  | Pressure  | 2661  | psi  | Explicit |
| Well-19 | Pressure  | null  | psi  | Not found |

Average: 2877 psi (from 3 wells with data)
```

**JSON (if requested):**
```json
[
  {"Source": "Well-7", "Parameter": "Pressure", "Value": 3124, "Unit": "psi", "Notes": "Explicit"},
  {"Source": "Well-12", "Parameter": "Pressure", "Value": 2847, "Unit": "psi", "Notes": "Inferred from context"},
  {"Source": "Well-4", "Parameter": "Pressure", "Value": 2661, "Unit": "psi", "Notes": "Explicit"},
  {"Source": "Well-19", "Parameter": "Pressure", "Value": null, "Unit": "psi", "Notes": "Not found"}
]
```

### **Extraction Protocol:**

#### **1. Explicit Values (Highest Priority):**
```
Source Text: "Pressure: 327.07 psi"
→ Parameter: Pressure, Value: 327.07, Unit: psi, Notes: Explicit

Source Text: "Temperature = 301.9°F"
→ Parameter: Temperature, Value: 301.9, Unit: °F, Notes: Explicit
```

#### **2. Inferred Values (Contextual):**
```
Source Text: "Well #7 shows 3124 psig"
→ Parameter: Pressure, Value: 3124, Unit: psi, Notes: Inferred from context

Source Text: "North sector: 2847" (in pressure section)
→ Parameter: Pressure, Value: 2847, Unit: psi, Notes: Inferred from context

Source Text: "301.9 degrees F recorded at Site A"
→ Parameter: Temperature, Value: 301.9, Unit: °F, Notes: Inferred from context
```

#### **3. Missing Data Handling:**
```
True missing → Value: null, Notes: "Not found"
Units unclear → Unit: "Unknown unit"
Parameter unclear → Parameter: "Unspecified", Notes: "Requires clarification"
⚠️ NEVER invent placeholder values like 0 unless explicitly stated
```

#### **4. Contextual Clues for Inference:**
- Section headers: "Pressure Data", "Temperature Readings"
- Column names: "Well ID", "Pressure (psi)", "Temp (°F)"
- Proximity to units: "3124 psig", "301.9 degrees F"
- Location names: "North-7", "Well #12", "Site A"

### **🚫 FORBIDDEN in V3.5 (STRICT ENFORCEMENT):**

❌ **WRONG OUTPUT:**
```
Based on the provided context, here are the pressure values extracted from the document:

**Introduction**
The following table presents pressure measurements across multiple wells...

| Source | Parameter | Value | Unit |
|---------|-----------|-------|------|
| Well-7  | Pressure  | 3124  | psi  |

**Key Insights**
The data shows significant variation across locations, with Well-7 demonstrating the highest pressure reading...

**Conclusion**
In summary, the pressure distribution indicates optimal performance in the northern sector.
```

✅ **CORRECT OUTPUT:**
```
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| Well-7  | Pressure  | 3124  | psi  | Explicit |
| Well-12 | Pressure  | 2847  | psi  | Inferred from context |
| Well-4  | Pressure  | 2661  | psi  | Explicit |

Average: 2877 psi (from 3 wells)
```

### **Example Queries:**
```
✅ "Extract pressure values at each location"
✅ "List temperature readings from the spreadsheet"
✅ "Find all production data in bbl"
✅ "Show pressure, temperature, and volume for Well-7"
✅ "What are the numeric values at each site?"
```

### **Example Output (V3.5 Compliant):**
```
| Source    | Parameter   | Value  | Unit  | Notes                   |
|-----------|-------------|--------|-------|-------------------------|
| North-7   | Pressure    | 3124   | psi   | Explicit                |
| North-12  | Pressure    | 2847   | psi   | Inferred from context   |
| South-4   | Pressure    | 2661   | psi   | Explicit                |
| North-7   | Temperature | 301.9  | °F    | Explicit                |
| North-12  | Temperature | 298.5  | °F    | Inferred from context   |
| South-4   | Temperature | null   | °F    | Not found               |
| North-7   | Volume      | 1250   | bbl   | Explicit                |
| North-12  | Volume      | 1180   | bbl   | Explicit                |

Average Pressure: 2877 psi (from 3 wells)
Average Temperature: 300.2°F (from 2 wells)
Total Volume: 2430 bbl
```

---

## 3️⃣ CHAT MODE 💬

### **Triggers:**
- Casual phrases: hi, hello, thanks, ok, bye
- Very short inputs (≤4 words) without analytical keywords

### **Output:**
```
Hey 👋 You're in **Document Mode** — ask a question about your uploaded files, 
or switch to Chat Mode for general queries.
```

### **Purpose:**
- Prevents unnecessary document retrieval for greetings
- Guides users to appropriate mode

---

## ⚙️ MODE DETECTION ALGORITHM

### **Detection Flow:**
```python
def detect_mode(query, chunks):
    # Step 1: Check casual intent
    if is_casual(query):  # "hi", "thanks", etc.
        return "chat"
    
    # Step 2: Check numeric triggers (V3.5 enhanced)
    numeric_triggers = [
        'extract', 'value', 'pressure', 'temperature', 'psi', 'bbl', '°f',
        'table', 'excel', 'csv', 'at each', 'by location', # 30+ total
    ]
    
    trigger_count = count_triggers(query, numeric_triggers)
    if trigger_count >= 1:
        return "numeric"  # V3.5: Single trigger is enough
    
    # Step 3: Check chunk content (30% threshold in V3.5)
    if numeric_pattern_in_chunks(chunks) >= 0.30:
        return "numeric"
    
    # Step 4: Default to textual analysis
    return "text"
```

### **V3.5 Changes:**
- **Lowered threshold** for numeric mode: 30% chunks (was 40%)
- **Single trigger** now activates numeric mode (was multiple)
- **Expanded trigger list** from 15 to 30+ keywords
- **Enhanced unit detection** (psi, psig, mcf, ft³, etc.)

---

## 🧪 VALIDATION RULES

### **Numeric Mode Validation (V3.5):**
```python
def validate_numeric_response(response):
    # Must have table or JSON
    has_table = '|' in response and 'Parameter' in response
    has_json = '{' in response and '"Source"' in response
    
    if not (has_table or has_json):
        return False, "Missing table/JSON format"
    
    # Check for forbidden prose BEFORE table
    forbidden = ['based on the', 'introduction', 'key insights', 
                 'findings', 'conclusion', 'as we can see']
    
    table_start = response.find('|')
    before_table = response[:table_start].lower()
    
    if len(before_table.strip()) > 20:  # Too much text before table
        return False, "Prose detected before table"
    
    for phrase in forbidden:
        if phrase in before_table:
            return False, f"Forbidden phrase: {phrase}"
    
    return True, "V3.5 compliant"
```

### **Text Mode Validation:**
```python
def validate_text_response(response, detail_level):
    word_count = len(response.split())
    
    if detail_level == 'detailed':
        if word_count < 1200:
            return False, f"Too short: {word_count} words (need 1200+)"
        
        headings = response.count('**') // 2
        if headings < 3:
            return False, "Needs more structure (3+ sections)"
    
    elif detail_level == 'brief':
        if word_count < 400:
            return False, f"Too short: {word_count} words (need 400+)"
    
    return True, "Valid"
```

---

## 🔧 INTEGRATION TIP (Python/Node)

### **Python Example:**
```python
def build_prompt(query, data_type):
    if any(kw in query.lower() for kw in ["pressure", "temperature", "volume", 
                                            ".xlsx", ".csv", "table", "extract"]):
        data_type = "numeric"
        user_prompt = (
            "V3.5 STRICT: Extract numeric values and parameters. "
            "Return ONLY as Markdown table or JSON — NO PROSE. "
            "Include explicit + inferred values with units. "
            "Handle missing data as Value: null."
        )
    else:
        data_type = "text"
        user_prompt = (
            "Provide structured analysis with citations [Source X]. "
            "Use paragraphs with Introduction, Findings, Analysis, Conclusion."
        )
    
    return user_prompt
```

### **Node.js Example:**
```javascript
function detectMode(query) {
    const numericKeywords = [
        'pressure', 'temperature', 'psi', 'bbl', 'extract', 
        'table', 'excel', 'csv', 'at each', 'by location'
    ];
    
    const lowerQuery = query.toLowerCase();
    const isNumeric = numericKeywords.some(kw => lowerQuery.includes(kw));
    
    if (isNumeric) {
        return {
            mode: 'numeric',
            prompt: 'V3.5 STRICT: Return ONLY table/JSON with numeric data. NO PROSE.'
        };
    } else {
        return {
            mode: 'text',
            prompt: 'Provide analytical response with structured paragraphs and citations.'
        };
    }
}
```

---

## 📊 V3.5 IMPROVEMENTS SUMMARY

| Feature | V3.0 | V3.5 |
|---------|------|------|
| **Numeric trigger threshold** | 40% chunks | 30% chunks (more sensitive) |
| **Trigger keywords** | 15 keywords | 30+ keywords (expanded) |
| **Single trigger activation** | Multiple required | Single trigger enough |
| **Unit detection** | Basic (psi, °F) | Extended (psig, mcf, ft³, etc.) |
| **Prose validation** | Basic table check | **STRICT - no prose before table** |
| **Dummy data prevention** | Warning | **HARD BLOCK - validation fails** |
| **Contextual inference** | Limited | **Enhanced - uses surrounding text** |
| **Missing data handling** | Generic "Missing" | **Structured: Value: null, Notes: "Not found"** |

---

## ✅ TESTING CHECKLIST

### **Numeric Mode Tests:**
- [ ] Query with "extract pressure" → Returns ONLY table
- [ ] No "Introduction" or "Summary" headers
- [ ] No prose before table (max 20 chars allowed)
- [ ] Missing data shown as `Value: null`
- [ ] Inferred values marked in Notes column
- [ ] Units always included
- [ ] Optional calculation line (if requested)
- [ ] Validation passes (no forbidden phrases)

### **Text Mode Tests:**
- [ ] Narrative query → Structured paragraphs
- [ ] Detailed mode → ≥1200 words
- [ ] Brief mode → ≥400 words
- [ ] Citations present [Source 1], [Source 2]
- [ ] No hallucination (only document content)

### **Chat Mode Tests:**
- [ ] "hi" → Mode switching message
- [ ] "thanks" → Mode switching message
- [ ] No document retrieval triggered

---

## 🎯 BEST PRACTICES

### **For Developers:**
1. **Always auto-detect mode** — don't ask users to specify
2. **Lock output format** once mode is detected
3. **Log mode detection** for debugging (`logger.info("Mode: numeric")`)
4. **Validate responses** against mode rules before returning
5. **Cache embeddings** to avoid re-processing same files

### **For Users:**
1. **Use specific keywords** for numeric extraction:
   - "Extract", "List", "Find values", "At each location"
2. **Ask narrative questions** for textual analysis:
   - "Explain", "Analyze", "Discuss", "Summarize"
3. **Upload correct file types**:
   - Numeric mode: Excel (.xlsx), CSV (.csv)
   - Text mode: PDF (.pdf), Word (.docx), TXT (.txt)
4. **Set detail level** before querying (Brief vs Detailed)

---

## 🐛 TROUBLESHOOTING

### **Problem: Numeric mode returns prose**
**Solution:**
- Check validation function is called
- Ensure system prompt includes V3.5 strict rules
- Verify forbidden phrases list is complete
- Log response before validation

### **Problem: Text mode triggers instead of numeric**
**Solution:**
- Add more numeric triggers to query ("extract", "pressure", "psi")
- Check chunk content has numbers (use regex validation)
- Lower detection threshold to 25% if needed
- Verify trigger list includes domain-specific terms

### **Problem: Missing data shown as 0 instead of null**
**Solution:**
- Update prompt to explicitly forbid dummy values
- Add validation rule: `if Value == 0 and not explicitly_stated: reject`
- Use "Value: null" or "Value: N/A" in training examples

---

## 📝 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| **3.5** | Oct 24, 2025 | STRICT no-prose mode, 30+ triggers, contextual inference, dummy data prevention |
| **3.0** | Oct 15, 2025 | Initial numeric extraction mode, basic table output |
| **2.0** | Oct 1, 2025 | Text analysis mode with citations |
| **1.0** | Sep 15, 2025 | Basic RAG implementation |

---

**End of V3.5 Configuration Guide** 🎉
