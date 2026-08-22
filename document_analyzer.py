from pathlib import Path

from pdf_loader import load_pdf


def analyze_pdf(pdf_path):
    """
    Analyze a PDF and determine whether it contains
    machine-readable text.
    """

    pdf_path = Path(pdf_path)

    pages = load_pdf(pdf_path)

    total_characters = sum(
        len(page["text"])
        for page in pages
    )

    pages_with_text = sum(
        1
        for page in pages
        if page["text"].strip()
    )

    total_pages = len(pages)

    if total_characters == 0:
        document_type = "scanned"
    else:
        document_type = "text"

    return {
        "filename": pdf_path.name,
        "total_pages": total_pages,
        "pages_with_text": pages_with_text,
        "total_characters": total_characters,
        "document_type": document_type,
    }