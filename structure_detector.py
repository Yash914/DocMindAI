import re


def detect_heading(line):
    """
    Detect whether a line is likely to be a technical
    document heading.

    Returns:
        tuple: (section_number, title)
        or None if the line is not a heading.
    """

    line = line.strip()

    if not line:
        return None

    # Match numbered headings such as:
    # 1. SCOPE
    # 3. MATERIAL
    # 3.2 CEMENT
    # 4.1 MOULD
    # 1006. CEMENT

    pattern = r"^(\d+(?:\.\d+)*)\.?\s+(.+)$"

    match = re.match(pattern, line)

    if not match:
        return None

    section_number = match.group(1)
    title = match.group(2).strip()

    # -----------------------------
    # Heading confidence checks
    # -----------------------------

    # Very long lines are unlikely to be headings.
    if len(title) > 100:
        return None

    # A heading normally should not end like a sentence.
    if title.endswith((".", ",", ";", ":")):
        return None

    # Reject obvious sentence-style text.
    sentence_words = [
        "shall",
        "should",
        "must",
        "will",
        "may",
        "is",
        "are",
        "was",
        "were",
        "has",
        "have",
        "used",
        "provided",
        "required",
    ]

    words = title.lower().split()

    if any(word in words for word in sentence_words):
        return None

    # Headings in technical specifications are often
    # uppercase or title-like.
    uppercase_ratio = sum(
        1 for char in title
        if char.isupper()
    )

    alphabetic_count = sum(
        1 for char in title
        if char.isalpha()
    )

    if alphabetic_count == 0:
        return None

    ratio = uppercase_ratio / alphabetic_count

    # If the title is mostly lowercase sentence text,
    # it is probably not a heading.
    if ratio < 0.35:
        return None

    return section_number, title