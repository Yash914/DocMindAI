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


from normalizer.entity_completion import (
    complete_entities
)


# ============================================================
# LLM ENTITIES
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
        "aliases": []
    }
]


# ============================================================
# VALIDATED FACTS
# ============================================================

facts = [

    {
        "subject": "Cement",
        "predicate": "REQUIRES",
        "object": "test certificate",
        "evidence":
            "Each consignment of cement shall be "
            "covered by a test certificate."
    },

    {
        "subject": "Cement",
        "predicate": "TESTED_FOR",
        "object": "physical properties",
        "evidence":
            "Cement shall be tested for physical properties."
    }
]


# ============================================================
# COMPLETE
# ============================================================

completed = complete_entities(
    entities,
    facts
)


# ============================================================
# OUTPUT
# ============================================================

print("=" * 70)
print("ENTITY COMPLETION TEST")
print("=" * 70)

for entity in completed:

    print(
        f"\n{entity['name']} "
        f"[{entity['type']}]"
    )