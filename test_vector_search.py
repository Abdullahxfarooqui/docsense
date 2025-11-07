"""
Quick test to verify vector store has tank data
"""
import os
from dotenv import load_dotenv
from vector_store import get_vector_store
from document_engine import process_documents_with_embeddings

load_dotenv()

# Simulate file upload
class FakeFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.name = os.path.basename(filepath)
    
    def read(self):
        with open(self.filepath, 'rb') as f:
            return f.read()

# Process the PDF
print("Processing production data.pdf...")
fake_file = FakeFile("production data.pdf")
success = process_documents_with_embeddings([fake_file])

if success:
    print("✓ Document processed successfully")
    
    # Get vector store
    vector_store = get_vector_store()
    stats = vector_store.get_stats()
    
    print(f"\nVector Store Stats:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Vector count: {stats['vector_count']}")
    print(f"  Sources: {stats['sources']}")
    
    # Test search
    print("\n" + "="*60)
    print("Testing search queries...")
    print("="*60)
    
    test_queries = [
        "What is the total liquid volume?",
        "Show me HALINI tank data",
        "Tell me about tank deliveries"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.semantic_search(query, top_k=3)
        print(f"Found {len(results)} results:")
        for i, doc in enumerate(results, 1):
            text_preview = doc['text'][:150].replace('\n', ' ')
            print(f"  {i}. Type: {doc.get('type', 'text')}, Preview: {text_preview}...")
else:
    print("✗ Document processing failed")
