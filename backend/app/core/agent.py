"""
Agentic RAG Core - Robust version for Llama 3.2 3B.
Includes fallback for small talk when tool-calling confuses the model.
"""
import logging
import httpx
import re
from typing import Optional
from dataclasses import dataclass, field

from app.config import get_settings
from app.core.retriever import HybridRetriever
from app.core.reranker import create_reranker

logger = logging.getLogger(__name__)
settings = get_settings()

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the company's internal documents for specific information, policies, or technical details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A detailed search query to find relevant documents."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clarify_with_user",
            "description": "Ask the user to specify which document or policy they mean ONLY if they asked a document-related question that is severely ambiguous (e.g., 'What is the policy?' without saying which one).",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The clarifying question to ask the user."
                    }
                },
                "required": ["question"]
            }
        }
    }
]

@dataclass
class AgentStep:
    iteration: int
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""

class RAGAgent:
        # "Goldilocks" Prompt - Strict on hallucination, confident on context
    SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Your job is to answer questions about company documents.

TOOLS:
- Use `search_knowledge_base` when the user asks about company policies, HR, tech, or documents.
- Use `clarify_with_user` ONLY if the user asks a vague question like "What is the policy?" without specifying which one.
- If the user is making small talk (e.g., "hi", "hello"), DO NOT use any tools. Just respond naturally.

HOW TO ANSWER:
1. If you use the search tool, carefully read the search results provided in the Observation.
2. IF the search results contain the answer, write a confident, detailed answer using ONLY the information from the search results. Cite your sources using [Source: DocumentName, Page X].
3. IF the search results are empty, OR the user asks about sports, current events, or general knowledge NOT related to the company, you MUST respond with EXACTLY: "I don't have enough information to answer this question based on the available documents."

NEVER use your internal training data to answer questions. You ONLY know what is in the search results."""
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.reranker = create_reranker()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_llm_model
        self.max_iterations = settings.agent_max_iterations
        self._collected_documents: list[dict] = []

    def run(
        self,
        question: str,
        conversation_history: list[dict] = None,
    ) -> dict:
        self._collected_documents = []
        reasoning_trace: list[AgentStep] = []

        system_msg = {
            "role": "system",
            "content": self.SYSTEM_PROMPT
        }
        
        messages = [system_msg]
        if conversation_history:
            messages.extend(conversation_history[-4:])
        messages.append({"role": "user", "content": question})

        for iteration in range(self.max_iterations):
            logger.info(f"Agent iteration {iteration + 1}/{self.max_iterations}")
            
            llm_response = self._call_llm(messages, tools=AGENT_TOOLS)

            if not llm_response:
                return self._format_result(
                    "I encountered an error processing your request.",
                    reasoning_trace, 0.0
                )

            assistant_message = llm_response.get("message", {})
            
            # Clean up any leaked prompt text
            if "content" in assistant_message:
                assistant_message["content"] = self._clean_text(assistant_message["content"])

            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls", [])
            content = assistant_message.get("content", "").strip()

            # --- ROBUSTNESS FIX ---
            # If the model didn't call a tool, but also returned empty text or '{}', 
            # it means it got confused by the tool definitions when trying to make small talk.
            # We fallback to a standard LLM call WITHOUT tools.
            if not tool_calls and (not content or content == "{}"):
                logger.info("Model returned empty text with tools active. Falling back to conversational mode...")
                fallback_answer = self._generate_conversational_response(question, conversation_history)
                return self._format_result(fallback_answer, reasoning_trace, 0.0)

            # Normal final answer path (no tools, valid text)
            if not tool_calls:
                return self._format_result(content, reasoning_trace, self._calculate_confidence())

            # Tool execution path
            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                action_name = func.get("name", "")
                
                try:
                    import json
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                except Exception:
                    args = {}

                step = AgentStep(iteration=iteration + 1, action=action_name)

                if action_name == "search_knowledge_base":
                    query = args.get("query", question)
                    step.action_input = query
                    observation = self._execute_search(query)
                    step.observation = "Found relevant documents." if "No relevant" not in observation else "No documents found."
                    messages.append({
                        "role": "tool",
                        "name": action_name,
                        "content": observation
                    })

                elif action_name == "clarify_with_user":
                    clarifying_q = args.get("question", "Could you please clarify?")
                    step.action_input = clarifying_q
                    return {
                        "answer": "I need more information to help you.",
                        "sources": [],
                        "confidence": 0.0,
                        "reasoning_trace": [self._step_to_dict(step) for step in reasoning_trace] + [self._step_to_dict(step)],
                        "requires_clarification": True,
                        "clarification_question": self._clean_text(clarifying_q),
                    }
                else:
                    step.observation = f"Error: Unknown tool {action_name}"
                    messages.append({
                        "role": "tool",
                        "name": action_name,
                        "content": step.observation
                    })
                
                reasoning_trace.append(step)

        return self._format_result(
            "I searched the documents but couldn't find a complete answer. Please try rephrasing.",
            reasoning_trace, 0.3
        )

    def _call_llm(self, messages: list[dict], tools: list[dict] = None) -> Optional[dict]:
        """Call Ollama /api/chat. Tools are optional."""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": settings.agent_temperature,
                    "num_ctx": settings.llm_num_ctx,
                }
            }
            if tools:
                payload["tools"] = tools

            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Ollama Agent call failed: {e}")
            return None

    def _generate_conversational_response(self, question: str, conversation_history: list[dict] = None) -> str:
        """Fallback: Ask the model to respond conversationally WITHOUT tools."""
        try:
            fallback_msg = {
                "role": "system",
                "content": "You are a friendly Enterprise Knowledge Assistant. Respond politely and briefly to the user's greeting or small talk, and remind them you can help search company documents if they have questions."
            }
            messages = [fallback_msg]
            if conversation_history:
                messages.extend(conversation_history[-4:])
            messages.append({"role": "user", "content": question})
            
            # _call_llm without tools parameter
            data = self._call_llm(messages, tools=None)
            if data:
                answer = data.get("message", {}).get("content", "").strip()
                return self._clean_text(answer)
            return "Hello! I am here to help you with questions about your company documents. What would you like to know?"
        except Exception as e:
            logger.error(f"Fallback conversational call failed: {e}")
            return "Hello! I am here to help you with questions about your company documents. What would you like to know?"

    def _execute_search(self, query: str) -> str:
        retrieved_docs = self.retriever.search(query, top_k=settings.top_k)
        
        if retrieved_docs and len(retrieved_docs) > 1:
            filtered_docs = [d for d in retrieved_docs if d.get("score", 0) >= settings.similarity_threshold]
            if not filtered_docs: filtered_docs = retrieved_docs[:3]
            reranked_docs = self.reranker.rerank(query, filtered_docs, top_k=settings.rerank_top_k)
        else:
            reranked_docs = retrieved_docs

        for doc in reranked_docs:
            if doc["id"] not in [d["id"] for d in self._collected_documents]:
                self._collected_documents.append(doc)

        if not reranked_docs:
            return "No relevant documents found for this query."

        obs_parts = []
        for i, doc in enumerate(reranked_docs, 1):
            metadata = doc.get("metadata", {})
            doc_name = metadata.get("document", "Unknown")
            page = metadata.get("page", "")
            page_str = f", Page {page}" if page and page != "" else ""
            obs_parts.append(f"[{i}] (Source: {doc_name}{page_str})\n{doc['text']}")
        
        return "\n\n---\n\n".join(obs_parts)

    def _clean_text(self, text: str) -> str:
        """Remove leaked Ollama system prompt instructions from the model output."""
        if not text:
            return text
        if "Given the following functions" in text:
            text = re.sub(r"Given the following functions.*?best answers the given prompt\.\s*", "", text, flags=re.DOTALL).strip()
        return text

    def _calculate_confidence(self) -> float:
        if not self._collected_documents:
            return 0.0
        scores = [d.get("rerank_score", d.get("score", 0)) for d in self._collected_documents]
        return round(min(1.0, max(scores)), 2) if scores else 0.0

    def _format_result(self, answer: str, trace: list[AgentStep], confidence: float) -> dict:
        sources = []
        seen = set()
        for doc in self._collected_documents:
            metadata = doc.get("metadata", {})
            source_key = f"{metadata.get('document', '')}-{metadata.get('page', '')}"
            if source_key not in seen:
                seen.add(source_key)
                page_val = metadata.get("page")
                sources.append({
                    "document": metadata.get("document", "Unknown"),
                    "page": int(page_val) if page_val and page_val != "" else None,
                    "section": metadata.get("section") or None,
                    "chunk_id": doc.get("id"),
                    "relevance_score": doc.get("rerank_score") or doc.get("score"),
                })

        return {
            "answer": self._clean_text(answer),
            "sources": sources,
            "confidence": confidence,
            "reasoning_trace": [self._step_to_dict(s) for s in trace],
            "requires_clarification": False,
            "clarification_question": None,
        }

    def _step_to_dict(self, step: AgentStep) -> dict:
        return {
            "iteration": step.iteration,
            "thought": self._clean_text(step.thought),
            "action": step.action,
            "action_input": self._clean_text(step.action_input),
            "observation": step.observation[:200] + "..." if len(step.observation) > 200 else step.observation
        }