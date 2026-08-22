from config import INPUT_DIR
from ocr import ocr_pdf


pdf_path = INPUT_DIR / "S-1_sr.pdf"

pages = ocr_pdf(pdf_path)

print("\n" + "=" * 60)
print("OCR RESULT")
print("=" * 60)

print(f"PDF: {pdf_path.name}")
print(f"Pages: {len(pages)}")

for page in pages[:3]:

    print("\n" + "-" * 60)
    print(f"PAGE {page['page_number']}")
    print("-" * 60)

    print(f"Characters: {len(page['text'])}")
    print(page["text"][:1000])