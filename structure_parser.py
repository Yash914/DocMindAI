import re


NUMBER_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)*)\.?$"
)


def is_number_line(line):
    """
    Check whether a line contains only a section/clause number.

    Examples:
        3.
        3.1
        3.1.1
        1006.
    """

    line = line.strip()

    return NUMBER_PATTERN.match(line) is not None


def looks_like_heading(text):
    """
    Determine whether text looks like a section heading.
    """

    text = text.strip()

    if not text:
        return False

    # Headings are usually relatively short.
    if len(text) > 100:
        return False

    # A heading should not look like a complete sentence.
    if text.endswith((".", ",", ";", ":")):
        return False

    sentence_words = {
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
    }

    words = text.lower().split()

    if any(word in sentence_words for word in words):
        return False

    return True


def classify_number(number):
    """
    Classify a numbered item based on its depth.

    Examples:
        3       -> section
        3.1     -> subsection
        3.1.1   -> clause
        3.1.1.1 -> subclause
    """

    depth = len(number.split("."))

    if depth == 1:
        return "section"

    if depth == 2:
        return "subsection"

    if depth == 3:
        return "clause"

    return "subclause"


def parse_page_lines(page):
    """
    Parse a single page and detect numbered structures.

    Returns a list of detected structures.
    """

    lines = [
        line.strip()
        for line in page["text"].splitlines()
        if line.strip()
    ]

    structures = []

    i = 0

    while i < len(lines):

        current = lines[i]

        # Case 1:
        # Number and title are on the same line.
        #
        # Example:
        # 1006. CEMENT

        same_line = re.match(
            r"^(\d+(?:\.\d+)*)\.?\s+(.+)$",
            current
        )

        if same_line:

            number = same_line.group(1)
            title = same_line.group(2).strip()

            if looks_like_heading(title):

                structures.append({
                    "number": number,
                    "title": title,
                    "type": classify_number(number),
                    "page_number": page["page_number"],
                    "source_type": page["source_type"]
                })

            i += 1
            continue

        # Case 2:
        # Number and title are on separate lines.
        #
        # Example:
        # 3.2
        # Cement

        if is_number_line(current):

            number = current.rstrip(".")

            if i + 1 < len(lines):

                next_line = lines[i + 1]

                if looks_like_heading(next_line):

                    structures.append({
                        "number": number,
                        "title": next_line,
                        "type": classify_number(number),
                        "page_number": page["page_number"],
                        "source_type": page["source_type"]
                    })

                    i += 2
                    continue

        i += 1

    return structures