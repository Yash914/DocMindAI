import re


# ============================================================
# ALLOWED PREDICATES
# ============================================================

ALLOWED_PREDICATES = {
    "CONFORMS_TO",
    "REQUIRES",
    "TESTED_AT",
    "TESTED_FOR",
    "STORED_AT",
    "STORED_SEPARATELY",
    "APPROVED_BY",
    "MUST_PROVIDE",
    "MUST_TEST",
    "HAS_RIGHT_TO_TEST",
    "REQUIRED_TO_TEST",
}


# ============================================================
# PREDICATE NORMALIZATION
# ============================================================

PREDICATE_MAP = {
    "SHALL_GET": "REQUIRED_TO_TEST",
    "HAS_RIGHT": "HAS_RIGHT_TO_TEST",
    "MUST_GET": "REQUIRED_TO_TEST",
}


def normalize_predicate(predicate):

    if not predicate:
        return None

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


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# SUBJECT SUPPORT
# ============================================================

def subject_supported(
    subject,
    evidence,
    source_text
):
    """
    Check whether the subject is supported by the
    evidence or the surrounding source context.

    This allows implicit references such as:

        Cement → Each consignment
        Cement → The consignment

    """

    subject = normalize_text(subject)
    evidence = normalize_text(evidence)
    source_text = normalize_text(source_text)

    if not subject:
        return False

    # Direct mention
    if subject in evidence:
        return True

    # Check source context
    if subject in source_text:
        return True

    # Common document-reference patterns
    if subject == "cement":

        patterns = [
            "consignment",
            "each consignment",
            "cement in stock",
            "cement shall",
            "cement more than"
        ]

        for pattern in patterns:

            if pattern in evidence:

                return True

    if subject == "steel":

        patterns = [
            "steel in stock",
            "the steel",
            "steel shall"
        ]

        for pattern in patterns:

            if pattern in evidence:

                return True

    if subject == "manufacturer":

        if (
            "manufacturer" in evidence
            or "cost of manufacturer" in evidence
        ):
            return True

    if subject == "inspecting officer":

        if "inspecting officer" in evidence:
            return True

    return False


# ============================================================
# OBJECT SUPPORT
# ============================================================

def object_supported(
    object_value,
    evidence,
    source_text
):
    """
    Check whether the object is supported by evidence.
    """

    object_value = normalize_text(
        object_value
    )

    evidence = normalize_text(
        evidence
    )

    source_text = normalize_text(
        source_text
    )

    if not object_value:
        return False

    # Direct mention
    if object_value in evidence:
        return True

    # Source-level support
    if object_value in source_text:
        return True

    # --------------------------------------------------------
    # Common aliases
    # --------------------------------------------------------

    aliases = {

        "test certificate": [
            "test certificate",
            "certificate"
        ],

        "laboratory": [
            "laboratory",
            "lab"
        ],

        "physical properties": [
            "physical properties",
            "relevant properties"
        ],

        "steel": [
            "steel",
            "steel in stock"
        ],

        "cement": [
            "cement",
            "cement in stock"
        ]
    }

    if object_value in aliases:

        for alias in aliases[object_value]:

            if alias in evidence:

                return True

    return False


# ============================================================
# FACT VALIDATION
# ============================================================

def validate_fact(
    fact,
    source_text
):
    """
    Validate a single extracted fact.

    Returns:

        {
            "valid": True/False,
            "reason": "...",
            "fact": fact
        }
    """

    subject = fact.get(
        "subject",
        ""
    )

    predicate = normalize_predicate(
        fact.get(
            "predicate",
            ""
        )
    )

    object_value = fact.get(
        "object",
        ""
    )

    evidence = fact.get(
        "evidence",
        ""
    )

    # --------------------------------------------------------
    # Predicate
    # --------------------------------------------------------

    if predicate not in ALLOWED_PREDICATES:

        return {
            "valid": False,
            "reason":
                f"Unknown predicate: {predicate}",
            "fact": fact
        }

    # Update normalized predicate
    fact = fact.copy()

    fact["predicate"] = predicate

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    if not evidence:

        return {
            "valid": False,
            "reason": "Missing evidence",
            "fact": fact
        }

    # --------------------------------------------------------
    # Subject
    # --------------------------------------------------------

    if not subject_supported(
        subject,
        evidence,
        source_text
    ):

        return {
            "valid": False,
            "reason":
                "Subject not supported by evidence",
            "fact": fact
        }

    # --------------------------------------------------------
    # Object
    # --------------------------------------------------------

    if not object_supported(
        object_value,
        evidence,
        source_text
    ):

        return {
            "valid": False,
            "reason":
                "Object not supported by evidence",
            "fact": fact
        }

    # --------------------------------------------------------
    # Valid
    # --------------------------------------------------------

    return {
        "valid": True,
        "reason": "Fact supported by evidence",
        "fact": fact
    }


# ============================================================
# VALIDATE ALL FACTS
# ============================================================

def validate_facts(
    facts,
    source_text
):
    """
    Validate all LLM-extracted facts.

    Returns:

        valid_facts,
        rejected_facts
    """

    valid_facts = []
    rejected_facts = []

    for fact in facts:

        result = validate_fact(
            fact,
            source_text
        )

        if result["valid"]:

            valid_facts.append(
                result["fact"]
            )

        else:

            rejected_facts.append(
                {
                    "fact": result["fact"],
                    "reason": result["reason"]
                }
            )

    return (
        valid_facts,
        rejected_facts
    )