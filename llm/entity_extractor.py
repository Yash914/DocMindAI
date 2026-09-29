from llm.llm_client import generate_json

EXTRACTION_PROMPT = """
You are a high-precision construction specification knowledge extraction system.

Extract ONLY information explicitly supported by the supplied document chunk.

Entities:
- Activity
- Material
- Equipment
- Standard
- Requirement
- Test
- Approval
- Section
- Role
- Organization
- Person
- Property
- Measurement
- Document
- Location
- Process

Extract explicit relationships. Prefer these normalized predicates:
REQUIRES, USES, REFERENCES, APPLIES_TO, REQUIRES_APPROVAL, DEFINED_IN,
CONFORMS_TO, TESTED_BY, TESTED_AT, APPROVED_BY, HAS_PROPERTY, SPECIFIES,
PART_OF, COVERED_BY, STORED_AT, STORED_SEPARATELY, TESTED_FOR, MAY_BE_USED.

Every fact MUST include exact supporting evidence from the chunk.
Do not create uncertain facts.
Return ONLY valid JSON:

{
  "entities": [{"name": "...", "type": "..."}],
  "facts": [{
    "subject": "...",
    "predicate": "NORMALIZED_PREDICATE",
    "object": "...",
    "evidence": "exact supporting text"
  }]
}

DOCUMENT CHUNK:
"""

def extract_knowledge(text):
    if not text or not text.strip():
        return {"entities": [], "facts": []}
    result = generate_json(EXTRACTION_PROMPT + "\n" + text)
    if not isinstance(result, dict):
        raise ValueError("LLM did not return a JSON object.")
    result.setdefault("entities", [])
    result.setdefault("facts", [])
    return result
