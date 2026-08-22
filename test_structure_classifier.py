from config import INPUT_DIR

from layout_extractor import extract_page_layout

from structure_classifier import (
    is_number,
    classify_numbered_item
)

from page_filter import filter_layout_items


pdf_path = INPUT_DIR / "S-2_sr.pdf"

pages = [4, 5]


for page_number in pages:

    print("\n" + "=" * 70)
    print(f"PAGE {page_number}")
    print("=" * 70)

    # Extract layout information
    items = extract_page_layout(
        pdf_path,
        page_number
    )

    # Remove obvious page headers/footers
    items = filter_layout_items(
        items,
        page_number
    )

    i = 0

    while i < len(items):

        current = items[i]

        text = current["text"].strip()

        # Check whether the current item is a number
        if is_number(text):

            number = text.rstrip(".")

            # Look at the following text item
            if i + 1 < len(items):

                next_item = items[i + 1]

                classification = classify_numbered_item(
                    number,
                    next_item
                )

                is_bold_text = (
                    "bold" in next_item["font"].lower()
                )

                print(
                    f"{number:<8} | "
                    f"{classification:<12} | "
                    f"bold={str(is_bold_text):<5} | "
                    f"{next_item['text']}"
                )

        i += 1