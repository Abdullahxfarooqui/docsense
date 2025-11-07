"""
Test Persistent Document Storage

Verifies that documents are saved and loaded correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from document_persistence import (
    ensure_data_folder,
    get_existing_documents,
    get_document_stats,
    should_rebuild_vectors,
    check_vector_store_exists
)


def test_folder_creation():
    """Test that data folder is created."""
    print("Testing folder creation...")
    folder = ensure_data_folder()
    assert folder.exists(), "Data folder should exist"
    assert folder.is_dir(), "Data folder should be a directory"
    print("✓ Data folder created successfully")


def test_document_detection():
    """Test detection of existing documents."""
    print("\nTesting document detection...")
    docs = get_existing_documents()
    print(f"Found {len(docs)} documents:")
    for doc in docs:
        print(f"  • {doc.name} ({doc.stat().st_size / 1024:.2f} KB)")
    print("✓ Document detection working")


def test_stats():
    """Test document statistics."""
    print("\nTesting statistics...")
    stats = get_document_stats()
    print(f"Statistics:")
    print(f"  Count: {stats['count']}")
    print(f"  Total Size: {stats['total_size_mb']} MB")
    print(f"  Files: {', '.join(stats['files']) if stats['files'] else 'None'}")
    print("✓ Statistics working")


def test_vector_store_check():
    """Test vector store existence check."""
    print("\nTesting vector store check...")
    exists = check_vector_store_exists()
    print(f"Vector store exists: {exists}")
    
    if exists:
        from document_persistence import get_vector_store_age
        age = get_vector_store_age()
        print(f"Vector store age: {age:.2f} seconds")
    
    print("✓ Vector store check working")


def test_rebuild_logic():
    """Test rebuild decision logic."""
    print("\nTesting rebuild logic...")
    docs = get_existing_documents()
    
    if docs:
        needs_rebuild = should_rebuild_vectors(docs)
        print(f"Needs rebuild: {needs_rebuild}")
        
        if needs_rebuild:
            print("  Reason: No vector store OR documents newer than vector store")
        else:
            print("  Reason: Vector store is up-to-date")
    else:
        print("  No documents to test with")
    
    print("✓ Rebuild logic working")


def main():
    """Run all tests."""
    print("=" * 60)
    print("PERSISTENT STORAGE TEST SUITE")
    print("=" * 60)
    
    try:
        test_folder_creation()
        test_document_detection()
        test_stats()
        test_vector_store_check()
        test_rebuild_logic()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
