"""
Integration tests for the RAG pipeline (Ollama local).
"""
import pytest
from app.core.rag_pipeline import RAGPipeline
from app.core.document_processor import DocumentProcessor


class TestDocumentProcessor:
    def setup_method(self):
        self.processor = DocumentProcessor(chunk_size=200, chunk_overlap=20)

    def test_chunk_size_respected(self):
        text = "A" * 500
        pages = [{"text": text, "document": "test.txt", "page": 1, "section": "test"}]
        chunks = self.processor.chunk_pages(pages)
        for chunk in chunks:
            assert len(chunk.text) <= 300

    def test_metadata_preserved(self):
        pages = [{"text": "Hello world", "document": "hr.pdf", "page": 5, "section": "Policy"}]
        chunks = self.processor.chunk_pages(pages)
        assert len(chunks) == 1
        assert chunks[0].document == "hr.pdf"
        assert chunks[0].page == 5
        assert chunks[0].section == "Policy"

    def test_empty_text_skipped(self):
        pages = [{"text": "", "document": "empty.txt", "page": 1, "section": None}]
        chunks = self.processor.chunk_pages(pages)
        assert len(chunks) == 0

    def test_unsupported_file_type(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            self.processor.load_document("test.xyz")


class TestRAGPipeline:
    @pytest.fixture
    def pipeline(self):
        return RAGPipeline()

    def test_pipeline_initialization(self, pipeline):
        assert pipeline.embedding_engine is not None
        assert pipeline.vector_store is not None
        assert pipeline.retriever is not None
        assert pipeline.generator is not None

    def test_ask_returns_required_fields(self, pipeline):
        result = pipeline.ask("What is the leave policy?")
        assert "answer" in result
        assert "sources" in result
        assert "confidence" in result
        assert "conversation_id" in result

    def test_conversation_persistence(self, pipeline):
        result1 = pipeline.ask("Hello", conversation_id="test-conv-1")
        assert result1["conversation_id"] == "test-conv-1"
        assert "test-conv-1" in pipeline.conversations

    def test_ollama_status_check(self, pipeline):
        status = pipeline.check_ollama_status()
        assert "reachable" in status
        assert "models" in status
