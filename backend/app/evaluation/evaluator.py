"""
Evaluation Framework for the Agentic RAG Pipeline.
Measures: Relevance, Source Accuracy, Ambiguity Handling, Hallucination Rate, and Latency.
"""
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.core.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    id: int
    category: str
    question: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_sources: list[str] = field(default_factory=list)
    expected_behavior: Optional[str] = None  # "clarify", "no_hallucination", "conversational"

@dataclass
class EvalResult:
    id: int
    category: str
    question: str
    generated_answer: str
    latency_ms: float
    keyword_coverage: float
    source_accuracy: float
    behavior_correct: bool
    has_answer: bool
    confidence: float
    requires_clarification: bool

class RAGEvaluator:
    def __init__(self, pipeline: RAGPipeline, test_cases_path: str = "./data/eval/test_cases.json"):
        self.pipeline = pipeline
        self.test_cases_path = test_cases_path
        self.test_cases = self._load_test_cases()

    def _load_test_cases(self) -> list[TestCase]:
        path = Path(self.test_cases_path)
        if not path.exists():
            logger.error(f"Test cases file not found at {self.test_cases_path}")
            return []
        with open(path, "r") as f:
            data = json.load(f)
        return [TestCase(**tc) for tc in data]

    def evaluate(self) -> list[EvalResult]:
        results = []
        for tc in self.test_cases:
            logger.info(f"Evaluating Q{tc.id} [{tc.category}]: {tc.question}")
            
            start_time = time.time()
            response = self.pipeline.ask(tc.question)
            latency = (time.time() - start_time) * 1000

            # 1. Keyword Coverage (Relevance proxy)
            keyword_coverage = 0.0
            if tc.expected_keywords:
                answer_lower = response["answer"].lower()
                found = sum(1 for kw in tc.expected_keywords if kw.lower() in answer_lower)
                keyword_coverage = round(found / len(tc.expected_keywords), 2)
            else:
                keyword_coverage = 1.0 # No keywords expected

            # 2. Source Accuracy (Retrieval Quality)
            source_accuracy = 0.0
            if tc.expected_sources:
                retrieved_docs = [s["document"].lower() for s in response["sources"]]
                found = sum(1 for exp in tc.expected_sources if any(exp.lower() in doc for doc in retrieved_docs))
                source_accuracy = round(found / len(tc.expected_sources), 2)
            else:
                source_accuracy = 1.0 # No sources expected

            # 3. Behavior Correctness (Ambiguity / OOS / Chitchat)
            behavior_correct = False
            has_answer = "don't have enough information" not in response["answer"].lower() and response["answer"].strip() not in ["", "{}"]

            if tc.expected_behavior == "clarify":
                behavior_correct = response.get("requires_clarification", False)
            elif tc.expected_behavior == "no_hallucination":
                behavior_correct = not has_answer or "world cup" not in response["answer"].lower()
            elif tc.expected_behavior == "conversational":
                behavior_correct = has_answer and not response.get("requires_clarification", False) and len(response["sources"]) == 0
            else:
                behavior_correct = has_answer

            results.append(EvalResult(
                id=tc.id,
                category=tc.category,
                question=tc.question,
                generated_answer=response["answer"],
                latency_ms=round(latency, 2),
                keyword_coverage=keyword_coverage,
                source_accuracy=source_accuracy,
                behavior_correct=behavior_correct,
                has_answer=has_answer,
                confidence=response["confidence"],
                requires_clarification=response.get("requires_clarification", False)
            ))
        return results

    def generate_report(self, results: list[EvalResult]) -> dict:
        if not results: return {}
        n = len(results)
        
        factual_results = [r for r in results if r.category in ["factual", "multi_hop"]]
        
        avg_keyword = sum(r.keyword_coverage for r in factual_results) / max(1, len(factual_results))
        avg_source = sum(r.source_accuracy for r in factual_results) / max(1, len(factual_results))
        avg_latency = sum(r.latency_ms for r in results) / n
        
        ambiguity_handled = sum(1 for r in results if r.category == "ambiguous" and r.behavior_correct) / max(1, len([r for r in results if r.category == "ambiguous"]))
        oos_handled = sum(1 for r in results if r.category == "out_of_scope" and r.behavior_correct) / max(1, len([r for r in results if r.category == "out_of_scope"]))
        chitchat_handled = sum(1 for r in results if r.category == "chitchat" and r.behavior_correct) / max(1, len([r for r in results if r.category == "chitchat"]))

        return {
            "total_questions": n,
            "avg_keyword_coverage_factual": round(avg_keyword, 2),
            "avg_source_accuracy_factual": round(avg_source, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "ambiguity_handling_rate": round(ambiguity_handled, 2),
            "out_of_scope_rejection_rate": round(oos_handled, 2),
            "chitchat_handling_rate": round(chitchat_handled, 2)
        }

    def save_results(self, results: list[EvalResult], report: dict, path: str = "./data/eval/results.json"):
        out_dir = Path(path).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "summary": report,
            "results": [asdict(r) for r in results]
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Evaluation results saved to {path}")