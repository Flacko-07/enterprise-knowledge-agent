"""
Hybrid retrieval: semantic (vector) + keyword (BM25) with Reciprocal Rank Fusion.
"""
import logging
import math
from collections import defaultdict
from typing import Optional

from app.config import get_settings
from app.core.vector_store import VectorStore

logger = logging.getLogger(__name__)
settings = get_settings()


class BM25Retriever:
    """Simple BM25 keyword search over indexed document chunks."""

    def __init__(self):
        self.doc_texts: dict[str, str] = {}
        self.doc_metadata: dict[str, dict] = {}
        self.inverted_index: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.doc_lengths: dict[str, int] = {}
        self.avg_doc_length: float = 0
        self.k1 = 1.5
        self.b = 0.75

    def index_documents(self, documents: list[dict]):
        for doc in documents:
            doc_id = doc["id"]
            text = doc["text"]
            self.doc_texts[doc_id] = text
            self.doc_metadata[doc_id] = doc.get("metadata", {})
            tokens = text.lower().split()
            self.doc_lengths[doc_id] = len(tokens)
            for token in set(tokens):
                self.inverted_index[token][doc_id] = tokens.count(token)

        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)
        logger.info(f"BM25 index built: {len(self.doc_texts)} documents")

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_tokens = query.lower().split()
        scores = defaultdict(float)
        N = len(self.doc_texts)

        for token in query_tokens:
            if token not in self.inverted_index:
                continue
            doc_freq = len(self.inverted_index[token])
            idf = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
            for doc_id, term_freq in self.inverted_index[token].items():
                dl = self.doc_lengths[doc_id]
                tf_norm = (
                    (term_freq * (self.k1 + 1))
                    / (term_freq + self.k1 * (1 - self.b + self.b * dl / self.avg_doc_length))
                )
                scores[doc_id] += idf * tf_norm

        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for doc_id, score in sorted_docs:
            results.append({
                "id": doc_id,
                "text": self.doc_texts[doc_id],
                "metadata": self.doc_metadata[doc_id],
                "score": score,
            })
        return results


class HybridRetriever:
    """Hybrid retriever: semantic + BM25 via Reciprocal Rank Fusion."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.bm25 = BM25Retriever()
        self._bm25_initialized = False

    def initialize_bm25(self):
        try:
            all_docs = self.vector_store.collection.get(
                include=["documents", "metadatas"]
            )
            documents = []
            for i in range(len(all_docs["ids"])):
                documents.append({
                    "id": all_docs["ids"][i],
                    "text": all_docs["documents"][i],
                    "metadata": all_docs["metadatas"][i] if all_docs["metadatas"] else {},
                })
            self.bm25.index_documents(documents)
            self._bm25_initialized = True
            logger.info("BM25 index initialized from vector store")
        except Exception as e:
            logger.warning(f"Failed to initialize BM25: {e}")
            self._bm25_initialized = False

    def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[dict] = None,
        alpha: float = 0.7,
    ) -> list[dict]:
        top_k = top_k or settings.top_k
        rrf_k = 60

        semantic_results = self.vector_store.search(
            query, top_k=top_k * 2, filter_metadata=filter_metadata
        )

        keyword_results = []
        if self._bm25_initialized:
            keyword_results = self.bm25.search(query, top_k=top_k * 2)

        if not keyword_results:
            return semantic_results[:top_k]

        # Reciprocal Rank Fusion
        rrf_scores = defaultdict(float)
        doc_data = {}

        for rank, result in enumerate(semantic_results):
            doc_id = result["id"]
            rrf_scores[doc_id] += alpha * (1 / (rrf_k + rank + 1))
            doc_data[doc_id] = result

        for rank, result in enumerate(keyword_results):
            doc_id = result["id"]
            rrf_scores[doc_id] += (1 - alpha) * (1 / (rrf_k + rank + 1))
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_ids[0][1] if sorted_ids else 1

        results = []
        for doc_id, rrf_score in sorted_ids[:top_k]:
            result = doc_data[doc_id].copy()
            result["score"] = rrf_score / max_score
            results.append(result)

        return results
