from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    # Embeddings
    embedding_provider: str = "ollama"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 768

    # Vector Store & Chunking
    vector_db_path: str = "./vector_db"
    collection_name: str = "enterprise_docs"
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Retrieval
    top_k: int = 5
    rerank_top_k: int = 3
    similarity_threshold: float = 0.3

    # Agent & LLM Generation (FIXED MISSING ATTRIBUTES)
    agent_max_iterations: int = 5
    agent_temperature: float = 0.1
    llm_temperature: float = 0.1
    llm_num_ctx: int = 4096          # <-- ADDED BACK
    llm_num_predict: int = 1024      # <-- ADDED BACK

    # Reranker
    reranker_type: str = "cross_encoder"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"
    app_name: str = "Enterprise Knowledge Assistant"
    debug: bool = False
    transformers_cache: str = "./models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

@lru_cache()
def get_settings() -> Settings:
    return Settings()