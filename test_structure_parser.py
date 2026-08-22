from config import INPUT_DIR
from document_processor import process_document
from structure_parser import parse_page_lines


pdf_path = INPUT_DIR / "S-2_sr.pdf"

result = process_document(pdf_path)

print("=" * 70)
print("STRUCTURE PARSER — S-2")
print("=" * 70)

total = 0

for page in result["pages"]:

    structures = parse_page_lines(page)

    for item in structures:

        print(
            f"Page {item['page_number']:>2} | "
            f"{item['number']:<8} | "
            f"{item['type']:<10} | "
            f"{item['title']}"
        )

        total += 1

print("\n" + "=" * 70)
print(f"TOTAL STRUCTURES: {total}")
print("=" * 70)