"""RAG vs GraphRAG retrieval evaluation helpers.

Prepare a JSON case file with:
[
  {"question": "...", "expected_chunks": ["chunk_34"]}
]

These metrics evaluate retrieval against manually verified source chunks.
They do not claim answer correctness without human/ground-truth evaluation.
"""

import json
import time
from pathlib import Path


def load_cases(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def retrieval_metrics(retrieved_chunks, expected_chunks):
    retrieved = set(retrieved_chunks)
    expected = set(expected_chunks)
    hit = len(retrieved & expected)
    precision = hit / len(retrieved) if retrieved else 0.0
    recall = hit / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def evaluate_retriever(retriever, cases, top_k=6):
    rows = []
    for case in cases:
        start = time.perf_counter()
        result = retriever.search(case["question"])
        elapsed = time.perf_counter() - start
        retrieved = [
            x.get("chunk", "")
            for x in result.get("combined_evidence", [])[:top_k]
            if x.get("chunk")
        ]
        metrics = retrieval_metrics(retrieved, case.get("expected_chunks", []))
        rows.append({
            "question": case["question"],
            "retrieved_chunks": retrieved,
            "latency_seconds": round(elapsed, 4),
            **metrics,
        })
    return rows


def save_results(rows, path):
    Path(path).write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    print("Use evaluate_retriever() with a manually verified test set.")
