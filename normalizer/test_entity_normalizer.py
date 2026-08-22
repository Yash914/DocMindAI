from pathlib import Path
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT
# ============================================================

from normalizer.entity_normalizer import (
    normalize_entities,
    normalize_facts
)


# ============================================================
# SAMPLE LLM ENTITIES
# ============================================================

entities = [

    {
        "name": "Cement",
        "type": "Material"
    },

    {
        "name": "IS: 12269 -1987 with amendment No.6 of June 2000",
        "type": "Standard"
    },

    {
        "name": "Government approved laboratory",
        "type": "Organization"
    },

    {
        "name": "independent government approved laboratory",
        "type": "Organization"
    },

    {
        "name": "The Inspecting Officer",
        "type": "Role"
    }
]


# ============================================================
# NORMALIZE ENTITIES
# ============================================================

normalized_entities = normalize_entities(
    entities
)


print("=" * 70)
print("ENTITY NORMALIZATION")
print("=" * 70)


for entity in normalized_entities:

    print(
        f"\nCanonical: {entity['name']}"
    )

    print(
        f"Type     : {entity['type']}"
    )

    print(
        f"Aliases  : {entity['aliases']}"
    )


# ============================================================
# SAMPLE FACTS
# ============================================================

facts = [

    {
        "subject": "Cement",
        "predicate": "CONFORMS_TO",
        "object":
            "IS: 12269 -1987 with amendment No.6 of June 2000",
        "evidence":
            "Cement shall conform to IS: 12269 -1987 "
            "with amendment No.6 of June 2000."
    },

    {
        "subject": "Cement",
        "predicate": "TESTED_AT",
        "object":
            "independent government approved laboratory",
        "evidence":
            "Cement shall be tested by an independent "
            "government approved laboratory."
    }
]


# ============================================================
# NORMALIZE FACTS
# ============================================================

normalized_facts = normalize_facts(
    facts,
    normalized_entities
)


print("\n" + "=" * 70)
print("NORMALIZED FACTS")
print("=" * 70)


for fact in normalized_facts:

    print(
        f"\n{fact['subject']} "
        f"--{fact['predicate']}--> "
        f"{fact['object']}"
    )