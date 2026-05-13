"""
Test script to validate CRAG System setup
Run this before deploying to production
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required packages are installed"""
    logger.info("🔍 Checking dependencies...")
    
    dependencies = [
        'faiss',
        'numpy',
        'sentence_transformers',
        'openai',
        'fastapi',
        'uvicorn',
        'dotenv'  # Note: pip package is 'python-dotenv' but import is 'dotenv'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            logger.info(f"  ✅ {dep}")
        except ImportError:
            logger.warning(f"  ❌ {dep} - NOT INSTALLED")
            missing.append(dep)
    
    if missing:
        logger.error(f"\n❌ Missing dependencies: {', '.join(missing)}")
        logger.info("Install with: pip install " + " ".join(missing))
        return False
    
    logger.info("✅ All dependencies installed!\n")
    return True


def check_embeddings():
    """Check if embeddings and FAISS index exist"""
    logger.info("🔍 Checking embeddings and FAISS index...")
    
    embeddings_dir = Path(__file__).parent / "Embeddings_data"
    
    files_to_check = {
        "FAISS Index": embeddings_dir / "faiss_index.bin",
        "Metadata": embeddings_dir / "metadata.json",
    }
    
    all_exist = True
    for name, path in files_to_check.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024**2)
            logger.info(f"  ✅ {name} ({size_mb:.2f} MB)")
        else:
            logger.warning(f"  ❌ {name} - NOT FOUND at {path}")
            all_exist = False
    
    if not all_exist:
        logger.error("\n❌ Missing embeddings. Run setup_faiss.py first")
        return False
    
    logger.info("✅ Embeddings ready!\n")
    return True


def check_environment():
    """Check if environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key and api_key.startswith("sk-"):
        logger.info("  ✅ OPENAI_API_KEY is set")
        return True
    else:
        logger.warning("  ❌ OPENAI_API_KEY not set or invalid")
        logger.info("     Set it in .env file:")
        logger.info("     OPENAI_API_KEY=sk-xxx...")
        return False


def test_faiss_retriever():
    """Test FAISS retriever functionality"""
    logger.info("🔍 Testing FAISS Retriever...")
    
    try:
        from Embeddings.faiss_retriever import FAISSRetriever
        
        retriever = FAISSRetriever()
        logger.info(f"  ✅ FAISS index loaded")
        logger.info(f"     Index size: {retriever.index.ntotal} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ FAISS Retriever failed: {e}")
        return False


def test_crag_system():
    """Test CRAG system initialization"""
    logger.info("🔍 Testing CRAG System...")
    
    try:
        from crag_system import CRAGSystem, CRAGRetriever, CRAGGenerator, CRAGCorrector
        from Embeddings.faiss_retriever import FAISSRetriever
        
        logger.info("  ✅ CRAG modules imported")
        
        faiss = FAISSRetriever()
        retriever = CRAGRetriever(faiss)
        generator = CRAGGenerator()
        corrector = CRAGCorrector()
        crag = CRAGSystem(faiss)
        
        logger.info("  ✅ All CRAG components initialized")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ CRAG System failed: {e}")
        return False


def test_api_imports():
    """Test if API imports work"""
    logger.info("🔍 Testing API imports...")
    
    try:
        from main import app, QueryRequest, QueryResponse
        
        logger.info("  ✅ FastAPI app imports successful")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ API imports failed: {e}")
        return False


def run_full_tests():
    """Run all tests and provide summary"""
    logger.info("=" * 60)
    logger.info("CRAG SYSTEM VALIDATION TEST")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("Dependencies", check_dependencies),
        ("Embeddings", check_embeddings),
        ("Environment", check_environment),
        ("FAISS Retriever", test_faiss_retriever),
        ("CRAG System", test_crag_system),
        ("API Imports", test_api_imports),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed\n")
    
    if passed == total:
        print("🎉 All tests passed! Your CRAG system is ready to use.")
        print("\nNext steps:")
        print("1. Start API server: uvicorn main:app --reload")
        print("2. Visit http://localhost:8000/docs for API documentation")
        print("3. Test with curl or Python requests")
        return True
    else:
        print("❌ Some tests failed. Fix issues above before deploying.")
        return False


if __name__ == "__main__":
    success = run_full_tests()
    sys.exit(0 if success else 1)
