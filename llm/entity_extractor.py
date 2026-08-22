from llm.llm_client import generate_json


EXTRACTION_PROMPT = """
You are a high-precision technical document knowledge extraction system.

Extract ONLY information explicitly supported by the provided document chunk.

Do not invent information.

Extract:

1. Important entities
2. Explicit facts/relationships between those entities

Allowed entity types:

- Material
- Standard
- Organization
- Person
- Role
- Process
- Equipment
- Test
- Property
- Measurement
- Document
- Location
- Requirement

For every fact provide:

- subject
- predicate
- object
- evidence

The evidence MUST come directly from the provided document chunk.

Do not create a fact if the relationship is uncertain.

Use short normalized predicates such as:

CONFORMS_TO
REQUIRES
TESTED_BY
TESTED_AT
APPROVED_BY
USES
HAS_PROPERTY
SPECIFIES
PART_OF
APPLIES_TO
REFERENCES
STORED_SEPARATELY
REVIEWED_WHEN
MODIFIED_WHEN
IDENTIFIED_BY
COVERED_BY
TESTED_FOR
MAY_BE_USED

Return ONLY valid JSON.

Use exactly this structure:

{
  "entities": [
    {
      "name": "entity name",
      "type": "entity type"
    }
  ],
  "facts": [
    {
      "subject": "subject",
      "predicate": "NORMALIZED_PREDICATE",
      "object": "object",
      "evidence": "exact supporting text"
    }
  ]
}

DOCUMENT CHUNK:
"""


def extract_knowledge(text):

    if not text or not text.strip():
        return {
            "entities": [],
            "facts": []
        }

    prompt = EXTRACTION_PROMPT + "\n" + text

    result = generate_json(prompt)

    if not isinstance(result, dict):
        raise ValueError(
            "LLM did not return a JSON object."
        )

    if "entities" not in result:
        result["entities"] = []

    if "facts" not in result:
        result["facts"] = []

    return result