"""
FastAPI application entry point — configured for fully local Ollama stack.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import router, set_pipeline
from app.core.rag_pipeline import RAGPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    logger.info("=" * 60)
    logger.info("Starting Enterprise Knowledge Assistant (Ollama - Local)")
    logger.info("=" * 60)

    # Initialize RAG pipeline
    pipeline = RAGPipeline()

    # Check Ollama connectivity
    ollama_status = pipeline.check_ollama_status()
    if ollama_status["reachable"]:
        logger.info(f"Ollama reachable. Models: {ollama_status['models']}")
    else:
        logger.warning(
            f"Ollama NOT reachable at {settings.ollama_base_url}. "
            "Make sure 'ollama serve' is running!"
        )

    pipeline.initialize()
    set_pipeline(pipeline)

    # Auto-ingest if vector store is empty
    stats = pipeline.get_stats()
    if stats["total_chunks"] == 0:
        logger.info("Vector store is empty, auto-ingesting documents...")
        result = pipeline.ingest_documents()
        logger.info(f"Auto-ingestion result: {result}")

    logger.info("Application ready!")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="AI-powered RAG system — fully local with Ollama",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["Knowledge Assistant"])


@app.get("/")
async def root():
    return {
        "name": "Enterprise Knowledge Assistant",
        "version": "1.0.0",
        "backend": "Ollama (Local)",
        "docs": "/docs",
    }
