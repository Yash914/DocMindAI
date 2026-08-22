from config import INPUT_DIR
from layout_extractor import extract_page_layout


pdf_path = INPUT_DIR / "S-2_sr.pdf"

pages_to_check = [3, 4, 5]


for page_number in pages_to_check:

    print("\n" + "=" * 80)
    print(f"PAGE {page_number}")
    print("=" * 80)

    lines = extract_page_layout(
        pdf_path,
        page_number
    )

    for index, item in enumerate(lines):

        print(
            f"{index:>3} | "
            f"y={item['y0']:>7.2f} | "
            f"size={item['font_size']:>5.1f} | "
            f"font={item['font']:<25} | "
            f"{item['text']}"
        )