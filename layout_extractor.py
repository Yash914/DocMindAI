import pymupdf


def extract_page_layout(pdf_path, page_number):
    """
    Extract text from a page while preserving
    layout and font information.
    """

    doc = pymupdf.open(pdf_path)

    page = doc[page_number - 1]

    blocks = page.get_text("dict")["blocks"]

    result = []

    for block_index, block in enumerate(blocks):

        # Ignore image-only blocks for now
        if "lines" not in block:
            continue

        for line_index, line in enumerate(block["lines"]):

            spans = line.get("spans", [])

            if not spans:
                continue

            text = "".join(
                span.get("text", "")
                for span in spans
            ).strip()

            if not text:
                continue

            first_span = spans[0]

            result.append({
                "text": text,
                "block_index": block_index,
                "line_index": line_index,
                "x0": line["bbox"][0],
                "y0": line["bbox"][1],
                "x1": line["bbox"][2],
                "y1": line["bbox"][3],
                "font": first_span.get("font", ""),
                "font_size": first_span.get("size", 0),
                "flags": first_span.get("flags", 0),
            })

    doc.close()

    return result