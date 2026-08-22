from config import INPUT_DIR
from document_processor import process_document
from structure_detector import detect_heading


pdf_files = [
    "S-1_sr.pdf",
    "S-2_sr.pdf",
    "S-3_sr.pdf"
]


for filename in pdf_files:

    print("\n" + "=" * 70)
    print(f"DOCUMENT: {filename}")
    print("=" * 70)

    pdf_path = INPUT_DIR / filename

    result = process_document(pdf_path)

    pages = result["pages"]

    total_headings = 0

    for page in pages:

        lines = page["text"].splitlines()

        for line in lines:

            heading = detect_heading(line)

            if heading:

                section_number, title = heading

                print(
                    f"Page {page['page_number']:>2} | "
                    f"{section_number:<8} | "
                    f"{title}"
                )

                total_headings += 1

    print("\nTotal headings detected:", total_headings)