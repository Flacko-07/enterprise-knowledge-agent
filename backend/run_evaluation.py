"""
Script to run the evaluation suite and print the report.
Automatically creates test cases if they don't exist.
Usage: python run_evaluation.py
"""
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from app.core.rag_pipeline import RAGPipeline
from app.evaluation.evaluator import RAGEvaluator

# Define default test cases
DEFAULT_TEST_CASES = [
  {
    "id": 1, "category": "factual",
    "question": "What is the employee leave policy?",
    "expected_keywords": ["24", "paid", "leaves", "casual", "sick"],
    "expected_sources": ["hr_policy.pdf"]
  },
  {
    "id": 2, "category": "factual",
    "question": "How do I request a refund?",
    "expected_keywords": ["30 days", "refund", "support"],
    "expected_sources": ["customer_faq.pdf"]
  },
  {
    "id": 3, "category": "factual",
    "question": "What are the minimum system requirements?",
    "expected_keywords": ["8 gb", "ram", "operating system"],
    "expected_sources": ["product_docs.pdf"]
  },
  {
    "id": 4, "category": "multi_hop",
    "question": "What is the deployment process and what are the deployment windows?",
    "expected_keywords": ["argo", "feature branch", "tuesday", "thursday"],
    "expected_sources": ["tech_guide.pdf"]
  },
  {
    "id": 5, "category": "ambiguous",
    "question": "What is the policy?",
    "expected_keywords": [],
    "expected_sources": [],
    "expected_behavior": "clarify"
  },
  {
    "id": 6, "category": "out_of_scope",
    "question": "Who won the soccer world cup in 2022?",
    "expected_keywords": [],
    "expected_sources": [],
    "expected_behavior": "no_hallucination"
  },
  {
    "id": 7, "category": "chitchat",
    "question": "Hello, how are you?",
    "expected_keywords": ["help", "assist", "hello"],
    "expected_sources": [],
    "expected_behavior": "conversational"
  }
]

def main():
    # Ensure test cases file exists automatically
    eval_dir = Path("./data/eval")
    eval_dir.mkdir(parents=True, exist_ok=True)
    test_cases_path = eval_dir / "test_cases.json"
    
    if not test_cases_path.exists():
        print("Creating default test cases in ./data/eval/test_cases.json...")
        with open(test_cases_path, "w") as f:
            json.dump(DEFAULT_TEST_CASES, f, indent=2)

    print("="*60)
    print("INITIALIZING RAG PIPELINE FOR EVALUATION...")
    print("="*60)
    
    pipeline = RAGPipeline()
    pipeline.initialize()
    
    print("\nSTARTING EVALUATION...\n")
    evaluator = RAGEvaluator(pipeline)
    
    # FIXED: This must be evaluate() with no arguments, NOT evaluate(results)
    results = evaluator.evaluate() 
    
    report = evaluator.generate_report(results)
    
    print("\n" + "="*60)
    print("EVALUATION REPORT")
    print("="*60)
    print(json.dumps(report, indent=2))
    
    # Save detailed results to file
    evaluator.save_results(results, report)
    print("\nDetailed results saved to ./data/eval/results.json")

if __name__ == "__main__":
    main()