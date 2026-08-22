from pathlib import Path
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from graph.graph_builder import KnowledgeGraph


# ============================================================
# REAL LLM ENTITIES
# ============================================================

entities = [

    {
        "name": "Manufacturer",
        "type": "Organization"
    },

    {
        "name": "Inspecting Officer",
        "type": "Person"
    },

    {
        "name": "Cement",
        "type": "Material"
    },

    {
        "name": "IS: 12269 -1987 with amendment No.6 of June 2000",
        "type": "Standard"
    },

    {
        "name": "Test certificate",
        "type": "Document"
    },

    {
        "name": "Laboratory of the plant",
        "type": "Location"
    },

    {
        "name": "Government approved laboratory",
        "type": "Organization"
    }
]


# ============================================================
# VALIDATED FACTS
# ============================================================

facts = [

    {
        "subject": "Cement",

        "predicate": "CONFORMS_TO",

        "object":
            "IS: 12269 -1987 with amendment No.6 of June 2000",

        "evidence":
            "Cement shall conform to IS: 12269 -1987 "
            "with amendment No.6 of June 2000."
    },

    {
        "subject": "Cement",

        "predicate": "REQUIRES",

        "object": "test certificate",

        "evidence":
            "Each consignment of cement shall be "
            "covered by a test certificate."
    },

    {
        "subject": "Cement",

        "predicate": "TESTED_AT",

        "object":
            "independent government approved laboratory",

        "evidence":
            "Cement more than 3 months old, if free from lumps, "
            "shall be tested for physical properties by an "
            "independent government approved laboratory."
    }
]


# ============================================================
# BUILD GRAPH
# ============================================================

knowledge_graph = KnowledgeGraph()


knowledge_graph.build(
    entities=entities,
    facts=facts,
    document="S-2_sr.pdf",
    page=5,
    chunk_id="chunk_10"
)


# ============================================================
# DISPLAY
# ============================================================

knowledge_graph.print_graph()