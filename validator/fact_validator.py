import re

ALLOWED_PREDICATES = {
    "CONFORMS_TO","REQUIRES","TESTED_AT","TESTED_FOR","STORED_AT",
    "STORED_SEPARATELY","APPROVED_BY","MUST_PROVIDE","MUST_TEST",
    "HAS_RIGHT_TO_TEST","REQUIRED_TO_TEST","USES","REFERENCES",
    "APPLIES_TO","REQUIRES_APPROVAL","DEFINED_IN","PART_OF",
    "HAS_PROPERTY","SPECIFIES","MAY_BE_USED","COVERED_BY",
}

PREDICATE_MAP = {
    "SHALL_GET": "REQUIRED_TO_TEST",
    "HAS_RIGHT": "HAS_RIGHT_TO_TEST",
    "MUST_GET": "REQUIRED_TO_TEST",
}

def normalize_predicate(predicate):
    if not predicate:
        return None
    predicate = re.sub(r"\s+", "_", str(predicate).strip().upper())
    return PREDICATE_MAP.get(predicate, predicate)

def normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()

def subject_supported(subject, evidence, source_text):
    subject = normalize_text(subject)
    evidence = normalize_text(evidence)
    source_text = normalize_text(source_text)
    if not subject:
        return False
    if subject in evidence or subject in source_text:
        return True
    aliases = {
        "cement": ["consignment", "cement shall", "cement in stock", "cement more than"],
        "steel": ["steel in stock", "the steel", "steel shall"],
        "manufacturer": ["manufacturer", "cost of manufacturer"],
        "inspecting officer": ["inspecting officer"],
    }
    return any(x in evidence for x in aliases.get(subject, []))

def object_supported(object_value, evidence, source_text):
    value = normalize_text(object_value)
    evidence = normalize_text(evidence)
    source_text = normalize_text(source_text)
    if not value:
        return False
    if value in evidence or value in source_text:
        return True
    aliases = {
        "test certificate": ["test certificate", "certificate"],
        "laboratory": ["laboratory", "lab"],
        "physical properties": ["physical properties", "relevant properties"],
        "steel": ["steel", "steel in stock"],
        "cement": ["cement", "cement in stock"],
    }
    return any(x in evidence for x in aliases.get(value, []))

def validate_fact(fact, source_text):
    predicate = normalize_predicate(fact.get("predicate", ""))
    normalized = fact.copy()
    normalized["predicate"] = predicate

    if predicate not in ALLOWED_PREDICATES:
        return {"valid": False, "reason": f"Unknown predicate: {predicate}", "fact": normalized}
    if not normalized.get("evidence"):
        return {"valid": False, "reason": "Missing evidence", "fact": normalized}
    if not subject_supported(normalized.get("subject", ""), normalized["evidence"], source_text):
        return {"valid": False, "reason": "Subject not supported by evidence", "fact": normalized}
    if not object_supported(normalized.get("object", ""), normalized["evidence"], source_text):
        return {"valid": False, "reason": "Object not supported by evidence", "fact": normalized}
    return {"valid": True, "reason": "Fact supported by evidence", "fact": normalized}

def validate_facts(facts, source_text):
    valid, rejected = [], []
    for fact in facts or []:
        result = validate_fact(fact, source_text)
        (valid if result["valid"] else rejected).append(
            result["fact"] if result["valid"] else {
                "fact": result["fact"], "reason": result["reason"]
            }
        )
    return valid, rejected
