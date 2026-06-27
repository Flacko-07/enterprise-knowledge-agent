"""
Embedding generation — supports two fully-local backends:
  1. Ollama embedding API  (nomic-embed-text, mxbai-embed-large, etc.)
  2. Sentence Transformers  (all-MiniLM-L6-v2, etc.)

No cloud API keys required.
"""
import logging
import httpx
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OllamaEmbedding:
    """Embeddings via Ollama's /api/embeddings endpoint."""

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._dimension: Optional[int] = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for text in texts:
            embedding = self._embed_single(text)
            all_embeddings.append(embedding)
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._embed_single(text)

    def _embed_single(self, text: str) -> list[float]:
        try:
            resp = httpx.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data["embedding"]
            if self._dimension is None:
                self._dimension = len(embedding)
                logger.info(f"Ollama embedding dimension: {self._dimension}")
            return embedding
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            )
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            # Probe with a dummy text to discover dimension
            emb = self._embed_single("test")
            self._dimension = len(emb)
        return self._dimension


class SentenceTransformerEmbedding:
    """Embeddings via local Sentence Transformers (no server needed)."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, cache_folder=settings.transformers_cache)
        self.model_name = model_name
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"SentenceTransformer loaded: {model_name} (dim={self._dimension})")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=len(texts) > 100)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text], show_progress_bar=False)
        return embedding.tolist()[0]

    @property
    def dimension(self) -> int:
        return self._dimension


class EmbeddingEngine:
    """
    Unified embedding interface.
    Picks backend based on EMBEDDING_PROVIDER setting.
    """

    def __init__(self):
        self.model_name: str = ""
        self._dimension: int = 0
        self._engine = None
        self._initialize()

    def _initialize(self):
        provider = settings.embedding_provider.lower()

        if provider == "ollama":
            self._engine = OllamaEmbedding(
                model=settings.ollama_embedding_model,
                base_url=settings.ollama_base_url,
            )
            self.model_name = settings.ollama_embedding_model
            # Probe dimension lazily on first call
            logger.info(f"Embedding provider: Ollama ({self.model_name})")

        elif provider == "sentence_transformers":
            self._engine = SentenceTransformerEmbedding(
                model_name=settings.sentence_transformer_model,
            )
            self.model_name = settings.sentence_transformer_model
            self._dimension = self._engine.dimension
            logger.info(f"Embedding provider: SentenceTransformers ({self.model_name})")

        else:
            raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self._engine.embed_texts(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._engine.embed_query(text)

    @property
    def dimension(self) -> int:
        if self._dimension == 0:
            self._dimension = self._engine.dimension
        return self._dimension

    @property
    def is_ready(self) -> bool:
        return self._engine is not None
