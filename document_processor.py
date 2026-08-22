from pathlib import Path

from document_analyzer import analyze_pdf
from pdf_loader import load_pdf
from ocr import ocr_pdf


def process_document(pdf_path):
    """
    Automatically process a PDF using the appropriate
    extraction strategy.

    Returns:
        dict containing document profile and extracted pages.
    """

    pdf_path = Path(pdf_path)

    profile = analyze_pdf(pdf_path)

    if profile["document_type"] == "text":
        pages = load_pdf(pdf_path)

        for page in pages:
            page["source_type"] = "native_text"

    elif profile["document_type"] == "scanned":
        pages = ocr_pdf(pdf_path)

    else:
        # Mixed document:
        # Process each page according to whether it
        # already contains native text.
        native_pages = load_pdf(pdf_path)
        ocr_pages = ocr_pdf(pdf_path)

        pages = []

        for native_page, ocr_page in zip(
            native_pages,
            ocr_pages
        ):
            if native_page["text"].strip():
                native_page["source_type"] = "native_text"
                pages.append(native_page)
            else:
                pages.append(ocr_page)

    return {
        "profile": profile,
        "pages": pages
    }