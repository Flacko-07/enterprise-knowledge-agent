"""
Standalone ingestion script.
Usage: python ingest.py [directory_path]
"""
import sys
import logging

logging.basicConfig(level=logging.INFO)

from app.core.rag_pipeline import RAGPipeline


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "./data/sample_documents"

    print("=" * 60)
    print("Enterprise Knowledge Assistant — Document Ingestion")
    print("=" * 60)

    print("\n🔧 Initializing RAG Pipeline...")
    pipeline = RAGPipeline()

    # Check Ollama
    status = pipeline.check_ollama_status()
    if status["reachable"]:
        print(f"   ✅ Ollama reachable. Models: {status['models']}")
    else:
        print(f"   ⚠️  Ollama not reachable (embedding may use fallback)")

    print(f"\n📁 Ingesting documents from: {directory}")
    result = pipeline.ingest_documents(directory)

    print(f"\n{'='*50}")
    print(f"Status:              {result['status']}")
    print(f"Documents processed: {result['documents_processed']}")
    print(f"Chunks created:      {result['chunks_created']}")
    if result['errors']:
        print(f"Errors:              {result['errors']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
