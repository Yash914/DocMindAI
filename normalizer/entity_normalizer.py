import re


# ============================================================
# TYPE NORMALIZATION
# ============================================================

TYPE_MAP = {

    "PERSON/ROLE": "Role",
    "PERSON": "Person",
    "ROLE": "Role",

    "ORGANIZATION/PERSON": "Organization",
    "ORGANIZATION": "Organization",
    "ORG": "Organization",

    "ORGANIZATION/EQUIPMENT": "Organization",

    "LOCATION": "Location",

    "EQUIPMENT": "Equipment",

    "MATERIAL": "Material",

    "STANDARD": "Standard",

    "DOCUMENT": "Document",

    "PROPERTY": "Property",

    "CONCEPT": "Concept",

    "ENTITY": "Concept"
}


# ============================================================
# NAME NORMALIZATION
# ============================================================

def normalize_name(name):

    if not name:
        return ""

    name = str(name).strip()

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    return name


# ============================================================
# TYPE NORMALIZATION
# ============================================================

def normalize_type(entity_type):

    if not entity_type:

        return "Concept"

    cleaned = (
        str(entity_type)
        .strip()
        .upper()
    )

    return TYPE_MAP.get(
        cleaned,
        "Concept"
    )


# ============================================================
# ALIAS NORMALIZATION
# ============================================================

def normalize_alias(alias):

    return normalize_name(
        alias
    )


# ============================================================
# ENTITY NORMALIZATION
# ============================================================

def normalize_entities(
    entities
):
    """
    Convert LLM entities into canonical entities.
    """

    canonical = {}

    for entity in entities:

        raw_name = entity.get(
            "name",
            ""
        )

        name = normalize_name(
            raw_name
        )

        if not name:
            continue

        entity_type = normalize_type(
            entity.get(
                "type",
                "Concept"
            )
        )

        aliases = []

        for alias in entity.get(
            "aliases",
            []
        ):

            alias = normalize_alias(
                alias
            )

            if (
                alias
                and alias.lower()
                != name.lower()
            ):

                aliases.append(
                    alias
                )

        key = name.lower()

        # ----------------------------------------------------
        # Merge duplicates
        # ----------------------------------------------------

        if key in canonical:

            existing = canonical[key]

            for alias in aliases:

                if alias not in existing["aliases"]:

                    existing["aliases"].append(
                        alias
                    )

            continue

        # ----------------------------------------------------
        # Canonical entity
        # ----------------------------------------------------

        canonical[key] = {
            "name": name,
            "type": entity_type,
            "aliases": aliases
        }

    # --------------------------------------------------------
    # Domain-specific corrections
    # --------------------------------------------------------

    for key, entity in canonical.items():

        name = entity["name"].lower()

        if name == "laboratory":

            entity["type"] = "Organization"

        elif name == "inspecting officer":

            entity["type"] = "Role"

        elif name == "manufacturer":

            entity["type"] = "Organization"

        elif name == "cement":

            entity["type"] = "Material"

    return list(
        canonical.values()
    )


# ============================================================
# FACT NORMALIZATION
# ============================================================

PREDICATE_MAP = {

    "SHALL_GET":
        "REQUIRED_TO_TEST",

    "HAS_RIGHT":
        "HAS_RIGHT_TO_TEST",

    "MUST_GET":
        "REQUIRED_TO_TEST"
}


def normalize_predicate(
    predicate
):

    if not predicate:
        return ""

    predicate = (
        str(predicate)
        .strip()
        .upper()
    )

    predicate = re.sub(
        r"\s+",
        "_",
        predicate
    )

    return PREDICATE_MAP.get(
        predicate,
        predicate
    )


def normalize_facts(
    facts,
    entities=None
):
    """
    Normalize fact names and predicates.
    """

    normalized = []

    for fact in facts:

        new_fact = fact.copy()

        new_fact["subject"] = normalize_name(
            fact.get(
                "subject",
                ""
            )
        )

        new_fact["object"] = normalize_name(
            fact.get(
                "object",
                ""
            )
        )

        new_fact["predicate"] = normalize_predicate(
            fact.get(
                "predicate",
                ""
            )
        )

        normalized.append(
            new_fact
        )

    return normalized