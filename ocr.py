from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image


# Tesseract executable
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def ocr_pdf(pdf_path):
    """
    Extract text from a scanned PDF using OCR.

    Each PDF page is rendered as an image and processed
    separately so that page numbers are preserved.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file is not a PDF.")

    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        # Render PDF page as an image.
        pixmap = page.get_pixmap(dpi=200)

        # Convert image bytes to PIL image.
        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples
        )

        # OCR the page.
        text = pytesseract.image_to_string(image)

        pages.append({
            "page_number": page_number,
            "text": text.strip(),
            "source_type": "ocr"
        })

        print(
            f"OCR processed page "
            f"{page_number}/{len(document)}"
        )

    document.close()

    return pages