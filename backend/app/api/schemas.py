from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None

class SourceReference(BaseModel):
    document: str
    page: Optional[int] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    relevance_score: Optional[float] = None

class ReasoningStep(BaseModel):
    iteration: int
    thought: str = ""
    action: str
    action_input: str
    observation: str = ""

class AskResponse(BaseModel):
    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    conversation_id: str
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    reasoning_trace: list[ReasoningStep] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
    errors: list[str] = Field(default_factory=list)

class FeedbackRequest(BaseModel):
    conversation_id: str
    question: str
    answer: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str
    documents_indexed: int
    total_chunks: int
    llm_ready: bool
    embedding_ready: bool
    ollama_models: list[str] = Field(default_factory=list)