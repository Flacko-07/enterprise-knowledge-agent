"""
Query rewriting via local Ollama LLM.
Expands and reformulates user queries for better retrieval.
"""
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryRewriter:
    """Rewrites queries using Ollama LLM for improved retrieval."""

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_llm_model

    def rewrite(self, query: str, conversation_history: list[dict] = None) -> str:
        # Only rewrite if there's conversation history or the query is very short
        if not conversation_history and len(query.split()) > 4:
            return query

        prompt = self._build_rewrite_prompt(query, conversation_history)

        try:
            resp = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "num_predict": 200,
                    },
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            rewritten = resp.json().get("response", query).strip()
            # If the LLM returned something much longer than a query, truncate
            if len(rewritten) > 300:
                rewritten = rewritten.split("\n")[0].strip()
            if not rewritten:
                return query
            logger.info(f"Query rewritten: '{query}' → '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.warning(f"Query rewrite failed: {e}")
            return query

    def _build_rewrite_prompt(self, query: str, conversation_history: list[dict] = None) -> str:
        history_text = ""
        if conversation_history:
            history_text = "\nConversation history:\n"
            for msg in conversation_history[-4:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"

        return (
            f"You are a query rewriter for a document retrieval system.\n"
            f"Rewrite the user's question into a standalone, detailed search query "
            f"that will retrieve the most relevant documents.\n\n"
            f"Rules:\n"
            f"1. Resolve pronouns and references using conversation history\n"
            f"2. Expand abbreviations if context is clear\n"
            f"3. Add synonyms or related terms that might appear in documents\n"
            f"4. Make the query self-contained and specific\n"
            f"5. Return ONLY the rewritten query, nothing else\n"
            f"{history_text}\n"
            f"Original question: {query}\n\n"
            f"Rewritten query:"
        )
