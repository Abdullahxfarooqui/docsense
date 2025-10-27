# 🎯 DocSense V3.5 Quick Reference Card

**Version:** 3.5 - Enhanced Numeric Extraction (Strict No-Prose Mode)  
**Last Updated:** October 24, 2025

---

## 🚀 THREE MODES (AUTO-DETECTED)

| Mode | When? | Output |
|------|-------|--------|
| 📊 **NUMERIC** | Keywords: extract, pressure, psi, bbl, °F, table, excel, at each | **ONLY** Table/JSON — NO PROSE |
| 📄 **TEXT** | Narrative queries: explain, analyze, summarize, discuss | Structured paragraphs with citations |
| 💬 **CHAT** | Casual: hi, thanks, ok | "Switch to Chat Mode" message |

---

## 📊 NUMERIC EXTRACTION MODE (V3.5)

### ✅ USE WHEN:
- Extracting measurements (pressure, temperature, volume)
- Working with Excel/CSV files
- Need tables or JSON output
- Query contains units (psi, bbl, °F, MMBtu)
- Query says "at each location", "by well", "list all values"

### 🎯 MAGIC KEYWORDS (30+ triggers):
```
extract | value | number | list | show | find | get
pressure | temperature | rate | flow | volume | depth | production
psi | psig | bbl | °F | °C | MMBtu | ft | gal | m³
table | excel | csv | spreadsheet
at each | by location | by well | all values
```

### ✅ OUTPUT FORMAT (STRICT):
```markdown
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| Well-7  | Pressure  | 3124  | psi  | Explicit |
| Well-12 | Pressure  | 2847  | psi  | Inferred from context |
| Well-4  | Pressure  | null  | psi  | Not found |

Average: 2986 psi (from 2 wells with data)
```

### 🚫 FORBIDDEN (V3.5):
- ❌ NO "Introduction" or "Summary" sections
- ❌ NO prose before/after table (except ONE calculation line)
- ❌ NO invented data (Temperature = 0 when not stated)
- ❌ NO "Based on the document..." or "Here is the data..."

### 📝 EXAMPLE QUERIES:
```
✅ "Extract pressure values at each location"
✅ "List temperature readings from the spreadsheet"  
✅ "Find all production data in bbl"
✅ "Show numeric values for Well-7"
✅ "Get pressure, temperature, and volume for all wells"
```

---

## 📄 TEXT ANALYSIS MODE

### ✅ USE WHEN:
- Analyzing PDF reports
- Summarizing research papers
- Explaining concepts
- No numeric extraction needed

### 🎯 MAGIC KEYWORDS:
```
explain | analyze | discuss | summarize | describe
compare | contrast | evaluate | implications
why | how | what are | tell me about
```

### ✅ OUTPUT FORMAT:
```markdown
**Introduction**
Brief context and scope

**Key Insights**
Evidence with [Source 1], [Source 2] citations

**Analysis**
Deep interpretation and relationships

**Conclusion**
Synthesized insights
```

### 📝 EXAMPLE QUERIES:
```
✅ "Explain the methodology used in the research"
✅ "Summarize key findings from the report"
✅ "What are the implications of climate change?"
✅ "Compare the two approaches discussed"
```

---

## 💬 CHAT MODE

### ✅ USE WHEN:
- Saying hi/thanks/bye
- Casual conversation

### OUTPUT:
```
"You're in Document Mode — ask about your files or switch to Chat Mode"
```

---

## 🔧 QUICK SETTINGS

### Detail Level (Sidebar):
- **Brief:** 2-3 paragraphs (text mode only)
- **Detailed:** Full research-grade analysis (1200+ words)

### Source Citations (Sidebar):
- **ON:** Show document chunks used
- **OFF:** Hide sources

---

## 📂 FILE SUPPORT

| Format | Mode | Notes |
|--------|------|-------|
| **Excel (.xlsx)** | 📊 Numeric | Auto-detected for extraction |
| **CSV (.csv)** | 📊 Numeric | Auto-detected for extraction |
| **PDF (.pdf)** | 📄 Text | Narrative analysis |
| **TXT (.txt)** | 📄 Text | Narrative analysis |

**Limits:**
- Max 5 files
- Max 50MB total
- Auto-processes on upload ✨

---

## 🎯 V3.5 CHEAT SHEET

### Want ONLY a table with numbers?
**Use these words:**
```
extract | list | show | find | at each | by location
pressure | temperature | psi | bbl | °F | table | excel
```

### Want analytical paragraphs?
**Use these words:**
```
explain | analyze | discuss | summarize | why | how
implications | compare | describe | evaluate
```

### Getting prose when you want tables?
**Add these to your query:**
```
"Extract values ONLY as table"
"Return JSON format"
"List numeric data"
"At each location"
```

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| **Numeric mode returns text** | Add "extract", "psi", "at each location" to query |
| **Missing data shows as 0** | V3.5 now shows `Value: null` correctly |
| **Too much prose in table** | V3.5 validation blocks this - refresh if old cache |
| **Text mode too short** | Switch to "Detailed" in sidebar |

---

## 📊 V3.5 WHAT'S NEW?

✅ **Stricter Numeric Mode**
- NO prose allowed before tables
- Validation blocks introductions/summaries
- Only ONE calculation line permitted

✅ **Better Detection**
- 30+ trigger keywords (was 15)
- Single trigger activates mode (was multiple)
- 30% chunk threshold (was 40%)

✅ **Smarter Inference**
- Extracts "Well #7: 3124" as Pressure: 3124 psi
- Uses context to determine units
- Never fabricates missing data

✅ **Enhanced Units**
- psi, psig, bbl, barrels, °F, °C, MMBtu, ft, gal, m³, kg, lb, bar, Pa, kPa, ft³, mcf

---

## 💡 PRO TIPS

1. **Be explicit with numeric queries:**
   - ✅ "Extract pressure at each well"
   - ❌ "Tell me about the wells"

2. **Use detail level wisely:**
   - Brief: Quick answers (400+ words)
   - Detailed: Deep research (1200+ words)

3. **Check source citations:**
   - Enable in sidebar to see exact document chunks

4. **Multi-file uploads:**
   - System auto-processes — no button needed!

---

## 🎨 OUTPUT EXAMPLES

### Numeric Mode (V3.5 Compliant):
```
| Source  | Parameter   | Value | Unit | Notes                 |
|---------|-------------|-------|------|-----------------------|
| North-7 | Pressure    | 3124  | psi  | Explicit              |
| North-12| Pressure    | 2847  | psi  | Inferred from context |
| South-4 | Temperature | 301.9 | °F   | Explicit              |

Average Pressure: 2986 psi
```

### Text Mode (Brief):
```
**Overview**
The research demonstrates a 34% increase in efficiency through targeted interventions [Source 1].

**Key Findings**
Data analysis reveals significant correlations between education levels and outcomes, 
supported by 500+ participant surveys across three regions [Source 2].

**Implications**
These results suggest that resource allocation toward educational programs yields 
measurable improvements, aligning with prior studies [Source 3].
```

---

**🎉 You're all set! Upload documents and start querying.**

**Need help?** Check `MODE_DETECTION_GUIDE_V3.5.md` for full details.
