# 🎯 Entity-Based Extraction V3.7 - Complete Guide

## 📌 What Changed

**Version 3.7** introduces **intelligent entity-based extraction** that automatically:
- Detects named entities (TAIMUR, LPG, CONDEN, OIL, etc.) across all document chunks
- Merges data for the same entity from multiple files/sheets/locations
- Groups parameters by entity (Pressure, Temperature, Volume, etc.)
- Auto-detects units (psig, degF, bbl, dAPI, MMBtu, mcf, ft, gal)
- Outputs unified tables with no duplicate entity rows

---

## 🚀 Quick Start

### For Users:

1. **Upload your documents** (PDF, Excel, CSV - single or multiple files)

2. **Query with numeric extraction triggers:**
   - "Extract all data at each location"
   - "Show all parameters for each entity"
   - "Get all measurements in a table"

3. **System automatically:**
   - Detects entities (TAIMUR, LPG, CONDEN, OIL, Tank-C, Well-7, etc.)
   - Extracts 11 parameter types (Pressure, Temperature, Volume, API Gravity, Energy, Ticket, Sales, Product, Status, Storage, Delivery)
   - Identifies 9 unit types (psig, degF, bbl, dAPI, MMBtu, %, mcf, ft, gal)
   - Merges duplicate entities across all chunks/files
   - Returns unified Markdown table

4. **Example output:**
```markdown
| Entity | Pressure | Unit | Temperature | Unit | Volume | Unit | Product | Notes |
|--------|----------|------|-------------|------|--------|------|---------|-------|
| TAIMUR | 327.07 | psig | 301.9 | degF | 1250.5 | bbl | LPG | Explicit |
| LPG | 3124 | psig | NULL | degF | 845.2 | bbl | LPG | Inferred from context |
| CONDEN | 2847 | psig | 285.3 | degF | NULL | bbl | CONDEN | Explicit |
```

---

## 🔧 Technical Implementation

### Architecture:

```
User Query → Intent Detection (V3.6) → Numeric Mode
                     ↓
         Entity Extraction (V3.7)
                     ↓
    EntityExtractor.extract_from_text(all_chunks)
                     ↓
         Auto-merge entities by name
                     ↓
      EntityExtractor.format_as_markdown()
                     ↓
      Replace chunks with unified table
                     ↓
           LLM receives entity table
                     ↓
           Output to user
```

### Code Flow (document_mode.py):

**Lines 1403-1435: Entity Extraction Block**
```python
if data_type == 'numeric' and ENTITY_EXTRACTOR_AVAILABLE:
    logger.info("🔍 Applying entity-based extraction...")
    extractor = get_entity_extractor()
    extractor.reset()  # Clear previous extractions
    
    # Extract entities from ALL chunks
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
```

**Fallback:** If entity extraction fails or finds 0 entities, system uses original chunks (graceful degradation).

---

## 📊 Detection Patterns

### 11 Entity Patterns:
1. **Named Entities**: TAIMUR, FAZL, MARI, etc. (uppercase 3+ letters)
2. **Products**: OIL, LPG, CONDEN, CONDENSATE, GAS, etc.
3. **Custom Uppercase**: Any 3+ uppercase word (PRODUCTION, SALES, etc.)
4. **Sheet References**: "Sheet 1", "Sheet A", etc.
5. **Location Patterns**: "Location: [name]"
6. **Well Patterns**: "Well: [name]", "Well #7", etc.
7. **Site Patterns**: "Site: [name]", "Site A", etc.
8. **Tank Patterns**: "Tank: [name]", "Tank-C", etc.
9. **Station**: Captures "Station [name]"
10. **Field**: Captures "Field [name]"
11. **Sector**: Captures "Sector [name]"

### 11 Parameter Types:
1. **Pressure**: Pressure, press, pres (psig, psi, bar, Pa, kPa)
2. **Temperature**: Temperature, temp (degF, °F, °C, degC)
3. **Volume**: Volume, vol, qty (bbl, barrel, m³, gal, L)
4. **API Gravity**: API, gravity, dAPI (dAPI, °API)
5. **Energy**: Energy, MMBtu, BTU (MMBtu, BTU, GJ)
6. **Ticket**: Ticket, ticket no, ticket# (unitless)
7. **Sales**: Sales, sold, revenue (unitless or $)
8. **Product**: Product, type, grade (text)
9. **Status**: Status, state, condition (text)
10. **Storage**: Storage, stored, inventory (bbl, m³)
11. **Delivery**: Delivery, delivered, shipped (bbl, m³)

### 9 Unit Types:
1. **psig**: Pressure (psig, psi)
2. **degF**: Temperature (degF, °F, deg F)
3. **bbl**: Volume (bbl, barrel, barrels)
4. **dAPI**: API Gravity (dAPI, °API, deg API)
5. **MMBtu**: Energy (MMBtu, MMBTU)
6. **%**: Percentage (%)
7. **mcf**: Gas Volume (mcf, MCF)
8. **ft**: Length (ft, feet)
9. **gal**: Volume (gal, gallon)

---

## 🎯 Usage Examples

### Example 1: Single Entity in Multiple Chunks

**Document 1 (Chunk 1):**
```
TAIMUR pressure is 327.07 psig
```

**Document 2 (Chunk 2):**
```
TAIMUR temperature: 301.9 degF
```

**Entity Extraction Output:**
```markdown
| Entity | Pressure | Unit | Temperature | Unit | Notes |
|--------|----------|------|-------------|------|-------|
| TAIMUR | 327.07 | psig | 301.9 | degF | Explicit |
```
✅ **Auto-merged from 2 chunks into 1 row**

---

### Example 2: Multiple Entities

**Document:**
```
Tank-C:MARI DEEP pressure 327.07 psig, temperature 301.9°F
Tank-C:Fazl X-1 pressure 3124 psig
LPG volume: 845.2 barrels
```

**Entity Extraction Output:**
```markdown
| Entity | Pressure | Unit | Temperature | Unit | Volume | Unit | Notes |
|--------|----------|------|-------------|------|--------|------|-------|
| MARI DEEP | 327.07 | psig | 301.9 | degF | — | bbl | Explicit |
| Fazl X-1 | 3124 | psig | — | degF | — | bbl | Inferred from context |
| LPG | — | psig | — | degF | 845.2 | bbl | Explicit |
```
✅ **3 entities with different parameters**

---

### Example 3: Multi-File Entity Merging

**File 1 (January.pdf):**
```
TAIMUR pressure: 327.07 psig
```

**File 2 (February.xlsx):**
```
| Well | Temperature | Volume |
|------|-------------|--------|
| TAIMUR | 301.9 | 1250.5 |
```

**Entity Extraction Output:**
```markdown
| Entity | Pressure | Unit | Temperature | Unit | Volume | Unit | Sources | Notes |
|--------|----------|------|-------------|------|--------|------|---------|-------|
| TAIMUR | 327.07 | psig | 301.9 | degF | 1250.5 | bbl | January.pdf, February.xlsx | Explicit |
```
✅ **Single TAIMUR row merged from 2 files**

---

## 🔍 How It Works

### Detection Algorithm:

1. **Entity Name Detection:**
   - Regex match against 11 entity patterns
   - Extract entity name (e.g., "TAIMUR", "LPG", "Tank-C")
   - Store with source file metadata

2. **Parameter Detection:**
   - Scan text for 11 parameter patterns
   - Match parameter type (Pressure, Temperature, etc.)
   - Extract numeric value or text value

3. **Unit Detection:**
   - Check for explicit units (psig, degF, bbl, etc.)
   - Infer unit from parameter type if not found
   - Add notes: "Explicit" or "Inferred from context"

4. **Entity Merging:**
   - Group all data by entity name
   - Merge parameters from multiple chunks/files
   - Avoid duplicate rows for same entity
   - Track sources (file names)

5. **Output Formatting:**
   - Convert to Markdown table (default)
   - Or JSON format (if requested)
   - Include all parameters with units
   - Add "Notes" column for unit source (explicit/inferred)

---

## 📋 Output Formats

### Markdown Table (Default):
```markdown
| Entity | Parameter | Value | Unit | Notes |
|--------|-----------|-------|------|-------|
| TAIMUR | Pressure | 327.07 | psig | Explicit |
| TAIMUR | Temperature | 301.9 | degF | Explicit |
| LPG | Volume | 845.2 | bbl | Inferred from context |
```

### JSON (If Requested):
```json
[
  {
    "Entity": "TAIMUR",
    "Pressure": 327.07,
    "Pressure_Unit": "psig",
    "Temperature": 301.9,
    "Temperature_Unit": "degF",
    "Notes": "Explicit"
  },
  {
    "Entity": "LPG",
    "Volume": 845.2,
    "Volume_Unit": "bbl",
    "Notes": "Inferred from context"
  }
]
```

---

## 🛠️ Testing Instructions

### Test 1: Basic Entity Detection
1. Upload document with "TAIMUR pressure 327.07 psig"
2. Query: "Extract all data at each location"
3. Expected: Single row with TAIMUR entity and pressure parameter

### Test 2: Multi-Parameter Extraction
1. Upload document with multiple parameters for one entity
2. Query: "Show all parameters for each entity"
3. Expected: One row per entity with all parameters in columns

### Test 3: Multi-File Merging
1. Upload 2+ files with same entity (e.g., TAIMUR in file1.pdf and file2.xlsx)
2. Query: "Extract all data at each location"
3. Expected: Single TAIMUR row with merged data, Sources metadata shows both files

### Test 4: Mixed Entities
1. Upload document with TAIMUR, LPG, CONDEN
2. Query: "Extract all measurements"
3. Expected: 3 rows (one per entity) with their respective parameters

### Test 5: NULL Handling
1. Upload document where TAIMUR has pressure but no temperature
2. Query: "Extract all data"
3. Expected: TAIMUR row shows pressure value, temperature shows "—" or NULL

### Test 6: Text Parameters
1. Upload document with Product, Status columns
2. Query: "Extract all data"
3. Expected: Text parameters (Product: "LPG", Status: "Active") included in output

---

## 🔎 Verification Checklist

**Check logs for:**
- ✅ "Entity extractor available for smart data extraction" (startup)
- ✅ "🔍 Applying entity-based extraction..." (query time)
- ✅ "✅ Extracted N entities: TAIMUR, LPG, CONDEN, ..." (query time)

**Check output for:**
- ✅ Unified table with entity names
- ✅ All parameters grouped by entity
- ✅ Units detected (psig, degF, bbl, etc.)
- ✅ No duplicate rows for same entity
- ✅ "Notes" column shows "Explicit" or "Inferred from context"
- ✅ Text parameters (Product, Status) included
- ✅ NULL values shown as "—" or "NULL", not "0"

**Check for errors:**
- ❌ No "⚠️ No entities detected, using original chunks"
- ❌ No "Entity extraction failed: [error]"
- ❌ No duplicate entity rows
- ❌ No placeholder labels ("Source 1", "Source 2")

---

## 🐛 Troubleshooting

### Issue: "No entities detected"
**Cause:** Entity patterns didn't match any text in chunks  
**Solution:** Check if entity names are uppercase (TAIMUR vs Taimur), verify pattern matches in entity_extractor.py

### Issue: Duplicate entity rows
**Cause:** Entity merging logic failed  
**Solution:** Check EntityExtractor.merge_entities() - should group by entity name

### Issue: Wrong units detected
**Cause:** Unit inference logic incorrect  
**Solution:** Check UNIT_PATTERNS in entity_extractor.py, ensure explicit units are in text

### Issue: Missing parameters
**Cause:** Parameter patterns didn't match  
**Solution:** Check PARAMETER_PATTERNS in entity_extractor.py, add custom patterns if needed

### Issue: Entity extraction not triggered
**Cause:** 
1. Query didn't trigger numeric mode (check intent detection)
2. ENTITY_EXTRACTOR_AVAILABLE = False (import error)
**Solution:** 
1. Use strict numeric triggers ("extract all data", "show all parameters")
2. Check logs for "Entity extractor available" message at startup

---

## 📂 Files Modified

### New Files:
- **entity_extractor.py** (450+ lines)
  - EntityExtractor class with pattern-based detection
  - 11 entity patterns, 11 parameter patterns, 9 unit patterns
  - Auto-merging and output formatting

### Modified Files:
- **document_mode.py** (V3.7)
  - Lines 60-95: Added entity extractor import
  - Lines 817-825: Updated system prompt to mention entity extraction
  - Lines 1403-1435: Added entity extraction block in stream_rag_response()

---

## 🎓 Key Features

### 1. **Automatic Entity Detection**
No manual tagging needed - system detects entities using 11 regex patterns.

### 2. **Cross-File Merging**
Same entity in multiple files = single merged row with all parameters.

### 3. **Smart Unit Detection**
Explicit units (psig in text) or inferred (from parameter type) with clear notes.

### 4. **Graceful Fallback**
If entity extraction fails → uses original chunks (no error to user).

### 5. **Parameter Flexibility**
Numeric (Pressure, Temperature) AND text (Product, Status) parameters supported.

### 6. **NULL Handling**
Missing parameters shown as "—" or NULL with notes, not invented as "0".

### 7. **Source Tracking**
Metadata includes which files/sheets contributed to each entity's data.

---

## 🚀 Next Steps

1. **Restart application** to load V3.7:
   ```bash
   pkill streamlit
   streamlit run app.py
   ```

2. **Verify startup logs**:
   - Look for "Entity extractor available for smart data extraction"

3. **Test with sample query**:
   - Upload document with entities (TAIMUR, LPG, etc.)
   - Query: "Extract all data at each location"
   - Verify unified entity table with merged data

4. **Test multi-file merging**:
   - Upload 2+ files with same entity
   - Verify single row per entity with combined data

---

## 📊 Version History

- **V3.5**: Basic numeric extraction mode
- **V3.6**: Smart intent detection + structured data access
- **V3.6.1-3.6.2**: NULL handling + column completeness
- **V3.7**: Entity-based extraction with auto-merging ← **CURRENT**

---

## 📞 Support

**Entity extraction not working?**
1. Check logs for "Entity extractor available" at startup
2. Verify numeric mode triggers ("extract all", "show parameters")
3. Ensure entities are uppercase (TAIMUR, not Taimur)
4. Check entity_extractor.py patterns match your entity names

**Missing parameters?**
1. Check PARAMETER_PATTERNS in entity_extractor.py
2. Add custom patterns if needed
3. Verify parameter names in document match patterns

**Wrong units?**
1. Use explicit units in text (327.07 psig, not just 327.07)
2. Check UNIT_PATTERNS in entity_extractor.py
3. Review unit inference logic in detect_unit()

---

**Status**: ✅ Complete and integrated (V3.7)  
**Next**: User testing with multi-file entity merging
