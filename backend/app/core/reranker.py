"""
Re-ranking module — all local, no cloud APIs.
Two options:
  1. Cross-encoder (sentence-transformers) — fast, accurate
  2. LLM-based via Ollama — slower, but no extra model download
"""
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CrossEncoderReranker:
    """Re-rank using a local cross-encoder model (sentence-transformers)."""

    def __init__(self, model_name: str = None):
        model_name = model_name or settings.cross_encoder_model
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name, cache_folder=settings.transformers_cache)
            self.available = True
            logger.info(f"Cross-encoder reranker loaded: {model_name}")
        except Exception as e:
            self.model = None
            self.available = False
            logger.warning(f"Cross-encoder unavailable ({e}), reranking will use fallback")

    def rerank(self, query: str, documents: list[dict], top_k: int = None) -> list[dict]:
        top_k = top_k or settings.rerank_top_k
        if not self.available or not documents:
            return documents[:top_k]

        pairs = [(query, doc["text"][:512]) for doc in documents]
        scores = self.model.predict(pairs)

        scored_docs = list(zip(scores, documents))
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        max_s = scored_docs[0][0] if scored_docs else 1
        min_s = scored_docs[-1][0] if scored_docs else 0
        rng = max_s - min_s if max_s != min_s else 1

        results = []
        for score, doc in scored_docs[:top_k]:
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = (score - min_s) / rng
            results.append(doc_copy)
        return results


class OllamaReranker:
    """Re-rank using Ollama LLM to score document relevance."""

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_llm_model

    def rerank(self, query: str, documents: list[dict], top_k: int = None) -> list[dict]:
        top_k = top_k or settings.rerank_top_k
        if not documents:
            return []

        scored_docs = []
        for doc in documents:
            score = self._score_relevance(query, doc["text"])
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = score
            scored_docs.append((score, doc_copy))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]

    def _score_relevance(self, query: str, document: str) -> float:
        truncated = document[:500]
        prompt = (
            f"Rate the relevance of the following document to the query on a scale of 0 to 1.\n"
            f"Return ONLY a single number between 0 and 1 (e.g., 0.85).\n\n"
            f"Query: {query}\n\nDocument: {truncated}\n\nRelevance score:"
        )

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": 10},
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "0.5").strip()
            # Extract first number from response
            for token in text.split():
                try:
                    score = float(token)
                    return max(0.0, min(1.0, score))
                except ValueError:
                    continue
            return 0.5
        except Exception as e:
            logger.warning(f"Ollama rerank scoring failed: {e}")
            return 0.5


class NoOpReranker:
    """Pass-through reranker when reranking is disabled."""

    def rerank(self, query: str, documents: list[dict], top_k: int = None) -> list[dict]:
        top_k = top_k or settings.rerank_top_k
        return documents[:top_k]


def create_reranker():
    """Factory: pick reranker based on settings."""
    rtype = settings.reranker_type.lower()
    if rtype == "cross_encoder":
        reranker = CrossEncoderReranker()
        if reranker.available:
            return reranker
        logger.warning("Cross-encoder not available, falling back to LLM reranker")
        return OllamaReranker()
    elif rtype == "llm":
        return OllamaReranker()
    else:
        return NoOpReranker()
