# Persistent Document Storage Guide

## Overview

DocSense now supports **automatic persistent storage** of uploaded documents. Once you upload a PDF, it stays stored locally and loads automatically on the next app start.

## Features

### ✅ Auto-Load on Startup
- Documents in `/data` folder are automatically detected and loaded
- Vector embeddings are loaded from cache if available
- No need to re-upload documents after app restart

### 💾 Persistent Storage
- All uploaded PDFs/TXT files are saved to `/data` folder
- Files keep their original names
- Multiple documents can coexist in the folder

### 🔄 Smart Re-Vectorization
- If document is newer than vector store → rebuilds vectors
- If vector store is up-to-date → skips re-embedding
- Saves processing time on subsequent loads

### 📁 File Management
- View all stored documents in sidebar
- Delete individual documents with 🗑️ button
- Upload new documents to add to collection
- Re-uploading same file overwrites old version

## Folder Structure

```
docsense/
├── app_hybrid_v2.py
├── document_persistence.py      # New: Persistence manager
├── data/                         # New: Persistent storage folder
│   ├── production_data.pdf      # Your uploaded documents
│   ├── another_doc.pdf
│   └── vector_store.pkl         # Cached vector embeddings
└── ...
```

## How It Works

### First Upload
1. User uploads `production_data.pdf`
2. App saves file to `data/production_data.pdf`
3. Document is processed and vectorized
4. Vector store saved to `data/vector_store.pkl`
5. Status: "✓ Documents Saved & Vectorized"

### Subsequent App Starts
1. App starts → checks `data/` folder
2. Finds `production_data.pdf`
3. Checks if `vector_store.pkl` exists and is up-to-date
4. Auto-loads vectors from cache (instant)
5. Status: "✓ 1 document(s) loaded"

### Adding More Documents
1. Upload `new_document.pdf`
2. App saves to `data/new_document.pdf`
3. Re-processes ALL documents in `data/` folder
4. Updates vector store with all documents
5. Both documents now available for queries

## Usage Examples

### Example 1: Initial Setup
```python
# First time running app
# Upload production_data.pdf via sidebar
# → Saved to data/production_data.pdf
# → Vectors cached
```

### Example 2: Restart App
```python
# Restart Streamlit
# → App auto-detects data/production_data.pdf
# → Loads vectors from cache (fast!)
# → Ready to query immediately
```

### Example 3: Add Another Document
```python
# Upload another_doc.pdf
# → Saved to data/another_doc.pdf
# → Re-vectorizes all documents
# → Both available for queries
```

### Example 4: Delete Document
```python
# Click 🗑️ next to production_data.pdf
# → File deleted from data/ folder
# → Vector store cleared
# → Only another_doc.pdf remains
```

## API Reference

### `document_persistence.py` Functions

#### `ensure_data_folder() -> Path`
Creates `/data` folder if it doesn't exist.

#### `get_existing_documents() -> List[Path]`
Returns list of all PDFs/TXT files in `/data` folder.

#### `save_uploaded_file(uploaded_file, overwrite=True) -> Path`
Saves a single uploaded file to `/data` folder.

#### `save_multiple_files(uploaded_files) -> List[Path]`
Saves multiple uploaded files at once.

#### `load_document_from_path(file_path) -> FileWrapper`
Loads document from disk as file-like object for processing.

#### `get_document_stats() -> Dict`
Returns statistics about stored documents:
```python
{
    'count': 2,
    'total_size_mb': 5.43,
    'files': ['production_data.pdf', 'another_doc.pdf']
}
```

#### `delete_document(filename) -> bool`
Deletes a specific document from storage.

#### `should_rebuild_vectors(documents) -> bool`
Determines if vector store needs rebuilding based on file timestamps.

## Configuration

### Storage Location
Default: `./data/` (relative to app root)

To change location, modify `DATA_FOLDER` in `document_persistence.py`:
```python
DATA_FOLDER = Path("data")  # Change to your preferred path
```

### Vector Store Cache
Default: `data/vector_store.pkl`

To change location, modify `VECTOR_STORE_PATH` in `document_persistence.py`:
```python
VECTOR_STORE_PATH = DATA_FOLDER / "vector_store.pkl"
```

## Status Messages

| Message | Meaning |
|---------|---------|
| "✓ 2 document(s) loaded (5.43 MB)" | Documents auto-loaded from storage |
| "📤 1 new file(s) ready to upload" | New files detected in uploader |
| "💾 Saving files to persistent storage..." | Saving files to `/data` folder |
| "✓ Documents Saved & Vectorized" | Processing complete, files persisted |
| "💡 Documents will auto-load on next app start" | Reminder about persistence |

## Troubleshooting

### Documents Not Auto-Loading
**Symptom:** App starts but doesn't load documents from `/data` folder

**Solutions:**
1. Check if `/data` folder exists in app root directory
2. Verify files are valid PDFs/TXT (check extensions)
3. Check logs for auto-load errors
4. Try deleting `vector_store.pkl` to force rebuild

### Vector Store Out of Sync
**Symptom:** Queries return wrong results or no results

**Solutions:**
1. Delete `data/vector_store.pkl`
2. Restart app (will rebuild vectors)
3. Or click "🚀 Process Documents" to force rebuild

### File Already Exists Error
**Symptom:** Can't upload file with same name

**Solutions:**
- Re-uploading automatically overwrites old file
- Or delete old file first using 🗑️ button

## Performance Notes

### Initial Processing
- First upload processes document fully (~5-30 seconds depending on size)
- Creates vector embeddings for all chunks
- Saves vectors to disk

### Subsequent Loads
- Instant loading from cached vectors (<1 second)
- Skips text extraction and embedding
- Much faster than re-processing

### When Vectors Rebuild
- Document modified after vector store created
- Vector store file deleted or corrupted
- Manual re-processing via "🚀 Process Documents"

## Best Practices

1. **Keep Original Filenames**: Use descriptive names like `production_data_2025.pdf`
2. **Don't Edit Files in /data**: Upload new versions instead
3. **Backup /data Folder**: Contains your uploaded documents
4. **Monitor Disk Space**: Large PDFs accumulate quickly
5. **Periodic Cleanup**: Delete unused documents to save space

## Integration with Streamlit Cloud

When deploying to Streamlit Cloud:

1. **Note:** Cloud storage is ephemeral (resets on each deploy)
2. **Solution:** Use cloud storage services (S3, GCS, etc.)
3. **Alternative:** Store documents in GitHub repository (for public docs only)

For persistent cloud storage, modify `document_persistence.py` to use:
- AWS S3 (`boto3`)
- Google Cloud Storage (`google-cloud-storage`)
- Azure Blob Storage (`azure-storage-blob`)

## Security Considerations

1. **Local Development**: `/data` folder is in `.gitignore` (keeps documents private)
2. **Sensitive Data**: Don't commit documents to GitHub
3. **API Keys**: Keep in `.env` file (never in documents)
4. **Access Control**: Add authentication if deploying publicly

## Future Enhancements

Potential improvements:
- [ ] Document versioning (keep old versions)
- [ ] Search within stored documents by metadata
- [ ] Cloud storage integration (S3, GCS)
- [ ] Document categories/tags
- [ ] Compression for large PDFs
- [ ] Incremental vectorization (add without rebuilding all)

## Questions?

See main documentation or check logs for detailed error messages.
