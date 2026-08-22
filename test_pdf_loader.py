from config import INPUT_DIR
from pdf_loader import load_pdf


pdf_files = [
    "S-1_sr.pdf",
    "S-2_sr.pdf",
    "S-3_sr.pdf"
]


for filename in pdf_files:

    print("\n" + "=" * 60)
    print(f"Testing: {filename}")
    print("=" * 60)

    pdf_path = INPUT_DIR / filename

    try:
        pages = load_pdf(pdf_path)

        print(f"Pages detected: {len(pages)}")

        for page in pages[:3]:
            text = page["text"]

            print(
                f"\nPage {page['page_number']}: "
                f"{len(text)} characters"
            )

            if text:
                print(text[:300].replace("\n", " "))

    except Exception as e:
        print(f"ERROR: {e}")