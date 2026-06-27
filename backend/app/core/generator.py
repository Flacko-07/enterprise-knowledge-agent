"""
LLM-based answer generation using local Ollama — zero cloud dependencies.
Strict citation requirements and hallucination prevention via constrained prompting.
"""
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnswerGenerator:
    """Generates answers from retrieved context using Ollama LLM."""

    SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Answer employee questions accurately based ONLY on the provided context documents.

CRITICAL RULES:
1. Answer ONLY using the information provided in the context below.
2. If the context does not contain enough information to answer the question, say "I don't have enough information to answer this question based on the available documents."
3. Do NOT make up, infer, or hallucinate any information.
4. Always cite your sources by referencing the document name and page number.
5. Be concise but complete. Use bullet points for multi-part answers.
6. If multiple documents provide relevant information, synthesize them.
7. If documents contradict each other, mention the contradiction and cite both sources.

Citation format: [Source: DocumentName, Page X]"""

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_llm_model
        self._available: bool | None = None

    def _check_availability(self) -> bool:
        """Check if Ollama server is reachable and model is available."""
        if self._available is not None:
            return self._available
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            # Check if our model (or a base match) is present
            model_available = any(
                self.model in m or m.startswith(self.model.split(":")[0])
                for m in models
            )
            if not model_available:
                logger.warning(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Available: {models}. Run: ollama pull {self.model}"
                )
            self._available = model_available
            return self._available
        except Exception as e:
            logger.error(f"Ollama not reachable at {self.base_url}: {e}")
            self._available = False
            return False

    @property
    def is_ready(self) -> bool:
        return self._check_availability()

    def generate(
        self,
        query: str,
        context_documents: list[dict],
        conversation_history: list[dict] = None,
    ) -> dict:
        if not context_documents:
            return {
                "answer": "I don't have enough information to answer this question based on the available documents.",
                "has_answer": False,
                "confidence": 0.0,
            }

        context_text = self._format_context(context_documents)

        # Build the full prompt for Ollama
        prompt = self._build_prompt(query, context_text, conversation_history)

        if not self._check_availability():
            return self._fallback_generate(query, context_documents)

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.llm_temperature,
                        "num_ctx": settings.llm_num_ctx,
                        "num_predict": settings.llm_num_predict,
                    },
                },
                timeout=120.0,  # Local LLMs can be slow
            )
            resp.raise_for_status()
            answer = resp.json().get("response", "").strip()

            if not answer:
                return self._fallback_generate(query, context_documents)

            confidence = self._calculate_confidence(context_documents)
            has_answer = (
                "don't have enough information" not in answer.lower()
                and "not available" not in answer.lower()
            )

            return {
                "answer": answer,
                "has_answer": has_answer,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return self._fallback_generate(query, context_documents)

    def _build_prompt(
        self, query: str, context: str, conversation_history: list[dict] = None
    ) -> str:
        """Build the full prompt for Ollama's /api/generate endpoint."""
        parts = [self.SYSTEM_PROMPT]

        # Add conversation history
        if conversation_history:
            parts.append("\nConversation history:")
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"{role.title()}: {content}")

        parts.append(f"\nContext documents:\n{context}")
        parts.append(f"\nQuestion: {query}")
        parts.append(
            "\nPlease answer the question based only on the context documents above. "
            "Include source citations."
        )

        return "\n".join(parts)

    def _format_context(self, documents: list[dict]) -> str:
        formatted_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            doc_name = metadata.get("document", "Unknown")
            page = metadata.get("page", "")
            section = metadata.get("section", "")
            page_str = f", Page {page}" if page and page != "" else ""
            section_str = f" | Section: {section}" if section and section != "" else ""

            formatted_parts.append(
                f"[Document {i}: {doc_name}{page_str}{section_str}]\n"
                f"{doc['text']}\n"
            )

        return "\n---\n".join(formatted_parts)

    def _calculate_confidence(self, documents: list[dict]) -> float:
        if not documents:
            return 0.0

        scores = []
        for doc in documents:
            if "rerank_score" in doc:
                scores.append(doc["rerank_score"])
            elif "score" in doc:
                scores.append(doc["score"])

        if not scores:
            return 0.5

        avg_score = sum(scores) / len(scores)
        top_score = max(scores)
        confidence = 0.6 * top_score + 0.4 * avg_score
        return round(min(1.0, max(0.0, confidence)), 2)

    def _fallback_generate(self, query: str, documents: list[dict]) -> dict:
        """Fallback when Ollama is unavailable: extractive approach."""
        best_doc = documents[0] if documents else None
        if best_doc:
            metadata = best_doc.get("metadata", {})
            doc_name = metadata.get("document", "Unknown")
            page = metadata.get("page", "")
            citation = f" [Source: {doc_name}"
            if page and page != "":
                citation += f", Page {page}"
            citation += "]"

            return {
                "answer": f"Based on the documents found: {best_doc['text'][:500]}{citation}",
                "has_answer": True,
                "confidence": 0.4,
            }

        return {
            "answer": "I don't have enough information to answer this question.",
            "has_answer": False,
            "confidence": 0.0,
        }
