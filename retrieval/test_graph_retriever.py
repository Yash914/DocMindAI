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

from graph.graph_builder import KnowledgeGraph
from retrieval.graph_retriever import GraphRetriever


# ============================================================
# BUILD TEST GRAPH
# ============================================================

def build_test_graph():

    graph = KnowledgeGraph()

    # --------------------------------------------------------
    # Entities
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Facts
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Add all entities
    # --------------------------------------------------------

    graph.add_entities(
        entities
    )

    # --------------------------------------------------------
    # Add all facts
    # --------------------------------------------------------

    graph.add_facts(
        facts
    )

    return graph


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("GRAPH RETRIEVAL TEST")
    print("=" * 70)

    graph = build_test_graph()

    print(
        f"Nodes: {graph.graph.number_of_nodes()}"
    )

    print(
        f"Edges: {graph.graph.number_of_edges()}"
    )

    retriever = GraphRetriever(
        graph
    )

    # --------------------------------------------------------
    # QUESTIONS
    # --------------------------------------------------------

    questions = [

        "What standard does Cement conform to?",

        "How is Cement tested?",

        "What does Cement require?"
    ]

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    for question in questions:

        print("\n" + "-" * 70)

        print(
            f"QUESTION: {question}"
        )

        print("-" * 70)

        results = retriever.search(
            question
        )

        if not results:

            print(
                "No graph relationships found."
            )

            continue

        for i, result in enumerate(
            results,
            start=1
        ):

            print(
                f"\n{i}. "
                f"{result['subject']}"
                f" --{result['predicate']}--> "
                f"{result['object']}"
            )

            print(
                f"Evidence: "
                f"{result['evidence']}"
            )

            print(
                f"Source: "
                f"{result['document']} "
                f"| Page {result['page']} "
                f"| {result['chunk']}"
            )

    print("\n" + "=" * 70)
    print("GRAPH RETRIEVAL TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()