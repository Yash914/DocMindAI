"""
DocMindAI - Method Statement Generator

Generates the structured RCC Method Statement from evidence
retrieved by the existing HybridRetriever.

IMPORTANT:
- This file does NOT import itself.
- generate_method_statement() is preserved because the
  existing test script imports this function.
- Evidence is retained internally for source traceability.
- DOCX generation can display only Page + Chunk.
"""

from __future__ import annotations

import ast
import json
from typing import Any, Dict, List


# ============================================================
# LLM CLIENT
# ============================================================

from llm.llm_client import generate_json


# ============================================================
# SECTION DEFINITIONS
# ============================================================

SECTIONS = {

    "purpose": {
        "title": "Purpose of the Method Statement",
        "query": (
            "purpose objective aim of the specification "
            "RCC construction manufacture supply sleepers"
        )
    },

    "scope": {
        "title": "Scope of the Method Statement",
        "query": (
            "scope applicability work covered manufacture "
            "supply pre-tensioned pre-stressed concrete sleepers "
            "broad gauge meter gauge"
        )
    },

    "acronyms_and_definitions": {
        "title": "Acronyms and Definitions",
        "query": (
            "acronyms abbreviations definitions technical terms "
            "MR MF PASS FAIL"
        )
    },

    "reference_documents": {
        "title": "Reference Documents",
        "query": (
            "reference documents IS BIS code standard "
            "RDSO annexure specification"
        )
    },

    "procedure_for_concreting": {
        "title": "Procedure for Concreting",
        "query": (
            "prestressing wire stressing batching weighing "
            "mixing placement compaction concrete curing "
            "steam curing de-moulding water curing "
            "stacking loading inserts concreting"
        )
    },

    "equipment_used": {
        "title": "Equipment Used",
        "query": (
            "equipment machinery weigh batcher mixer pan "
            "turbine vibrator jack testing machine "
            "calibration"
        )
    },

    "key_people_involved": {
        "title": "Key People Involved",
        "query": (
            "Inspecting Officer supervisor manufacturer "
            "engineer inspection approval responsibility"
        )
    },

    "other_relevant_information": {
        "title": "Other Relevant Information",
        "query": (
            "testing inspection quality control calibration "
            "approval checking electrical resistance "
            "weather protection records"
        )
    }
}


# ============================================================
# CONTENT NORMALIZATION
# ============================================================

def normalize_llm_content(content: Any) -> Any:
    """
    Converts LLM output into proper Python structures.

    Handles:
        dict
        list
        JSON strings
        Python literal strings
        markdown fenced JSON
    """

    if isinstance(content, (dict, list)):
        return content

    if content is None:
        return ""

    if not isinstance(content, str):
        return content

    text = content.strip()

    if not text:
        return ""

    # --------------------------------------------------------
    # Remove Markdown fences
    # --------------------------------------------------------

    if text.startswith("```"):

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:
        return json.loads(text)

    except Exception:
        pass

    # --------------------------------------------------------
    # Python literal
    # --------------------------------------------------------

    try:
        return ast.literal_eval(text)

    except Exception:
        pass

    # --------------------------------------------------------
    # Plain text
    # --------------------------------------------------------

    return text


# ============================================================
# RESULT HELPERS
# ============================================================

def _safe_dict(value: Any) -> Dict:
    if isinstance(value, dict):
        return value
    return {}


def _extract_text(item: Any) -> str:
    """
    Extract text from the different result formats that the
    existing retriever may return.
    """

    if isinstance(item, str):
        return item.strip()

    if not isinstance(item, dict):
        return ""

    # Direct fields
    for key in (
        "text",
        "content",
        "page_content",
        "document_text",
        "chunk_text"
    ):

        value = item.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    # Metadata fields
    metadata = item.get(
        "metadata",
        {}
    )

    if isinstance(metadata, dict):

        for key in (
            "text",
            "content",
            "page_content"
        ):

            value = metadata.get(key)

            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _extract_page(item: Any) -> Any:

    if not isinstance(item, dict):
        return ""

    metadata = item.get(
        "metadata",
        {}
    )

    if not isinstance(metadata, dict):
        metadata = {}

    return (
        item.get("page")
        or item.get("page_number")
        or metadata.get("page")
        or metadata.get("page_number")
        or ""
    )


def _extract_chunk(item: Any) -> str:

    if not isinstance(item, dict):
        return ""

    metadata = item.get(
        "metadata",
        {}
    )

    if not isinstance(metadata, dict):
        metadata = {}

    return str(
        item.get("chunk")
        or item.get("chunk_id")
        or metadata.get("chunk")
        or metadata.get("chunk_id")
        or ""
    )


def _extract_document(item: Any) -> str:

    if not isinstance(item, dict):
        return ""

    metadata = item.get(
        "metadata",
        {}
    )

    if not isinstance(metadata, dict):
        metadata = {}

    return str(
        item.get("document")
        or item.get("filename")
        or item.get("file_name")
        or metadata.get("document")
        or metadata.get("filename")
        or metadata.get("file_name")
        or ""
    )


# ============================================================
# SOURCE CREATION
# ============================================================

def _make_source(item: Any) -> Dict:

    return {
        "document": _extract_document(item),
        "page": _extract_page(item),
        "chunk": _extract_chunk(item),
        "evidence": _extract_text(item)
    }


def _deduplicate_sources(
    sources: List[Dict]
) -> List[Dict]:

    output = []
    seen = set()

    for source in sources:

        if not isinstance(source, dict):
            continue

        key = (
            source.get("document", ""),
            str(source.get("page", "")),
            source.get("chunk", "")
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(source)

    return output


# ============================================================
# RETRIEVER RESULT NORMALIZATION
# ============================================================

def _extract_vector_results(result: Any) -> List:

    if isinstance(result, list):
        return result

    if not isinstance(result, dict):
        return []

    for key in (
        "vector_results",
        "vector_evidence",
        "results",
        "documents",
        "matches"
    ):

        value = result.get(key)

        if isinstance(value, list):
            return value

    return []


def _extract_graph_results(result: Any) -> List:

    if not isinstance(result, dict):
        return []

    for key in (
        "graph_results",
        "graph_evidence",
        "graph"
    ):

        value = result.get(key)

        if isinstance(value, list):
            return value

    return []


# ============================================================
# EVIDENCE FORMATTER
# ============================================================

def _format_vector_evidence(item: Any) -> str:

    text = _extract_text(item)

    if not text:
        return ""

    document = _extract_document(item)
    page = _extract_page(item)
    chunk = _extract_chunk(item)

    return (
        f"DOCUMENT: {document}\n"
        f"PAGE: {page}\n"
        f"CHUNK: {chunk}\n"
        f"SPECIFICATION TEXT:\n{text}"
    )


def _format_graph_evidence(item: Any) -> str:

    if not isinstance(item, dict):
        return ""

    subject = (
        item.get("subject")
        or item.get("source")
        or ""
    )

    predicate = (
        item.get("predicate")
        or item.get("relation")
        or ""
    )

    target = (
        item.get("object")
        or item.get("target")
        or ""
    )

    evidence = (
        item.get("evidence")
        or item.get("text")
        or ""
    )

    return (
        "GRAPH EVIDENCE\n"
        f"ENTITY: {subject}\n"
        f"RELATIONSHIP: {predicate}\n"
        f"TARGET: {target}\n"
        f"EVIDENCE: {evidence}"
    )


# ============================================================
# SECTION PROMPT
# ============================================================

def _build_prompt(
    section_name: str,
    evidence: str
) -> str:

    section = SECTIONS[
        section_name
    ]

    common = """
You are DocMindAI, an AI system generating a professional
engineering Method Statement from a construction specification.

STRICT SOURCE RULE:

Use ONLY the supplied specification evidence.

Do not use external knowledge.

Do not invent requirements.

Do not invent standards.

Do not invent numerical values.

Do not invent responsibilities.

Do not add generic construction practices unless they are
explicitly supported by the evidence.

Where information is absent, return an empty value.

The output will be reviewed by engineering judges.

Use concise but technically useful language.

Preserve all numerical values, capacities, frequencies,
time limits and approval requirements exactly as stated.
"""

    if section_name == "purpose":

        instructions = """
Generate one technically meaningful paragraph describing
the purpose supported by the specification.

Do not make it generic.
"""

        output = """
{
  "content": "..."
}
"""

    elif section_name == "scope":

        instructions = """
Generate a substantive scope description.

Include, where supported:
- work covered
- manufacture/supply covered
- type of sleepers
- gauge
- applicability
- limitations
"""

        output = """
{
  "content": {
    "purpose": "...",
    "description": "..."
  }
}
"""

    elif section_name == "acronyms_and_definitions":

        instructions = """
Extract only explicitly supported acronyms and definitions.
"""

        output = """
{
  "content": [
    {
      "term": "...",
      "definition": "..."
    }
  ]
}
"""

    elif section_name == "reference_documents":

        instructions = """
Extract explicitly referenced documents, standards,
codes and annexures.

Do not invent references.
"""

        output = """
{
  "content": [
    {
      "document": "...",
      "relevance": "..."
    }
  ]
}
"""

    elif section_name == "procedure_for_concreting":

        instructions = """
This is the most important section.

Create approximately 5–8 logical steps where sufficient
evidence exists.

Each step must contain:

title
description

The description should normally contain 2–4 sentences
when the evidence supports that amount of detail.

Include, where explicitly available:

- operation being performed
- specified method
- equipment
- numerical requirements
- time requirements
- approval requirements
- inspection requirements
- quality-control requirements
- special conditions

Potential operations include:

- preparation
- prestressing
- stressing
- batching
- weighing
- mixing
- placement
- compaction
- steam curing
- water curing
- de-moulding
- stacking/loading
- inserts
- testing

Do not invent missing operations.

Do not pad the response.
"""

        output = """
{
  "content": [
    {
      "title": "Batching and Weighing",
      "description": "..."
    },
    {
      "title": "Mixing and Consolidation",
      "description": "..."
    }
  ]
}
"""

    elif section_name == "equipment_used":

        instructions = """
Extract equipment and associated requirements.

Include calibration/frequency only where explicitly
available.
"""

        output = """
{
  "content": [
    {
      "item": "...",
      "description": "...",
      "calibration": "..."
    }
  ]
}
"""

    elif section_name == "key_people_involved":

        instructions = """
Extract explicitly identified roles.

Describe responsibilities only when supported by evidence.
"""

        output = """
{
  "content": [
    {
      "role": "...",
      "responsibility": "..."
    }
  ]
}
"""

    else:

        instructions = """
Extract other technically relevant requirements that do not
belong naturally in the previous sections.

Focus on:
- inspection
- testing
- calibration
- quality control
- approvals
- checking
- records
- weather-related requirements
"""

        output = """
{
  "content": [
    {
      "item": "...",
      "description": "..."
    }
  ]
}
"""

    return f"""
{common}

SECTION:
{section["title"]}

SECTION-SPECIFIC INSTRUCTIONS:
{instructions}

RETURN ONLY VALID JSON.

Do not use Markdown fences.

Do not include explanations.

Do not include sources.

Do not include page numbers.

Do not include chunk IDs.

EXPECTED JSON STRUCTURE:
{output}

============================================================
SPECIFICATION EVIDENCE
============================================================

{evidence}
"""


# ============================================================
# LLM GENERATION
# ============================================================

def _generate_section(
    section_name: str,
    evidence: str
) -> Any:

    prompt = _build_prompt(
        section_name,
        evidence
    )

    result = generate_json(
        prompt
    )

    # Some clients return:
    #
    # {"content": ...}
    #
    # Others return the section directly.

    if isinstance(result, dict):

        if (
            "content" in result
            and len(result) == 1
        ):

            return normalize_llm_content(
                result["content"]
            )

    return normalize_llm_content(
        result
    )


# ============================================================
# RETRIEVER SEARCH
# ============================================================

def _search_retriever(
    retriever,
    query: str
) -> Any:

    """
    Uses the existing HybridRetriever API.

    IMPORTANT:
    We intentionally call search(query) only.
    This avoids the vector_top_k / section_top_k errors
    encountered earlier.
    """

    return retriever.search(
        query
    )


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_method_statement(
    retriever,
    *args,
    **kwargs
):
    """
    Public function expected by the existing test script.

    Usage:

        result = generate_method_statement(
            retriever
        )

    Extra arguments are accepted for backward compatibility.
    """

    print()
    print(
        "-" * 70
    )
    print(
        "RETRIEVING METHOD STATEMENT EVIDENCE"
    )
    print(
        "-" * 70
    )

    method_statement = {}

    all_sources = []

    # ========================================================
    # EACH SECTION
    # ========================================================

    for section_name, config in SECTIONS.items():

        print()
        print(
            f"Retrieving: {section_name}"
        )

        query = config[
            "query"
        ]

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        try:

            search_result = _search_retriever(
                retriever,
                query
            )

        except Exception as exc:

            print(
                f"WARNING: Retrieval failed for "
                f"{section_name}: {exc}"
            )

            search_result = []

        vector_results = _extract_vector_results(
            search_result
        )

        graph_results = _extract_graph_results(
            search_result
        )

        # ----------------------------------------------------
        # Limit evidence
        # ----------------------------------------------------

        vector_results = vector_results[:5]

        graph_results = graph_results[:5]

        # ----------------------------------------------------
        # Evidence text
        # ----------------------------------------------------

        evidence_blocks = []

        for item in vector_results:

            block = _format_vector_evidence(
                item
            )

            if block:
                evidence_blocks.append(
                    block
                )

        for item in graph_results:

            block = _format_graph_evidence(
                item
            )

            if block:
                evidence_blocks.append(
                    block
                )

        evidence = "\n\n".join(
            evidence_blocks
        )

        # ----------------------------------------------------
        # Sources
        # ----------------------------------------------------

        sources = []

        for item in vector_results:

            source = _make_source(
                item
            )

            if source["evidence"]:
                sources.append(
                    source
                )

        for item in graph_results:

            if isinstance(item, dict):

                evidence_text = str(
                    item.get(
                        "evidence",
                        item.get(
                            "text",
                            ""
                        )
                    )
                ).strip()

                if evidence_text:

                    sources.append(
                        {
                            "document":
                                item.get(
                                    "document",
                                    ""
                                ),

                            "page":
                                item.get(
                                    "page",
                                    ""
                                ),

                            "chunk":
                                item.get(
                                    "chunk",
                                    ""
                                ),

                            "evidence":
                                evidence_text
                        }
                    )

        sources = _deduplicate_sources(
            sources
        )

        all_sources.extend(
            sources
        )

        # ----------------------------------------------------
        # Generate
        # ----------------------------------------------------

        if not evidence:

            print(
                "No evidence found."
            )

            content = ""

        else:

            try:

                print(
                    "Generating section..."
                )

                content = _generate_section(
                    section_name,
                    evidence
                )

            except Exception as exc:

                print()
                print(
                    f"WARNING: LLM generation failed "
                    f"for {section_name}"
                )

                print(
                    f"Error: {exc}"
                )

                content = ""

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

        method_statement[
            section_name
        ] = {

            "content":
                normalize_llm_content(
                    content
                ),

            "sources":
                sources
        }

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = {

        "method_statement":
            method_statement,

        "sources":
            _deduplicate_sources(
                all_sources
            )
    }

    print()
    print(
        "-" * 70
    )
    print(
        "METHOD STATEMENT DATA GENERATED"
    )
    print(
        "-" * 70
    )

    return result


# ============================================================
# BACKWARD-COMPATIBILITY ALIAS
# ============================================================

def generate_method_statement_data(
    retriever,
    *args,
    **kwargs
):

    return generate_method_statement(
        retriever,
        *args,
        **kwargs
    )