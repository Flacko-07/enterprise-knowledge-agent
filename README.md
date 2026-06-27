# Enterprise Knowledge Assistant 🤖

An AI-powered Agentic RAG system that enables employees to ask questions in natural language and receive accurate, sourced answers from internal company documents. Built with a fully local stack using Ollama (Llama 3.2 3B) — **zero cloud API keys required, 100% private.**

![Architecture](https://img.shields.io/badge/Architecture-Agentic%20RAG-blue) ![Model](https://img.shields.io/badge/Model-Llama%203.2%203B-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Bonus Features Implemented

We have implemented all major bonus features to demonstrate production-level engineering:

- [x] **Conversation Memory**: In-memory conversation history passed to the agent for contextual follow-up questions.
- [x] **Hybrid Search (Keyword + Semantic)**: Combines ChromaDB vector search with BM25 keyword search using Reciprocal Rank Fusion (RRF).
- [x] **Query Rewriting**: Ollama rewrites ambiguous/short user queries into detailed search queries.
- [x] **Re-ranking**: Cross-Encoder (or Ollama LLM fallback) re-ranks retrieved documents for higher precision.
- [x] **Multi-document Reasoning**: The agent autonomously performs multiple searches across different documents and synthesizes the answer.
- [x] **User Feedback Collection**: 👍/👎 feedback UI that writes to a persistent JSONL file via the `/feedback` API.
- [x] **Evaluation Metrics**: A comprehensive, deterministic evaluation framework (`run_evaluation.py`) measuring Keyword Coverage, Source Accuracy, Ambiguity Handling, and Hallucination Rejection.
- [x] **Deployment**: Dockerized for local deployment, Frontend configured for Vercel, with documented cloud scaling strategies.

---

## 🏛️ Architecture Overview

The system uses an **Agentic RAG architecture** with native Ollama Tool Calling. Instead of a rigid pipeline, the LLM acts as an autonomous agent that reasons, searches, and synthesizes.

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js    │────▶│   FastAPI Backend │────▶│   ChromaDB      │
│   Frontend   │◀────│   (RAG Agent)     │◀────│   Vector Store  │
└─────────────┘     │                  │     └─────────────────┘
                    │  ┌────────────┐  │     ┌─────────────────┐
                    │  │ Ollama     │  │────▶│   Ollama        │
                    │  │ Tool Caller│  │     │   (Local LLM)   │
                    │  └─────┬──────┘  │     │  llama3.2:3b    │
                    │        │         │     │  nomic-embed    │
                    │  ┌─────▼──────┐  │     └─────────────────┘
                    │  │ Hybrid     │  │     ┌─────────────────┐
                    │  │ Retriever  │  │────▶│ Cross-Encoder   │
                    │  └─────┬──────┘  │     │ (Re-ranker)     │
                    │        ▼         │     └─────────────────┘
                    │  ┌────────────┐  │
                    │  │ Response   │  │
                    │  │ Generator  │  │
                    │  └────────────┘  │
                    └──────────────────┘
```

### Data Flow (The Agentic Loop)
1.  **User Input**: User asks a question via the Next.js UI.
2.  **Agent Reasoning**: The LLM evaluates if it needs to search, clarify, or answer directly.
3.  **Tool Execution**: If `search_knowledge_base` is called, Hybrid Retrieval (BM25 + Semantic) is triggered.
4.  **Re-ranking**: Results are re-ranked locally for precision.
5.  **Synthesis**: The LLM generates a concise, cited answer strictly from the retrieved context.
6.  **Fallback**: If the user engages in small talk, a separate conversational fallback safely handles it without triggering document searches.

---

## 🛠️ Setup & Running Locally

### Prerequisites
- Python 3.11+
- Node.js 20+
- Ollama installed and running

### 1. Install & Start Ollama
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Start the server
ollama serve

# In a new terminal, pull the required models
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 2. Backend Setup
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt

# Generate sample enterprise PDFs
python create_sample_docs.py
```

### 3. Start the Application

**Option A: Development Mode (Recommended for Demo)**
```bash
# Start backend (from backend/)
uvicorn app.main:app --reload --port 8000

# Start frontend (from frontend/)
npm install
npm run dev
```

**Option B: Docker Compose (Includes Ollama container)**
```bash
docker-compose up --build
```
Access the app at `http://localhost:3000`.

---

## 💻 Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|----------|
| **LLM** | Ollama (llama3.2:3b) | Fully local, private, zero API cost, robust tool-calling support. |
| **Embeddings** | Ollama (nomic-embed-text) | 768-dim, high quality, runs alongside LLM locally. |
| **Backend** | FastAPI | Async, type-safe, automatic OpenAPI docs, production-ready. |
| **Frontend** | Next.js 14 | Server-side rendering, Vercel-compatible, modern React. |
| **Vector DB** | ChromaDB | Lightweight, persistent, local, metadata filtering. |
| **Re-ranker** | Cross-Encoder (ms-marco-MiniLM) | Fast local re-ranking to boost retrieval precision. |

---

## 🧠 Design Decisions

### 1. Why Agentic RAG over Pipeline RAG?
A standard pipeline (`Retrieve → Generate`) forces the system to search even for small talk and cannot handle ambiguity. The Agentic architecture allows the 3B model to autonomously decide *whether* to search, *how* to search, and *when* to ask for clarification, mimicking human reasoning.

### 2. Robust Fallback for 3B Models
Small models struggle when tool definitions are present but not needed (e.g., for "Hello"). We implemented a **two-tier fallback**: if the agent returns an empty response while tools are active, we automatically strip the tools and re-prompt the LLM in pure conversational mode.

### 3. Strict Hallucination Prevention
The system prompt enforces a "grounding-only" rule. The agent is explicitly told it has no general knowledge and must use a specific refusal phrase if the database returns no results, achieving a **100% Out-of-Scope Rejection Rate** in evaluations.

### 4. Hybrid Search + Re-ranking
Semantic search misses exact keywords (e.g., specific policy codes); BM25 misses semantic meaning. We combine them using Reciprocal Rank Fusion (α=0.7) and re-rank the top results with a local Cross-Encoder for the best of both worlds.

---

## 📊 Evaluation Approach

We built a deterministic evaluation framework (`run_evaluation.py`) to measure performance without relying on unreliable LLM-as-a-judge methods.

**Latest Results:**
- **Keyword Coverage**: 92% (Factual accuracy)
- **Source Accuracy**: 100% (Correct documents retrieved)
- **Ambiguity Handling**: 100% (Correctly asked for clarification)
- **Out-of-Scope Rejection**: 100% (Zero hallucinations)
- **Chitchat Handling**: 100% (Correctly routed to conversational fallback)

*See `EVALUATION.md` for the detailed methodology and iteration history.*

---

## ⚠️ Limitations

1.  **Local LLM Quality**: While robust, a 3B model occasionally struggles with complex multi-hop logic compared to GPT-4.
2.  **No Authentication**: The API is currently open. Production would require JWT/OAuth2.
3.  **In-Memory Conversation Store**: History is lost on backend restart (would use Redis/DB in production).
4.  **English Only**: Currently supports English documents.

---

## 🔮 Future Improvements

While the current system is robust and fully functional, the following improvements would be required to scale it to a production enterprise environment:

- **Persistent Conversation Store**: Move the in-memory conversation dictionary to Redis or Postgres so that user history survives backend restarts and can scale across multiple backend instances.
- **Authentication & RBAC**: Implement JWT-based authentication and Role-Based Access Control (e.g., HR can only query HR documents) to secure the API and ensure document compliance.
- **Streaming Responses**: Implement Server-Sent Events (SSE) to stream the agent's final answer token-by-token to the frontend, significantly improving perceived latency.
- **Distributed Vector Database**: Migrate from local ChromaDB to a managed, scalable vector database like Pinecone, Weaviate, or Supabase pgvector for high-availability and larger document corpora.
- **Multi-modal Parsing**: Integrate OCR and vision models (e.g., Llama 3.2 Vision) to extract information from tables, charts, and images currently ignored by standard PDF text extractors.

---

## 🚀 Deployment Strategy

While this application is designed to run fully locally for privacy, it can be deployed to the cloud for organization-wide access. Because local LLMs require significant compute, the deployment strategy differs from standard web apps.

### Option 1: Dockerized VM Deployment (Recommended for Local LLMs)
The entire stack (Ollama + FastAPI + ChromaDB) can be deployed on a single Virtual Machine with a GPU (e.g., AWS EC2 `g4dn` instances, RunPod, or Lambda Labs).

1.  **Setup**: Install Docker on the VM.
2.  **Deploy**: Use the provided `docker-compose.yml` to launch all services.
3.  **Network**: Expose the FastAPI port (8000) and Ollama port (11434) via Nginx with SSL.
4.  **Frontend**: Deploy the Next.js app to **Vercel**, setting `NEXT_PUBLIC_API_URL` to the VM's public IP/Domain.

### Option 2: Managed LLM + Supabase (Cloud-Native)
If local inference is not a strict requirement, the architecture can be easily swapped to cloud services:
1.  **LLM**: Swap the Ollama backend to Groq (OpenAI-compatible, blazing fast) or OpenAI API.
2.  **Vector DB**: Migrate ChromaDB to **Supabase** using `pgvector` for scalable, persistent storage.
3.  **Backend**: Deploy FastAPI to **Render** or **Railway**.
4.  **Frontend**: Deploy Next.js to **Vercel**.

---

## 📄 License

MIT
