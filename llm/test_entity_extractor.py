from pathlib import Path
import sys


# --------------------------------------------------
# PROJECT ROOT
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------
# PROJECT IMPORTS
# --------------------------------------------------

from config import INPUT_DIR
from document_processor import process_document

from chunker.chunker import create_chunks

from entity_extractor import extract_knowledge


# --------------------------------------------------
# LOAD REAL PDF
# --------------------------------------------------

pdf_path = INPUT_DIR / "S-2_sr.pdf"

print("=" * 70)
print("REAL PDF → CHUNK → LLM KNOWLEDGE EXTRACTION")
print("=" * 70)

print(f"PDF: {pdf_path.name}")


# --------------------------------------------------
# PROCESS PDF
# --------------------------------------------------

result = process_document(pdf_path)

pages = result["pages"]

print(f"Pages : {len(pages)}")


# --------------------------------------------------
# CREATE CHUNKS
# --------------------------------------------------

chunks = create_chunks(
    pages,
    chunk_size=1000,
    overlap=150
)

print(f"Chunks: {len(chunks)}")


# --------------------------------------------------
# FIND A USEFUL REAL CHUNK
# --------------------------------------------------

selected_chunk = None

for chunk in chunks:

    text = chunk["text"].lower()

    if "cement shall conform" in text:

        selected_chunk = chunk
        break


# Fallback if the expected text is not found
if selected_chunk is None:

    selected_chunk = chunks[0]


# --------------------------------------------------
# DISPLAY SELECTED CHUNK
# --------------------------------------------------

print("\n" + "-" * 70)

print(
    f"Chunk ID    : {selected_chunk['chunk_id']}"
)

print(
    f"Page        : {selected_chunk['page_number']}"
)

print(
    f"Source type : {selected_chunk['source_type']}"
)

print("\nTEXT:")
print(selected_chunk["text"])


# --------------------------------------------------
# LLM EXTRACTION
# --------------------------------------------------

print("\n" + "-" * 70)
print("LLM EXTRACTION")
print("-" * 70)


knowledge = extract_knowledge(
    selected_chunk["text"]
)


# --------------------------------------------------
# DISPLAY ENTITIES
# --------------------------------------------------

print("\nEntities:")

for entity in knowledge["entities"]:

    print(
        f"  - {entity.get('name', 'UNKNOWN')} "
        f"[{entity.get('type', 'UNKNOWN')}]"
    )


# --------------------------------------------------
# DISPLAY FACTS
# --------------------------------------------------

print("\nFacts:")

for fact in knowledge["facts"]:

    subject = fact.get(
        "subject",
        "UNKNOWN"
    )

    predicate = fact.get(
        "predicate",
        "UNKNOWN"
    )

    object_value = fact.get(
        "object",
        "UNKNOWN"
    )

    evidence = fact.get(
        "evidence",
        "NO EVIDENCE"
    )

    print(
        f"  - {subject} "
        f"--{predicate}--> "
        f"{object_value}"
    )

    print(
        f"    Evidence: {evidence}"
    )


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n" + "=" * 70)
print("EXTRACTION SUMMARY")
print("=" * 70)

print(
    f"Entities extracted : "
    f"{len(knowledge['entities'])}"
)

print(
    f"Facts extracted    : "
    f"{len(knowledge['facts'])}"
)

print(
    f"Source document     : "
    f"{pdf_path.name}"
)

print(
    f"Source page         : "
    f"{selected_chunk['page_number']}"
)

print(
    f"Source chunk        : "
    f"{selected_chunk['chunk_id']}"
)