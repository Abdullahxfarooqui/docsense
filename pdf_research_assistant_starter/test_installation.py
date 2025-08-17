#!/usr/bin/env python3
"""
Installation and Environment Test Script for PDF Research Assistant

This script validates that all dependencies are properly installed and
the environment is configured correctly for running the PDF Research Assistant.

Usage:
    python test_installation.py
"""

import sys
import os
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_python_version() -> bool:
    """Test if Python version meets requirements."""
    try:
        version_info = sys.version_info
        if version_info.major >= 3 and version_info.minor >= 10:
            logger.info(f"✅ Python version {version_info.major}.{version_info.minor}.{version_info.micro} is supported")
            return True
        else:
            logger.error(f"❌ Python version {version_info.major}.{version_info.minor}.{version_info.micro} is not supported. Requires Python 3.10+")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to check Python version: {e}")
        return False

def test_dependencies() -> Tuple[bool, List[str]]:
    """Test if all required dependencies are installed."""
    required_packages = [
        'streamlit',
        'langchain',
        'langchain_openai',
        'langchain_community',
        'chromadb',
        'openai',
        'fitz',  # PyMuPDF
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'fitz':
                import fitz
                logger.info(f"✅ {package} (PyMuPDF) is installed")
            elif package == 'dotenv':
                from dotenv import load_dotenv
                logger.info(f"✅ {package} (python-dotenv) is installed")
            else:
                __import__(package)
                logger.info(f"✅ {package} is installed")
        except ImportError:
            logger.error(f"❌ {package} is not installed")
            missing_packages.append(package)
        except Exception as e:
            logger.error(f"❌ Error importing {package}: {e}")
            missing_packages.append(package)
    
    success = len(missing_packages) == 0
    return success, missing_packages

def test_environment() -> bool:
    """Test environment variable configuration."""
    try:
        # Try to load from .env file first
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key:
            # Don't log the actual key for security
            key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            logger.info(f"✅ OPENAI_API_KEY is set ({key_preview})")
            return True
        else:
            logger.error("❌ OPENAI_API_KEY environment variable is not set")
            logger.info("   Please set it using: export OPENAI_API_KEY='your_api_key_here'")
            logger.info("   Or create a .env file with: OPENAI_API_KEY=your_api_key_here")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to check environment: {e}")
        return False

def test_module_imports() -> bool:
    """Test if custom modules can be imported."""
    try:
        # Test importing custom modules
        from ingestion import ingest_pdfs, get_ingestion_stats
        logger.info("✅ ingestion module imported successfully")
        
        from query_engine import get_query_engine
        logger.info("✅ query_engine module imported successfully")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import custom modules: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error importing custom modules: {e}")
        return False

def test_chromadb_initialization() -> bool:
    """Test ChromaDB initialization."""
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Try to create a test client
        client = chromadb.PersistentClient(path=".test_chromadb")
        test_collection = client.get_or_create_collection(name="test_collection")
        
        # Clean up test database
        try:
            import shutil
            shutil.rmtree(".test_chromadb", ignore_errors=True)
        except:
            pass
        
        logger.info("✅ ChromaDB initialization successful")
        return True
    except Exception as e:
        logger.error(f"❌ ChromaDB initialization failed: {e}")
        return False

def test_openai_connection() -> bool:
    """Test OpenAI API connection (if API key is available)."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️  Skipping OpenAI connection test (no API key)")
            return True
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Test with a minimal request
        models = client.models.list()
        logger.info("✅ OpenAI API connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI API connection failed: {e}")
        logger.info("   Please check your API key and internet connection")
        return False

def generate_report(results: Dict[str, bool], missing_packages: List[str]) -> None:
    """Generate a summary report of test results."""
    print("\n" + "="*60)
    print("PDF RESEARCH ASSISTANT - INSTALLATION TEST REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall Status: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your environment is ready.")
    else:
        print("❌ Some tests failed. Please review the issues above.")
    
    print("\nTest Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if missing_packages:
        print(f"\nMissing Packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print(f"\nTo install missing packages, run:")
        print(f"  pip install {' '.join(missing_packages)}")
    
    print("\nNext Steps:")
    if passed_tests == total_tests:
        print("  1. Run the application: streamlit run app.py")
        print("  2. Open http://localhost:8501 in your browser")
        print("  3. Upload PDF files and start asking questions!")
    else:
        print("  1. Fix the failing tests above")
        print("  2. Re-run this test script")
        print("  3. Once all tests pass, run: streamlit run app.py")
    
    print("\n" + "="*60)

def main():
    """Run all installation tests."""
    print("PDF Research Assistant - Installation Test")
    print("Testing your environment and dependencies...\n")
    
    # Run all tests
    results = {}
    missing_packages = []
    
    results["Python Version"] = test_python_version()
    deps_success, missing_deps = test_dependencies()
    results["Dependencies"] = deps_success
    missing_packages.extend(missing_deps)
    results["Environment Variables"] = test_environment()
    results["Module Imports"] = test_module_imports()
    results["ChromaDB"] = test_chromadb_initialization()
    results["OpenAI Connection"] = test_openai_connection()
    
    # Generate report
    generate_report(results, missing_packages)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
