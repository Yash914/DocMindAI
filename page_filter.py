def is_page_number(item, page_number):
    """
    Detect a printed page number near the top of the page.
    """

    text = item["text"].strip()

    if text != str(page_number):
        return False

    # Page numbers are usually very close to the top.
    if item["y0"] < 60:
        return True

    return False


def filter_layout_items(items, page_number):
    """
    Remove obvious page headers/footers.
    """

    filtered = []

    for item in items:

        if is_page_number(item, page_number):
            continue

        filtered.append(item)

    return filtered