from pathlib import Path
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from normalizer.entity_linker import (
    resolve_entity,
    link_facts
)


# ============================================================
# CANONICAL ENTITIES
# ============================================================

entities = [

    {
        "name": "Cement",
        "type": "Material",
        "aliases": []
    },

    {
        "name": "IS:12269-1987",
        "type": "Standard",
        "aliases": [
            "IS: 12269 -1987"
        ]
    },

    {
        "name": "Government approved laboratory",
        "type": "Organization",
        "aliases": [
            "independent government approved laboratory"
        ]
    },

    {
        "name": "Inspecting Officer",
        "type": "Role",
        "aliases": [
            "The Inspecting Officer"
        ]
    }
]


# ============================================================
# TEST ENTITY RESOLUTION
# ============================================================

print("=" * 70)
print("ENTITY LINKING TEST")
print("=" * 70)


test_entities = [
    "Cement",
    "IS: 12269 -1987",
    "independent government approved laboratory",
    "The Inspecting Officer",
    "Unknown laboratory"
]


for name in test_entities:

    result = resolve_entity(
        name,
        entities
    )

    print(
        f"\n{name}"
    )

    print(
        f"  → {result}"
    )


# ============================================================
# TEST FACT LINKING
# ============================================================

facts = [

    {
        "subject": "Cement",
        "predicate": "CONFORMS_TO",
        "object": "IS: 12269 -1987",
        "evidence":
            "Cement shall conform to IS: 12269 -1987."
    },

    {
        "subject": "Cement",
        "predicate": "TESTED_AT",
        "object":
            "independent government approved laboratory",
        "evidence":
            "Cement shall be tested by an independent "
            "government approved laboratory."
    },

    {
        "subject": "Cement",
        "predicate": "TESTED_AT",
        "object": "Unknown laboratory",
        "evidence":
            "Test evidence."
    }
]


linked, unresolved = link_facts(
    facts,
    entities
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 70)
print("LINKED FACTS")
print("=" * 70)


for fact in linked:

    print(
        f"\n✓ {fact['subject']} "
        f"--{fact['predicate']}--> "
        f"{fact['object']}"
    )


print("\n" + "=" * 70)
print("UNRESOLVED FACTS")
print("=" * 70)


for item in unresolved:

    fact = item["fact"]

    print(
        f"\n✗ {fact['subject']} "
        f"--{fact['predicate']}--> "
        f"{fact['object']}"
    )

    print(
        f"  Subject resolved: "
        f"{item['subject_resolved']}"
    )

    print(
        f"  Object resolved: "
        f"{item['object_resolved']}"
    )