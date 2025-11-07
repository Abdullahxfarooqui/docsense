# Persistent Storage - Quick Start

## What Changed?

### Before ❌
- Upload PDF → Process → Query ✅
- Restart app → **Documents gone** ❌
- Need to re-upload every time 😞

### After ✅
- Upload PDF → **Saved to /data folder** → Process ✅
- Restart app → **Auto-loads from /data** → Ready instantly! 🚀
- Documents persist forever 🎉

## Quick Demo

### 1️⃣ First Upload
```
User Action: Upload production_data.pdf
App Response: 
  💾 Saving files to persistent storage...
  ✓ Documents Saved & Vectorized
  💡 Documents will auto-load on next app start
  
File System:
  data/
  ├── production_data.pdf     ← Saved!
  └── vector_store.pkl        ← Cached embeddings!
```

### 2️⃣ Restart App
```
User Action: Restart Streamlit
App Response:
  ✓ 1 document(s) loaded (2.5 MB)
  📁 Stored Documents (1)
     • production_data.pdf
     
Status: Ready to query immediately! ⚡
(No re-upload needed)
```

### 3️⃣ Add More Documents
```
User Action: Upload another_doc.pdf
App Response:
  📤 1 new file(s) ready to upload
  💾 Saving files to persistent storage...
  ✓ Documents Saved & Vectorized
  
File System:
  data/
  ├── production_data.pdf     ← Still there!
  ├── another_doc.pdf         ← New!
  └── vector_store.pkl        ← Updated!
```

### 4️⃣ Delete Document
```
User Action: Click 🗑️ next to production_data.pdf
App Response:
  File deleted from storage
  ✓ 1 document(s) loaded (1.8 MB)
  
File System:
  data/
  ├── another_doc.pdf         ← Only this remains
  └── vector_store.pkl        ← Rebuilt
```

## Key Features

| Feature | Description |
|---------|-------------|
| 💾 **Persistent Storage** | PDFs saved to `/data` folder |
| 🚀 **Auto-Load** | Documents load automatically on startup |
| ⚡ **Smart Caching** | Vectors cached, skip re-embedding |
| 📁 **File Management** | View/delete documents in UI |
| 🔄 **Overwrite Support** | Re-upload same file to update |

## UI Changes

### Sidebar (Document Mode)
```
📄 Upload Documents
━━━━━━━━━━━━━━━━━━━━━
✓ 2 document(s) loaded (5.43 MB)

📁 Stored Documents (2)
  • production_data.pdf    🗑️
  • another_doc.pdf        🗑️

Upload new PDF or TXT files
[Choose files] 
🚀 Process Documents
```

## Status Messages

| When | Message |
|------|---------|
| App starts with docs | ✓ 2 document(s) loaded (5.43 MB) |
| New file in uploader | 📤 1 new file(s) ready to upload |
| Saving files | 💾 Saving files to persistent storage... |
| Processing complete | ✓ Documents Saved & Vectorized |
| After save | 💡 Documents will auto-load on next app start |

## Files Changed

1. **document_persistence.py** (NEW)
   - Manages `/data` folder
   - Save/load/delete operations
   - Smart caching logic

2. **app_hybrid_v2.py** (MODIFIED)
   - Auto-load on startup
   - File management UI
   - Status messages

3. **document_engine.py** (MODIFIED)
   - Saves vector store after processing

4. **vector_store.py** (MODIFIED)
   - Auto-loads from `data/vector_store.pkl`

5. **.gitignore** (MODIFIED)
   - Excludes `/data` folder from git

## Folder Structure

```
docsense/
├── app_hybrid_v2.py
├── document_persistence.py    ← NEW
├── data/                      ← NEW (auto-created)
│   ├── *.pdf                 ← Your documents
│   └── vector_store.pkl      ← Cached vectors
└── ...
```

## Performance

| Operation | Before | After |
|-----------|--------|-------|
| First upload | 10-30s | 10-30s (same) |
| App restart | Re-upload + 10-30s | **< 1s** ⚡ |
| Adding doc | Re-upload all | Upload new only |

## Next Steps

1. **Test it:** Upload a PDF and restart the app
2. **Verify:** Check that `/data` folder is created
3. **Query:** Documents should be ready immediately
4. **Manage:** Use 🗑️ button to delete unwanted docs

## Troubleshooting

**Q: Documents not loading?**  
A: Check if `/data` folder exists and contains PDFs

**Q: Wrong query results?**  
A: Delete `data/vector_store.pkl` and restart

**Q: Can't upload file?**  
A: File is auto-overwritten if name exists

## Documentation

For detailed information, see:
- **PERSISTENT_STORAGE_GUIDE.md** - Full documentation
- Logs in terminal for debugging

---

**Status: ✅ DEPLOYED**  
Commit: 73f8f44  
Branch: main
