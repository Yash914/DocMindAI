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

from config import INPUT_DIR
from document_processor import process_document
from chunker.chunker import create_chunks

from llm.entity_extractor import extract_knowledge

from validator.fact_validator import validate_facts

from normalizer.entity_completion import complete_entities

from normalizer.entity_normalizer import (
    normalize_entities,
    normalize_facts
)

from normalizer.entity_linker import link_facts

from graph.graph_builder import KnowledgeGraph


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("REAL PDF → LLM → VALIDATOR → COMPLETION → NORMALIZER → LINKER → GRAPH")
    print("=" * 70)

    # ========================================================
    # PDF
    # ========================================================

    pdf_path = INPUT_DIR / "S-2_sr.pdf"

    print(f"PDF: {pdf_path.name}")

    # ========================================================
    # DOCUMENT PROCESSING
    # ========================================================

    document = process_document(pdf_path)

    pages = document["pages"]

    print(f"Pages: {len(pages)}")

    # ========================================================
    # CHUNKING
    # ========================================================

    chunks = create_chunks(
        pages,
        chunk_size=1000,
        overlap=150
    )

    print(f"Chunks: {len(chunks)}")

    # ========================================================
    # FIND TEST CHUNK
    # ========================================================

    selected_chunk = None

    for chunk in chunks:

        if "cement shall conform" in chunk["text"].lower():

            selected_chunk = chunk
            break

    if selected_chunk is None:

        print("ERROR: Cement chunk not found.")
        return

    print("\n" + "-" * 70)

    print(
        f"Chunk: {selected_chunk['chunk_id']}"
    )

    print(
        f"Page: {selected_chunk['page_number']}"
    )

    print(
        f"Source type: {selected_chunk['source_type']}"
    )

    # ========================================================
    # LLM EXTRACTION
    # ========================================================

    print("\n" + "-" * 70)
    print("LLM EXTRACTION")
    print("-" * 70)

    knowledge = extract_knowledge(
        selected_chunk["text"]
    )

    entities = knowledge.get(
        "entities",
        []
    )

    facts = knowledge.get(
        "facts",
        []
    )

    print(
        f"Entities extracted: {len(entities)}"
    )

    print(
        f"Facts extracted: {len(facts)}"
    )

    # ========================================================
    # SHOW ALL LLM FACTS
    # ========================================================

    print("\nLLM Facts:")

    for fact in facts:

        print(
            f"  - {fact.get('subject')} "
            f"--{fact.get('predicate')}--> "
            f"{fact.get('object')}"
        )

    # ========================================================
    # FACT VALIDATION
    # ========================================================

    print("\n" + "-" * 70)
    print("FACT VALIDATION")
    print("-" * 70)

    valid_facts, rejected_facts = validate_facts(
        facts,
        selected_chunk["text"]
    )

    print(
        f"Valid facts: {len(valid_facts)}"
    )

    print(
        f"Rejected facts: {len(rejected_facts)}"
    )

    # ========================================================
    # SHOW VALID FACTS
    # ========================================================

    print("\nValid facts:")

    for fact in valid_facts:

        print(
            f"  ✓ {fact.get('subject')} "
            f"--{fact.get('predicate')}--> "
            f"{fact.get('object')}"
        )

        print(
            f"    Evidence: "
            f"{fact.get('evidence', '')}"
        )

    # ========================================================
    # SHOW REJECTED FACTS
    # ========================================================

    print("\nRejected facts:")

    for item in rejected_facts:

        if isinstance(item, dict):

            fact = item.get(
                "fact",
                item
            )

            reason = item.get(
                "reason",
                "Unknown reason"
            )

        else:

            fact = item
            reason = "Unknown reason"

        print(
            f"\n  ✗ {fact.get('subject')} "
            f"--{fact.get('predicate')}--> "
            f"{fact.get('object')}"
        )

        print(
            f"    Reason: {reason}"
        )

        print(
            f"    Evidence: "
            f"{fact.get('evidence', '')}"
        )

    # ========================================================
    # ENTITY COMPLETION
    # ========================================================

    print("\n" + "-" * 70)
    print("ENTITY COMPLETION")
    print("-" * 70)

    completed_entities = complete_entities(
        entities,
        valid_facts
    )

    print(
        f"Entities after completion: "
        f"{len(completed_entities)}"
    )

    # ========================================================
    # ENTITY NORMALIZATION
    # ========================================================

    print("\n" + "-" * 70)
    print("ENTITY NORMALIZATION")
    print("-" * 70)

    normalized_entities = normalize_entities(
        completed_entities
    )

    normalized_facts = normalize_facts(
        valid_facts,
        normalized_entities
    )

    print(
        f"Normalized entities: "
        f"{len(normalized_entities)}"
    )

    print(
        f"Normalized facts: "
        f"{len(normalized_facts)}"
    )

    # ========================================================
    # DISPLAY ENTITIES
    # ========================================================

    print("\nEntities:")

    for entity in normalized_entities:

        print(
            f"  - {entity['name']} "
            f"[{entity['type']}]"
        )

        aliases = entity.get(
            "aliases",
            []
        )

        if aliases:

            print(
                f"    Aliases: {aliases}"
            )

    # ========================================================
    # ENTITY LINKING
    # ========================================================

    print("\n" + "-" * 70)
    print("ENTITY LINKING")
    print("-" * 70)

    linked_facts, unresolved_facts = link_facts(
        normalized_facts,
        normalized_entities
    )

    print(
        f"Linked facts: "
        f"{len(linked_facts)}"
    )

    print(
        f"Unresolved facts: "
        f"{len(unresolved_facts)}"
    )

    # ========================================================
    # UNRESOLVED FACTS
    # ========================================================

    if unresolved_facts:

        print("\nUnresolved facts:")

        for item in unresolved_facts:

            fact = item["fact"]

            print(
                f"  ✗ {fact.get('subject')} "
                f"--{fact.get('predicate')}--> "
                f"{fact.get('object')}"
            )

            print(
                f"    Subject resolved: "
                f"{item['subject_resolved']}"
            )

            print(
                f"    Object resolved: "
                f"{item['object_resolved']}"
            )

    # ========================================================
    # LINKED FACTS
    # ========================================================

    print("\nLinked facts:")

    for fact in linked_facts:

        print(
            f"  ✓ {fact['subject']} "
            f"--{fact['predicate']}--> "
            f"{fact['object']}"
        )

    # ========================================================
    # BUILD GRAPH
    # ========================================================

    print("\n" + "-" * 70)
    print("BUILDING KNOWLEDGE GRAPH")
    print("-" * 70)

    graph = KnowledgeGraph()

    graph.build(
        entities=normalized_entities,
        facts=linked_facts,
        document=pdf_path.name,
        page=selected_chunk["page_number"],
        chunk_id=selected_chunk["chunk_id"]
    )

    # ========================================================
    # DISPLAY GRAPH
    # ========================================================

    graph.print_graph()

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"Document: {pdf_path.name}"
    )

    print(
        f"Chunk: {selected_chunk['chunk_id']}"
    )

    print(
        f"LLM entities: {len(entities)}"
    )

    print(
        f"LLM facts: {len(facts)}"
    )

    print(
        f"Valid facts: {len(valid_facts)}"
    )

    print(
        f"Rejected facts: {len(rejected_facts)}"
    )

    print(
        f"Entities after completion: "
        f"{len(completed_entities)}"
    )

    print(
        f"Normalized entities: "
        f"{len(normalized_entities)}"
    )

    print(
        f"Linked facts: {len(linked_facts)}"
    )

    print(
        f"Unresolved facts: {len(unresolved_facts)}"
    )

    print(
        f"Graph nodes: {graph.number_of_nodes()}"
    )

    print(
        f"Graph edges: {graph.number_of_edges()}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()