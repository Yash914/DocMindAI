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


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("LLM EXTRACTION → FACT VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    pdf_path = INPUT_DIR / "S-2_sr.pdf"

    print(f"PDF: {pdf_path.name}")

    # --------------------------------------------------------
    # PROCESS DOCUMENT
    # --------------------------------------------------------

    result = process_document(pdf_path)

    pages = result["pages"]

    print(f"Pages : {len(pages)}")

    # --------------------------------------------------------
    # CREATE CHUNKS
    # --------------------------------------------------------

    chunks = create_chunks(
        pages,
        chunk_size=1000,
        overlap=150
    )

    print(f"Chunks: {len(chunks)}")

    # --------------------------------------------------------
    # FIND CEMENT CHUNK
    # --------------------------------------------------------

    selected_chunk = None

    for chunk in chunks:

        if "cement shall conform" in chunk["text"].lower():

            selected_chunk = chunk
            break

    if selected_chunk is None:

        print("Could not find the required cement chunk.")

        return

    # --------------------------------------------------------
    # DISPLAY CHUNK
    # --------------------------------------------------------

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

    print("\nTEXT:")

    print(selected_chunk["text"])

    # --------------------------------------------------------
    # LLM EXTRACTION
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("RUNNING LLM EXTRACTION")
    print("-" * 70)

    knowledge = extract_knowledge(
        selected_chunk["text"]
    )

    # --------------------------------------------------------
    # SHOW ENTITIES
    # --------------------------------------------------------

    print("\nEntities:")

    for entity in knowledge.get("entities", []):

        print(
            f"  - {entity.get('name', 'UNKNOWN')} "
            f"[{entity.get('type', 'UNKNOWN')}]"
        )

    # --------------------------------------------------------
    # SHOW RAW FACTS
    # --------------------------------------------------------

    print("\nRaw LLM Facts:")

    for fact in knowledge.get("facts", []):

        print(
            f"  - {fact.get('subject', 'UNKNOWN')} "
            f"--{fact.get('predicate', 'UNKNOWN')}--> "
            f"{fact.get('object', 'UNKNOWN')}"
        )

        print(
            f"    Evidence: "
            f"{fact.get('evidence', 'NO EVIDENCE')}"
        )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("RUNNING FACT VALIDATOR")
    print("-" * 70)

    valid_facts, rejected_facts = validate_facts(
        knowledge.get("facts", []),
        selected_chunk["text"]
    )

    # --------------------------------------------------------
    # VALID FACTS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALID FACTS")
    print("=" * 70)

    if valid_facts:

        for fact in valid_facts:

            print(
                f"\n✓ {fact['subject']} "
                f"--{fact['predicate']}--> "
                f"{fact['object']}"
            )

            print(
                f"  Evidence: {fact['evidence']}"
            )

    else:

        print("No valid facts.")

    # --------------------------------------------------------
    # REJECTED FACTS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("REJECTED FACTS")
    print("=" * 70)

    if rejected_facts:

        for item in rejected_facts:

            fact = item["fact"]

            print(
                f"\n✗ {fact.get('subject', 'UNKNOWN')} "
                f"--{fact.get('predicate', 'UNKNOWN')}--> "
                f"{fact.get('object', 'UNKNOWN')}"
            )

            print(
                f"  Evidence: "
                f"{fact.get('evidence', 'NO EVIDENCE')}"
            )

            print(
                f"  Reason: {item['reason']}"
            )

    else:

        print("No rejected facts.")

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    print(
        f"Entities extracted : "
        f"{len(knowledge.get('entities', []))}"
    )

    print(
        f"LLM facts          : "
        f"{len(knowledge.get('facts', []))}"
    )

    print(
        f"Valid facts        : "
        f"{len(valid_facts)}"
    )

    print(
        f"Rejected facts     : "
        f"{len(rejected_facts)}"
    )

    print(
        f"Document           : "
        f"{pdf_path.name}"
    )

    print(
        f"Page               : "
        f"{selected_chunk['page_number']}"
    )

    print(
        f"Chunk              : "
        f"{selected_chunk['chunk_id']}"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()