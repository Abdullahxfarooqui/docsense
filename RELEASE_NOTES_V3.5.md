# 🎉 DocSense V3.5 Released!

**Release Date:** October 24, 2025  
**Version:** 3.5 - Enhanced Numeric Extraction Mode

---

## 🚀 What's New?

### **MAJOR UPGRADE: Strict Numeric Extraction Mode**

DocSense now intelligently detects when you want **numeric data extraction** and returns **ONLY tables or JSON** — absolutely **NO narrative text or summaries**.

---

## ✨ Key Improvements

### 1️⃣ **Smarter Detection (30+ Trigger Keywords)**

The system now recognizes **30+ keywords and patterns** that indicate you want numeric extraction:

**Examples that trigger Numeric Mode:**
```
✅ "Extract pressure values at each location"
✅ "List temperature readings from the spreadsheet"
✅ "Find all production data in bbl"
✅ "Show values for Well-7"
✅ "Get pressure and temperature by location"
```

**Magic Keywords:**
- **Extraction:** extract, list, show, find, get, value, number
- **Parameters:** pressure, temperature, flow, volume, depth, production
- **Units:** psi, psig, bbl, °F, °C, MMBtu, ft, gal, m³
- **Locations:** at each, by location, by well, per site
- **Data:** table, excel, csv, spreadsheet

### 2️⃣ **Zero-Prose Output (V3.5 Strict Mode)**

When numeric mode is triggered, you get **ONLY the data**:

**❌ OLD BEHAVIOR (V3.0):**
```
Based on the provided document, here are the pressure values:

**Introduction**
The following table presents...

| Source | Parameter | Value | Unit |
|---------|-----------|-------|------|
| Well-7  | Pressure  | 3124  | psi  |

**Key Insights**
The data shows that Well-7 has the highest pressure...
```

**✅ NEW BEHAVIOR (V3.5):**
```
| Source | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| Well-7  | Pressure  | 3124  | psi  | Explicit |
| Well-12 | Pressure  | 2847  | psi  | Inferred from context |
| Well-4  | Pressure  | 2661  | psi  | Explicit |

Average: 2877 psi (from 3 wells)
```

**That's it.** No fluff, no essays — just your data.

### 3️⃣ **Contextual Inference**

V3.5 is smarter about extracting values even when they're not perfectly labeled:

```
Source Text: "Well #7 shows 3124 psig in the north sector"
→ Extracted as: Pressure: 3124 psi (Inferred from context)

Source Text: "Temperature reading: 301.9 degrees Fahrenheit"
→ Extracted as: Temperature: 301.9°F (Explicit)

Source Text: "Site A reported 2847" (in pressure section)
→ Extracted as: Pressure: 2847 psi (Inferred from context)
```

### 4️⃣ **No More Fake Data**

**V3.0 Problem:**
```
| Location | Temperature | Pressure |
|----------|-------------|----------|
| Well-7   | 0           | 3124     |  ← Fabricated!
```

**V3.5 Solution:**
```
| Location | Temperature | Pressure |
|----------|-------------|----------|
| Well-7   | null        | 3124     |

Note: Temperature not found in source
```

If data doesn't exist, V3.5 shows `null` or "Not found" — **never invents placeholder values**.

### 5️⃣ **Enhanced Unit Support**

Now recognizes **all common units** in engineering, oil/gas, and scientific contexts:

✅ **Pressure:** psi, psig, bar, Pa, kPa  
✅ **Temperature:** °F, °C, K  
✅ **Volume:** bbl, barrels, m³, gal, ft³  
✅ **Gas:** MMBtu, mcf, scf  
✅ **Distance:** ft, m, km, mi  
✅ **Mass:** kg, lb, ton  

---

## 🎯 Three Modes Explained

DocSense automatically detects which mode you need:

### 📊 **Numeric Extraction Mode** (NEW in V3.5)
**When:** You ask for measurements, data, values  
**Output:** Pure tables/JSON — no prose  
**Triggers:** extract, pressure, temperature, psi, bbl, at each location

### 📄 **Text Analysis Mode**
**When:** You ask for explanations, summaries, analysis  
**Output:** Structured paragraphs with citations [Source 1]  
**Triggers:** explain, analyze, discuss, summarize, why, how

### 💬 **Chat Mode**
**When:** Casual greetings (hi, thanks, ok)  
**Output:** "Switch to Chat Mode" message  
**Purpose:** Guides you to the right mode

---

## 📝 Quick Start Examples

### Want Data Extraction?
```
"Extract pressure at each well"
"List all temperature readings"
"Show production data in bbl"
"Get numeric values from Sheet1"
"Find pressure and temperature by location"
```

### Want Analysis?
```
"Explain the research methodology"
"Summarize key findings"
"What are the implications of these results?"
"Compare the two approaches"
"Analyze the data trends"
```

---

## 🔧 Settings

Access via **sidebar**:

### **Detail Level** (Text Mode Only)
- **Brief:** 2-3 focused paragraphs
- **Detailed:** Full research-grade analysis (1200+ words)

*Note: Numeric mode ignores this setting — always outputs minimal tables*

### **Source Citations**
- **ON:** Show document chunks used
- **OFF:** Hide sources (cleaner output)

---

## 📂 File Support

| File Type | Mode | Notes |
|-----------|------|-------|
| Excel (.xlsx) | 📊 Numeric | Auto-detects for extraction |
| CSV (.csv) | 📊 Numeric | Auto-detects for extraction |
| PDF (.pdf) | 📄 Text | Narrative analysis |
| TXT (.txt) | 📄 Text | Narrative analysis |

**Limits:**
- Max 5 files per session
- Max 50MB total size
- **Auto-processing** on upload ✨

---

## 🐛 Troubleshooting

### "I want a table but got paragraphs"
**Solution:** Add these keywords to your query:
- "extract"
- "list"
- "at each location"
- "show values"
- Units like "psi", "bbl", "°F"

### "I see 'Value: null' for data I know exists"
**Possible causes:**
- Data might be in a different format than expected
- Document might have OCR errors (scanned PDFs)
- Try rephrasing: "Extract pressure for Well-7" instead of "Tell me about Well-7"

### "Response is too short"
**Solution:** Switch sidebar setting to "Detailed" mode

---

## 📚 Documentation

**Full Guide:** `MODE_DETECTION_GUIDE_V3.5.md`  
**Quick Reference:** `QUICK_REFERENCE_V3.5.md`  
**Implementation Details:** `V3.5_IMPLEMENTATION_SUMMARY.md`

---

## 🎉 Try It Now!

1. **Upload an Excel/CSV file** with numeric data
2. **Ask:** "Extract pressure values at each location"
3. **Get:** A clean table with all values — no fluff!

---

## 💡 Pro Tips

1. **Be specific:** "Extract pressure" > "Tell me about the data"
2. **Use units:** "Find values in psi" helps trigger numeric mode
3. **Location-based:** "At each well" or "By location" strongly triggers extraction
4. **Check citations:** Enable in sidebar to see exactly what was used

---

## 🔗 Need Help?

- Check the **Quick Reference** for common queries
- Review **Mode Detection Guide** for advanced usage
- Enable **Source Citations** to debug extraction issues

---

**Happy querying! 🚀**

*DocSense V3.5 — Three modes, one intelligent assistant*
