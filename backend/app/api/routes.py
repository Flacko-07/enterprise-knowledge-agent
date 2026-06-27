import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.api.schemas import (
    AskRequest, AskResponse, SourceReference, ReasoningStep,
    IngestResponse, FeedbackRequest, FeedbackResponse, HealthResponse,
)
from app.core.rag_pipeline import RAGPipeline
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()
pipeline: RAGPipeline = None

def set_pipeline(p: RAGPipeline):
    global pipeline
    pipeline = p

@router.get("/health", response_model=HealthResponse)
async def health_check():
    stats = pipeline.get_stats()
    ollama_status = pipeline.check_ollama_status()
    return HealthResponse(
        status="healthy" if ollama_status["reachable"] else "degraded",
        version="1.0.0",
        documents_indexed=stats.get("total_chunks", 0),
        total_chunks=stats.get("total_chunks", 0),
        llm_ready=ollama_status["llm_ready"],
        embedding_ready=ollama_status["embedding_ready"],
        ollama_models=ollama_status.get("models", []),
    )

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        result = pipeline.ask(
            question=request.question,
            conversation_id=request.conversation_id,
        )
        sources = [
            SourceReference(
                document=s["document"], page=s.get("page"),
                section=s.get("section"), chunk_id=s.get("chunk_id"),
                relevance_score=s.get("relevance_score"),
            ) for s in result["sources"]
        ]
        reasoning = [
            ReasoningStep(
                iteration=s["iteration"], thought=s["thought"],
                action=s["action"], action_input=s["action_input"],
                observation=s["observation"]
            ) for s in result.get("reasoning_trace", [])
        ]

        return AskResponse(
            answer=result["answer"],
            sources=sources,
            confidence=result["confidence"],
            conversation_id=result["conversation_id"],
            requires_clarification=result.get("requires_clarification", False),
            clarification_question=result.get("clarification_question"),
            reasoning_trace=reasoning,
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents():
    try:
        result = pipeline.ingest_documents()
        return IngestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename: raise HTTPException(status_code=400, detail="No file provided")
    upload_dir = Path("./data/uploads"); upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    try:
        contents = await file.read()
        with open(file_path, "wb") as f: f.write(contents)
        chunks = pipeline.document_processor.process_document(str(file_path))
        pipeline.vector_store.add_chunks(chunks)
        pipeline.retriever.initialize_bm25()
        return {"status": "success", "filename": file.filename, "chunks_created": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    feedback_dir = Path("./data/feedback"); feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / f"feedback_{request.conversation_id}.jsonl"
    try:
        with open(feedback_file, "a") as f:
            f.write(json.dumps({**request.dict(), "comment": request.comment or ""}) + "\n")
        return FeedbackResponse(status="success", message="Feedback recorded!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))