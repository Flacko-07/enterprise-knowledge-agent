"""
Main RAG Pipeline — Now delegates question-answering to the RAG Agent.
"""
import uuid
import logging
from typing import Optional

from app.config import get_settings
from app.core.document_processor import DocumentProcessor
from app.core.embedding import EmbeddingEngine
from app.core.vector_store import VectorStore
from app.core.retriever import HybridRetriever
from app.core.agent import RAGAgent

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGPipeline:
    """Application pipeline: ingestion + Agentic Q&A."""

    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.vector_store = VectorStore(self.embedding_engine)
        self.document_processor = DocumentProcessor()
        self.retriever = HybridRetriever(self.vector_store)
        
        # The Agentic Core
        self.agent = RAGAgent(self.retriever)

        self.conversations: dict[str, list[dict]] = {}
        self._initialized = False

    def initialize(self):
        if not self._initialized:
            self.retriever.initialize_bm25()
            self._initialized = True
            logger.info("RAG Pipeline fully initialized (Agentic Mode)")

    def ingest_documents(self, directory: str = None) -> dict:
        directory = directory or "./data/sample_documents"
        logger.info(f"Starting document ingestion from: {directory}")
        chunks = self.document_processor.process_directory(directory)
        if not chunks:
            return {"status": "warning", "documents_processed": 0, "chunks_created": 0, "errors": ["No documents found"]}

        added = self.vector_store.add_chunks(chunks)
        self.retriever.initialize_bm25()
        logger.info(f"Ingestion complete: {added} chunks indexed")
        return {"status": "success", "documents_processed": len(set(c.document for c in chunks)), "chunks_created": added, "errors": []}

    def ask(self, question: str, conversation_id: Optional[str] = None) -> dict:
        if not self._initialized:
            self.initialize()

        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # Ollama chat format history
        conversation_history = self.conversations[conversation_id]

        # Run Agent
        result = self.agent.run(question, conversation_history)

        # Update history
        conversation_history.append({"role": "user", "content": question})
        assistant_msg = result["answer"]
        if result.get("requires_clarification"):
            assistant_msg = f"[Clarification needed]: {result.get('clarification_question', '')}"
        conversation_history.append({"role": "assistant", "content": assistant_msg})

        result["conversation_id"] = conversation_id
        return result

    def get_stats(self) -> dict:
        stats = self.vector_store.get_collection_stats()
        return {**stats, "pipeline_initialized": self._initialized, "active_conversations": len(self.conversations), "embedding_model": self.embedding_engine.model_name, "llm_model": settings.ollama_llm_model, "mode": "agentic"}

    def check_ollama_status(self) -> dict:
        import httpx
        try:
            resp = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {
                "reachable": True, "models": models,
                "llm_ready": any(settings.ollama_llm_model in m or m.startswith(settings.ollama_llm_model.split(":")[0]) for m in models),
                "embedding_ready": any(settings.ollama_embedding_model in m or m.startswith(settings.ollama_embedding_model.split(":")[0]) for m in models) if settings.embedding_provider == "ollama" else True,
            }
        except Exception as e:
            return {"reachable": False, "models": [], "llm_ready": False, "embedding_ready": False, "error": str(e)}