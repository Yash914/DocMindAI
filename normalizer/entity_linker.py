import re


def _clean(text):
    """Basic text normalization for matching."""

    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(
        r"\bthe\b",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def build_entity_index(entities):
    """
    Build lookup tables for canonical entities
    and their aliases.
    """

    index = {}

    for entity in entities:

        canonical = entity.get(
            "name",
            ""
        )

        if not canonical:
            continue

        # Canonical name
        index[_clean(canonical)] = canonical

        # Aliases
        for alias in entity.get(
            "aliases",
            []
        ):

            index[_clean(alias)] = canonical

    return index


def resolve_entity(name, entities):
    """
    Resolve an entity mention to a canonical entity.

    Returns:
        canonical name or None
    """

    if not name:
        return None

    index = build_entity_index(
        entities
    )

    cleaned = _clean(name)

    # Exact canonical / alias match
    if cleaned in index:

        return index[cleaned]

    return None


def link_facts(facts, entities):
    """
    Link fact subjects and objects to canonical entities.

    Returns:
        linked_facts
        unresolved_facts
    """

    index = build_entity_index(
        entities
    )

    linked_facts = []
    unresolved_facts = []

    for fact in facts:

        subject = fact.get(
            "subject",
            ""
        )

        object_value = fact.get(
            "object",
            ""
        )

        subject_key = _clean(
            subject
        )

        object_key = _clean(
            object_value
        )

        canonical_subject = index.get(
            subject_key
        )

        canonical_object = index.get(
            object_key
        )

        # Both must resolve
        if (
            canonical_subject
            and canonical_object
        ):

            linked_fact = fact.copy()

            linked_fact["subject"] = (
                canonical_subject
            )

            linked_fact["object"] = (
                canonical_object
            )

            linked_facts.append(
                linked_fact
            )

        else:

            unresolved_facts.append(
                {
                    "fact": fact,
                    "reason": (
                        "Entity could not be resolved"
                    ),
                    "subject_resolved":
                        bool(canonical_subject),
                    "object_resolved":
                        bool(canonical_object)
                }
            )

    return (
        linked_facts,
        unresolved_facts
    )