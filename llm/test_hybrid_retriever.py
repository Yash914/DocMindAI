from pathlib import Path
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from retrieval.hybrid_retriever import HybridRetriever
from graph.graph_builder import KnowledgeGraph
from llm.llm_client import generate


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph():

    graph = KnowledgeGraph()

    entities = [
        {
            "name": "Cement",
            "type": "Material"
        },
        {
            "name": "IS:12269-1987",
            "type": "Standard"
        },
        {
            "name": "Test certificate",
            "type": "Document"
        },
        {
            "name": "Government approved laboratory",
            "type": "Organization"
        }
    ]

    facts = [
        {
            "subject": "Cement",
            "predicate": "CONFORMS_TO",
            "object": "IS:12269-1987",
            "document": "S-2_sr.pdf",
            "page": 5,
            "chunk": "chunk_10",
            "evidence":
                "Cement shall conform to IS:12269-1987."
        },
        {
            "subject": "Cement",
            "predicate": "REQUIRES",
            "object": "Test certificate",
            "document": "S-2_sr.pdf",
            "page": 5,
            "chunk": "chunk_10",
            "evidence":
                "Each consignment of cement shall be covered by a test certificate."
        },
        {
            "subject": "Cement",
            "predicate": "TESTED_AT",
            "object": "Government approved laboratory",
            "document": "S-2_sr.pdf",
            "page": 5,
            "chunk": "chunk_10",
            "evidence":
                "Cement shall be tested by an independent government approved laboratory."
        }
    ]

    graph.add_entities(entities)
    graph.add_facts(facts)

    return graph


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(question, results):

    context = []

    # --------------------------------------------------------
    # Vector evidence
    # --------------------------------------------------------

    for result in results["vector_results"]:

        chunk = result["document"]

        context.append(
            f"""
DOCUMENT EVIDENCE
Page: {chunk.get("page_number")}
Chunk: {chunk.get("chunk_id")}

{chunk.get("text", "")}
"""
        )

    # --------------------------------------------------------
    # Graph evidence
    # --------------------------------------------------------

    for result in results["graph_results"]:

        context.append(
            f"""
GRAPH EVIDENCE
{result["subject"]}
--{result["predicate"]}-->
{result["object"]}

Evidence: {result["evidence"]}
Source: {result.get("document", "")}
Page: {result.get("page", "")}
Chunk: {result.get("chunk", "")}
"""
        )

    joined_context = "\n".join(context)

    return f"""
You are DocMindAI, an intelligent technical-document
question answering system.

Answer the user's question ONLY using the supplied evidence.

Do not invent information.

If the evidence is insufficient, say:
"Insufficient evidence in the retrieved document."

Give a concise answer.

Include the relevant page/chunk as the source.

USER QUESTION:
{question}

RETRIEVED EVIDENCE:
{joined_context}

ANSWER:
"""


# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(
    retriever,
    question
):

    print("\n" + "=" * 70)
    print("QUESTION")
    print("=" * 70)

    print(question)

    # --------------------------------------------------------
    # Hybrid retrieval
    # --------------------------------------------------------

    results = retriever.search(
        question
    )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = build_prompt(
        question,
        results
    )

    # --------------------------------------------------------
    # Llama 3
    # --------------------------------------------------------

    answer = generate(
        prompt
    )

    print("\n" + "=" * 70)
    print("DOCMINDAI ANSWER")
    print("=" * 70)

    print(answer)

    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("RETRIEVED SOURCES")
    print("=" * 70)

    for result in results["vector_results"]:

        chunk = result["document"]

        print(
            f"Page {chunk.get('page_number')} "
            f"| {chunk.get('chunk_id')} "
            f"| Vector score: "
            f"{result['score']:.4f}"
        )

    for result in results["graph_results"]:

        print(
            f"Graph: "
            f"{result['subject']} "
            f"--{result['predicate']}--> "
            f"{result['object']} "
            f"| Page {result.get('page', '')}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("DOCMINDAI HYBRID GRAPH-RAG")
    print("=" * 70)

    graph = build_graph()

    retriever = HybridRetriever(
        graph,
        vector_top_k=3,
        graph_top_k=3
    )

    questions = [
        "What standard must cement conform to?",
        "How is cement tested?",
        "What does cement require?"
    ]

    for question in questions:

        ask_question(
            retriever,
            question
        )

    print("\n" + "=" * 70)
    print("DOCMINDAI TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()