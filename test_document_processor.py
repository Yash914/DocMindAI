from config import INPUT_DIR
from document_processor import process_document


pdf_files = [
    "S-1_sr.pdf",
    "S-2_sr.pdf",
    "S-3_sr.pdf"
]


for filename in pdf_files:

    print("\n" + "=" * 70)
    print(f"PROCESSING: {filename}")
    print("=" * 70)

    pdf_path = INPUT_DIR / filename

    result = process_document(pdf_path)

    profile = result["profile"]
    pages = result["pages"]

    print(f"Document type: {profile['document_type']}")
    print(f"Pages: {len(pages)}")

    native_count = sum(
        1
        for page in pages
        if page["source_type"] == "native_text"
    )

    ocr_count = sum(
        1
        for page in pages
        if page["source_type"] == "ocr"
    )

    print(f"Native text pages: {native_count}")
    print(f"OCR pages: {ocr_count}")

    print("\nFirst page:")
    print("-" * 70)
    print(pages[0]["text"][:500])