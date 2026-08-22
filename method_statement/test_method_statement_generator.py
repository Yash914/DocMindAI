from pathlib import Path
import sys
import json


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
from retrieval.hybrid_retriever import HybridRetriever

from method_statement.method_statement_generator import (
    generate_method_statement
)


# ============================================================
# BUILD SMALL TEST GRAPH
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
            "object":
                "Government approved laboratory",
            "document": "S-2_sr.pdf",
            "page": 5,
            "chunk": "chunk_10",
            "evidence":
                "Cement shall be tested by an independent government approved laboratory."
        }
    ]

    graph.add_entities(
        entities
    )

    graph.add_facts(
        facts
    )

    return graph


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_method_statement(data):

    statement = data.get(
        "method_statement",
        {}
    )

    print()
    print("=" * 70)
    print("METHOD STATEMENT EXTRACTION RESULT")
    print("=" * 70)

    sections = [

        (
            "PURPOSE",
            "purpose"
        ),

        (
            "SCOPE",
            "scope"
        ),

        (
            "ACRONYMS AND DEFINITIONS",
            "acronyms_and_definitions"
        ),

        (
            "REFERENCE DOCUMENTS",
            "reference_documents"
        ),

        (
            "PROCEDURE FOR CONCRETING",
            "procedure_for_concreting"
        ),

        (
            "EQUIPMENT USED",
            "equipment_used"
        ),

        (
            "KEY PEOPLE INVOLVED",
            "key_people_involved"
        ),

        (
            "OTHER RELEVANT INFORMATION",
            "other_relevant_information"
        )
    ]

    for title, key in sections:

        section = statement.get(
            key,
            {}
        )

        print()
        print("-" * 70)
        print(title)
        print("-" * 70)

        content = section.get(
            "content",
            ""
        )

        if isinstance(
            content,
            list
        ):

            for item in content:

                print(
                    f"  • {item}"
                )

        else:

            print(
                content
            )

        sources = section.get(
            "sources",
            []
        )

        if sources:

            print()
            print("Sources:")

            for source in sources:

                print(
                    f"  Page: {source.get('page', '')} "
                    f"| Chunk: {source.get('chunk', '')}"
                )

                evidence = source.get(
                    "evidence",
                    ""
                )

                if evidence:

                    print(
                        f"  Evidence: {evidence}"
                    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("DOCMINDAI METHOD STATEMENT GENERATOR TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Build graph
    # --------------------------------------------------------

    graph = build_graph()

    print(
        f"Test graph nodes: "
        f"{len(graph.nodes)}"
    )

    print(
        f"Test graph edges: "
        f"{len(graph.edges)}"
    )

    # --------------------------------------------------------
    # Hybrid retriever
    # --------------------------------------------------------

    retriever = HybridRetriever(
        graph,
        vector_top_k=3,
        graph_top_k=3
    )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    result = generate_method_statement(
        retriever
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    display_method_statement(
        result
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    output_path = (
        PROJECT_ROOT
        / "method_statement"
        / "method_statement_output.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("METHOD STATEMENT JSON SAVED")
    print("=" * 70)

    print(
        output_path
    )

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()