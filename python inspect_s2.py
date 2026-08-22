from config import INPUT_DIR
from pdf_loader import load_pdf


pdf_path = INPUT_DIR / "S-2_sr.pdf"

pages = load_pdf(pdf_path)

for page in pages[:6]:

    print("\n" + "=" * 70)
    print(f"PAGE {page['page_number']}")
    print("=" * 70)

    for number, line in enumerate(
        page["text"].splitlines(),
        start=1
    ):
        if line.strip():
            print(f"{number:>3}: {repr(line)}")