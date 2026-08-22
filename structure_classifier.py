import re


NUMBER_PATTERN = re.compile(
    r"^\d+(?:\.\d+)*\.?$"
)


def is_number(text):
    """
    Check whether text is a section/clause number.
    """

    return bool(
        NUMBER_PATTERN.match(text.strip())
    )


def get_depth(number):
    """
    Determine numbering depth.

    3       -> 1
    3.1     -> 2
    3.1.1   -> 3
    3.1.1.1 -> 4
    """

    number = number.rstrip(".")

    return len(number.split("."))


def is_bold(item):
    """
    Determine whether a PDF text span is bold.

    PyMuPDF font names commonly contain:
        Bold
        BOLD
    """

    font = item.get("font", "")

    return "bold" in font.lower()


def classify_numbered_item(number, title_item):
    """
    Classify a numbered item using numbering depth,
    font information and text characteristics.
    """

    depth = get_depth(number)

    bold = is_bold(title_item)

    title = title_item["text"].strip()

    # -----------------------------------------
    # Strong heading signal
    # -----------------------------------------

    if bold:

        if depth == 1:
            return "section"

        if depth == 2:
            return "subsection"

        return "subsection"

    # -----------------------------------------
    # Non-bold numbered text
    # -----------------------------------------

    if depth >= 3:
        return "clause"

    # A depth-1 or depth-2 non-bold item
    # needs more context.
    return "unknown"