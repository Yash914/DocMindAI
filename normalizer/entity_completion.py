import re


# ============================================================
# ENTITY TYPE RULES
# ============================================================

ENTITY_TYPE_RULES = {

    "certificate": "Document",
    "test certificate": "Document",
    "report": "Document",
    "drawing": "Document",
    "specification": "Document",

    "laboratory": "Organization",
    "laboratory of the plant": "Organization",

    "cement": "Material",
    "steel": "Material",
    "concrete": "Material",
    "aggregate": "Material",

    "physical properties": "Property",
    "compressive strength": "Property",
    "strength": "Property",

}


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# INFER ENTITY TYPE
# ============================================================

def infer_entity_type(name):

    cleaned = clean_text(
        name
    ).lower()

    # Exact / phrase matching
    for phrase, entity_type in ENTITY_TYPE_RULES.items():

        if cleaned == phrase:

            return entity_type

    # Partial matching
    if "certificate" in cleaned:

        return "Document"

    if "laboratory" in cleaned:

        return "Organization"

    if "property" in cleaned:

        return "Property"

    if "cement" in cleaned:

        return "Material"

    if "steel" in cleaned:

        return "Material"

    if "concrete" in cleaned:

        return "Material"

    return "Concept"


# ============================================================
# EXTRACT FACT REFERENCES
# ============================================================

def collect_fact_entities(facts):

    references = []

    for fact in facts:

        subject = clean_text(
            fact.get(
                "subject",
                ""
            )
        )

        object_value = clean_text(
            fact.get(
                "object",
                ""
            )
        )

        if subject:

            references.append(
                subject
            )

        if object_value:

            references.append(
                object_value
            )

    return references


# ============================================================
# COMPLETE ENTITIES
# ============================================================

def complete_entities(
    entities,
    facts
):
    """
    Add entities referenced by validated facts
    but missing from the LLM entity list.
    """

    completed = []

    existing = {}

    # --------------------------------------------------------
    # Existing entities
    # --------------------------------------------------------

    for entity in entities:

        name = clean_text(
            entity.get(
                "name",
                ""
            )
        )

        if not name:
            continue

        key = name.lower()

        existing[key] = {
            "name": name,
            "type": entity.get(
                "type",
                "Entity"
            ),
            "aliases": entity.get(
                "aliases",
                []
            )
        }

        completed.append(
            existing[key]
        )

    # --------------------------------------------------------
    # Entities referenced by facts
    # --------------------------------------------------------

    references = collect_fact_entities(
        facts
    )

    for reference in references:

        key = reference.lower()

        if key in existing:

            continue

        entity_type = infer_entity_type(
            reference
        )

        new_entity = {
            "name": reference,
            "type": entity_type,
            "aliases": []
        }

        completed.append(
            new_entity
        )

        existing[key] = new_entity

    return completed