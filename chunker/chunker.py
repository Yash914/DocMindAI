import re


def clean_text(text):
    """
    Basic text cleaning while preserving meaning.
    """

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def split_into_paragraphs(text):
    """
    Split document text into paragraph-like units.
    """

    text = clean_text(text)

    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def create_chunks(
    pages,
    chunk_size=1000,
    overlap=150
):
    """
    Create chunks from processed document pages.

    Each chunk keeps its source page and extraction method.
    """

    chunks = []

    for page in pages:

        text = clean_text(page["text"])

        if not text:
            continue

        paragraphs = split_into_paragraphs(text)

        current_text = ""

        for paragraph in paragraphs:

            # Save current chunk if adding another
            # paragraph would make it too large.
            if (
                current_text
                and len(current_text) + len(paragraph) + 2
                > chunk_size
            ):

                chunks.append({
                    "text": current_text.strip(),
                    "page_number": page["page_number"],
                    "source_type": page["source_type"]
                })

                # Keep overlap from previous chunk
                current_text = current_text[-overlap:]

            if current_text:
                current_text += "\n\n"

            current_text += paragraph

        # Save remaining text from the page
        if current_text.strip():

            chunks.append({
                "text": current_text.strip(),
                "page_number": page["page_number"],
                "source_type": page["source_type"]
            })

    # Assign IDs
    for index, chunk in enumerate(chunks, start=1):
        chunk["chunk_id"] = f"chunk_{index}"

    return chunks