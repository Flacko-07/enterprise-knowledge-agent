.PHONY: help setup run dev test clean ingest pull-models ollama-check eval

help: ## Show help
    @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
    cd backend && pip install -r requirements.txt
    cd frontend && npm install
    cd backend && python create_sample_docs.py

pull-models: ## Pull required Ollama models
    @echo "Pulling Ollama models (this may take a while on first run)..."
    ollama pull llama3.1
    ollama pull nomic-embed-text
    @echo "✅ Models ready!"

ollama-check: ## Check Ollama status
    @curl -s http://localhost:11434/api/tags | python -m json.tool || echo "❌ Ollama not running. Start with: ollama serve"

run: ## Run all services via Docker (includes Ollama)
    docker-compose up --build

dev: ## Run in development mode (assumes Ollama is already running)
    @echo "Make sure Ollama is running: ollama serve"
    @echo "Starting backend..."
    @cd backend && uvicorn app.main:app --reload --port 8000 &
    @echo "Starting frontend..."
    @cd frontend && npm run dev

ingest: ## Run document ingestion
    cd backend && python ingest.py

test: ## Run tests
    cd backend && python -m pytest tests/ -v

clean: ## Clean up generated files
    rm -rf backend/vector_db backend/__pycache__ backend/**/__pycache__
    rm -rf frontend/.next frontend/node_modules

eval: ## Run evaluation
    cd backend && python -c "\
from app.core.rag_pipeline import RAGPipeline; \
from app.evaluation.evaluator import RAGEvaluator; \
p = RAGPipeline(); p.initialize(); \
e = RAGEvaluator(p); r = e.evaluate(); \
report = e.generate_report(r); \
print('\n=== Evaluation Report ==='); \
import json; print(json.dumps(report, indent=2)); \
e.save_results(r)"

create-docs: ## Create sample PDF documents
    cd backend && python create_sample_docs.py
