from pathlib import Path
import sys


# Allow this test to import the existing
# project files from the parent directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


from config import INPUT_DIR
from document_processor import process_document

from chunker.chunker import create_chunks


pdf_path = INPUT_DIR / "S-2_sr.pdf"

print("=" * 70)
print("SMART CHUNKING TEST")
print("=" * 70)

print(f"PDF: {pdf_path.name}")

# Process the PDF using our existing pipeline
result = process_document(pdf_path)

pages = result["pages"]

print(f"Pages: {len(pages)}")

# Create chunks
chunks = create_chunks(
    pages,
    chunk_size=1000,
    overlap=150
)

print(f"Chunks created: {len(chunks)}")


# Display first five chunks
for chunk in chunks[:5]:

    print("\n" + "-" * 70)

    print(f"Chunk ID    : {chunk['chunk_id']}")
    print(f"Page        : {chunk['page_number']}")
    print(f"Source type : {chunk['source_type']}")
    print(f"Characters  : {len(chunk['text'])}")

    print("\nTEXT:")
    print(chunk["text"])