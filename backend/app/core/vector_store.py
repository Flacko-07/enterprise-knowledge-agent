"""
Vector store management using ChromaDB — fully local, no cloud dependencies.
"""
import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.core.embedding import EmbeddingEngine
from app.core.document_processor import Chunk

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """ChromaDB-backed vector store with custom embedding function."""

    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedding_engine = embedding_engine
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0

        ids = [chunk.id for chunk in chunks]
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.to_dict()["metadata"] for chunk in chunks]

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_engine.embed_texts(texts)

        # Ensure metadata values are proper types for ChromaDB
        for meta in metadatas:
            for key, value in meta.items():
                if value is None:
                    meta[key] = ""
                elif not isinstance(value, (str, int, float, bool)):
                    meta[key] = str(value)

        batch_size = 500
        added = 0
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i + batch_size],
                documents=texts[i:i + batch_size],
                embeddings=embeddings[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
            )
            added += min(batch_size, len(ids) - i)

        logger.info(f"Added {added} chunks to vector store")
        return added

    def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        top_k = top_k or settings.top_k
        query_embedding = self.embedding_engine.embed_query(query)

        where_filter = None
        if filter_metadata:
            conditions = [{k: {"$eq": v} for k, v in filter_metadata.items()}]
            if len(conditions) == 1:
                where_filter = conditions[0]
            elif len(conditions) > 1:
                where_filter = {"$and": conditions}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                similarity = 1 - distance
                formatted.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": similarity,
                })

        return formatted

    def get_collection_stats(self) -> dict:
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": settings.collection_name,
        }

    def reset(self):
        self.client.delete_collection(settings.collection_name)
        self.collection = self._get_or_create_collection()
        logger.info("Vector store reset complete")
