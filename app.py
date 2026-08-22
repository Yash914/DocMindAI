import re
import json
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import ollama


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DocMindAI | Method Statement Generator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PROFESSIONAL UI
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .stApp {
        background: #F7F8FA;
        color: #202124;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 35px;
        padding-bottom: 50px;
    }

    /* ---------- TYPOGRAPHY ---------- */

    html, body, [class*="css"] {
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Arial,
            sans-serif;
    }

    h1, h2, h3 {
        color: #202124;
    }

    /* ---------- HEADER ---------- */

    .brand {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #1F4E78;
        margin-bottom: 2px;
    }

    .tagline {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 34px;
    }

    /* ---------- SECTION LABEL ---------- */

    .section-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: #6B7280;
        margin-top: 26px;
        margin-bottom: 8px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 650;
        color: #202124;
        margin-bottom: 5px;
    }

    .section-description {
        font-size: 13px;
        color: #6B7280;
        margin-bottom: 15px;
    }

    /* ---------- PANELS ---------- */

    .panel {
        background: #FFFFFF;
        border: 1px solid #DDE2E7;
        border-radius: 6px;
        padding: 24px;
        margin-bottom: 18px;
    }

    .document-panel {
        background: #FFFFFF;
        border: 1px solid #DDE2E7;
        border-radius: 6px;
        padding: 18px 20px;
        margin-top: 12px;
    }

    /* ---------- FILE INFO ---------- */

    .file-name {
        font-size: 15px;
        font-weight: 600;
        color: #202124;
    }

    .file-meta {
        font-size: 12px;
        color: #6B7280;
        margin-top: 3px;
    }

    .ready {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 4px;
        background: #EEF6F0;
        color: #276738;
        font-size: 11px;
        font-weight: 600;
    }

    /* ---------- METRICS ---------- */

    .metric {
        background: #FFFFFF;
        border: 1px solid #DDE2E7;
        border-radius: 6px;
        padding: 16px 18px;
    }

    .metric-label {
        font-size: 11px;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-value {
        font-size: 23px;
        font-weight: 650;
        color: #202124;
        margin-top: 3px;
    }

    /* ---------- PREVIEW ---------- */

    .preview-section {
        background: #FFFFFF;
        border: 1px solid #DDE2E7;
        border-radius: 6px;
        padding: 20px 22px;
        margin-bottom: 10px;
    }

    .preview-heading {
        font-size: 15px;
        font-weight: 650;
        color: #1F4E78;
        margin-bottom: 8px;
    }

    .preview-text {
        font-size: 13px;
        line-height: 1.65;
        color: #343A40;
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 5px;
        min-height: 40px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #1F4E78;
    }

    /* ---------- UPLOADER ---------- */

    [data-testid="stFileUploader"] {
        background: #FFFFFF;
        border: 1px solid #DDE2E7;
        border-radius: 6px;
        padding: 6px;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #FAFBFC;
        border: 1px dashed #B9C2CC;
        border-radius: 5px;
    }

    /* ---------- EXPANDER ---------- */

    .streamlit-expanderHeader {
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    /* ---------- ALERTS ---------- */

    .stAlert {
        border-radius: 5px;
    }

    /* ---------- FOOTER ---------- */

    .bottom-line {
        margin-top: 45px;
        padding-top: 15px;
        border-top: 1px solid #DDE2E7;
        color: #8A9199;
        font-size: 11px;
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="brand">DocMindAI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="tagline">'
    'Evidence-Grounded Construction Method Statement Generator'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "pdf_name": None,
    "pdf_data": None,
    "chunks": [],
    "embeddings": None,
    "method_statement": None,
    "docx_path": None,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# EMBEDDING MODEL
# ============================================================

@st.cache_resource
def load_embedding_model():

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_pages(pdf_bytes):

    reader = PdfReader(pdf_bytes)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

    return pages


# ============================================================
# CHUNKING
# ============================================================

def create_chunks(
    pages,
    chunk_size=1200,
    overlap=200,
):

    chunks = []

    chunk_id = 0

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        if not text:
            continue

        start = 0

        while start < len(text):

            end = min(
                start + chunk_size,
                len(text),
            )

            chunk_text = text[
                start:end
            ].strip()

            if chunk_text:

                chunks.append(
                    {
                        "chunk": f"chunk_{chunk_id}",
                        "page": page_number,
                        "text": chunk_text,
                    }
                )

                chunk_id += 1

            if end >= len(text):
                break

            start = end - overlap

    return chunks


# ============================================================
# EMBEDDINGS
# ============================================================

def build_embeddings(
    chunks,
    model,
):

    texts = [
        item["text"]
        for item in chunks
    ]

    if not texts:

        return np.empty(
            (0, 384)
        )

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return np.asarray(
        embeddings
    )


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(
    query,
    chunks,
    embeddings,
    model,
    top_k=5,
):

    if not chunks:
        return []

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    scores = np.dot(
        embeddings,
        query_embedding,
    )

    indices = np.argsort(
        scores
    )[::-1][:top_k]

    results = []

    for index in indices:

        result = dict(
            chunks[index]
        )

        result["score"] = float(
            scores[index]
        )

        results.append(result)

    return results


# ============================================================
# SECTION QUERIES
# ============================================================

SECTION_QUERIES = {

    "purpose":
        "purpose objective intention method statement work",

    "scope":
        "scope applicability work covered construction activities",

    "acronyms_and_definitions":
        "acronyms abbreviations definitions terminology",

    "reference_documents":
        "reference documents standards specifications codes drawings annexures",

    "procedure_for_concreting":
        "procedure concreting batching mixing placing compaction curing stressing",

    "equipment_used":
        "equipment machinery tools mixers vibrators batchers jacks",

    "key_people_involved":
        "supervisor engineer inspecting officer personnel responsibilities",

    "other_relevant_information":
        "inspection testing quality control calibration acceptance requirements",
}


# ============================================================
# EVIDENCE
# ============================================================

def build_evidence(
    chunks,
    embeddings,
    model,
):

    evidence = {}

    for section, query in SECTION_QUERIES.items():

        evidence[section] = retrieve(
            query,
            chunks,
            embeddings,
            model,
            top_k=5,
        )

    return evidence


def format_evidence(evidence):

    blocks = []

    for section, results in evidence.items():

        blocks.append(
            f"\n===== {section.upper()} ====="
        )

        for result in results:

            blocks.append(
                f"""
SOURCE:
Page: {result['page']}
Chunk: {result['chunk']}

TEXT:
{result['text']}
"""
            )

    return "\n".join(blocks)


# ============================================================
# LLM PROMPT
# ============================================================

def build_prompt(
    evidence_text,
):

    return f"""
You are DocMindAI, an expert construction-document
method statement generator.

Generate a professional RCC Method Statement using ONLY
the supplied specification evidence.

RULES:

1. Do not invent technical requirements.
2. Do not use outside knowledge.
3. Preserve numerical values exactly.
4. Preserve standards and specification references.
5. Summarize evidence instead of copying large passages.
6. Write useful engineering descriptions.
7. Keep the document concise enough for approximately
   2-6 pages.
8. Every section must be grounded in the evidence.
9. Return ONLY valid JSON.
10. Do not use markdown code fences.

Return exactly this structure:

{{
  "purpose": {{
    "content": "...",
    "sources": []
  }},

  "scope": {{
    "content": "...",
    "sources": []
  }},

  "acronyms_and_definitions": {{
    "content": [],
    "sources": []
  }},

  "reference_documents": {{
    "content": [],
    "sources": []
  }},

  "procedure_for_concreting": {{
    "content": [
      {{
        "title": "...",
        "description": "..."
      }}
    ],
    "sources": []
  }},

  "equipment_used": {{
    "content": [
      {{
        "item": "...",
        "description": "...",
        "calibration": "..."
      }}
    ],
    "sources": []
  }},

  "key_people_involved": {{
    "content": [
      {{
        "role": "...",
        "responsibility": "..."
      }}
    ],
    "sources": []
  }},

  "other_relevant_information": {{
    "content": [
      {{
        "item": "...",
        "description": "..."
      }}
    ],
    "sources": []
  }}
}}

For every source use:

{{
  "document": "uploaded PDF filename",
  "page": 1,
  "chunk": "chunk_0"
}}

Only cite evidence that actually supports the section.

SPECIFICATION EVIDENCE:

{evidence_text}
"""


# ============================================================
# JSON PARSER
# ============================================================

def extract_json(response):

    if isinstance(
        response,
        dict,
    ):
        return response

    text = str(
        response
    ).strip()

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```",
        "",
        text,
    ).strip()

    start = text.find("{")

    if start == -1:

        raise ValueError(
            "No JSON object found."
        )

    depth = 0
    in_string = False
    escape = False

    for index in range(
        start,
        len(text),
    ):

        char = text[index]

        if escape:

            escape = False
            continue

        if char == "\\" and in_string:

            escape = True
            continue

        if char == '"':

            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":

            depth += 1

        elif char == "}":

            depth -= 1

            if depth == 0:

                return json.loads(
                    text[
                        start:index + 1
                    ]
                )

    raise ValueError(
        "Could not extract complete JSON."
    )


# ============================================================
# GENERATE METHOD STATEMENT
# ============================================================

def generate_method_statement(
    evidence,
    pdf_name,
):

    prompt = build_prompt(
        format_evidence(evidence)
    )

    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        format="json",
    )

    result = extract_json(
        response["message"]["content"]
    )

    for section_data in result.values():

        if not isinstance(
            section_data,
            dict,
        ):
            continue

        for source in section_data.get(
            "sources",
            [],
        ):

            if isinstance(
                source,
                dict,
            ):

                if not source.get(
                    "document"
                ):

                    source[
                        "document"
                    ] = pdf_name

    return result


# ============================================================
# UPLOAD SECTION
# ============================================================

st.markdown(
    '<div class="section-label">Document</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    'Select specification'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-description">'
    'Upload the construction specification PDF that will '
    'be used as the source for the method statement.'
    '</div>',
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Choose PDF",
    type=["pdf"],
    label_visibility="collapsed",
)


# ============================================================
# PROCESS BUTTON
# ============================================================

if uploaded_file:

    st.markdown(
        '<div class="document-panel">',
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        [5, 1]
    )

    with left:

        st.markdown(
            f'<div class="file-name">'
            f'{uploaded_file.name}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="file-meta">'
            'PDF specification'
            '</div>',
            unsafe_allow_html=True,
        )

    with right:

        st.markdown(
            '<span class="ready">SELECTED</span>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button(
        "Process document",
        type="primary",
        use_container_width=True,
    ):

        try:

            with st.spinner(
                "Reading specification..."
            ):

                pages = extract_pdf_pages(
                    uploaded_file
                )

            valid_pages = [
                page
                for page in pages
                if page["text"]
            ]

            if not valid_pages:

                st.error(
                    "The PDF does not contain readable text."
                )

                st.stop()

            with st.spinner(
                "Preparing document for retrieval..."
            ):

                chunks = create_chunks(
                    pages
                )

            model = load_embedding_model()

            with st.spinner(
                "Building document index..."
            ):

                embeddings = build_embeddings(
                    chunks,
                    model
                )

            st.session_state.pdf_name = (
                uploaded_file.name
            )

            st.session_state.pdf_data = (
                uploaded_file.getvalue()
            )

            st.session_state.chunks = chunks

            st.session_state.embeddings = (
                embeddings
            )

            st.session_state.method_statement = None

            st.session_state.docx_path = None

            st.success(
                "Document processed successfully."
            )

        except Exception as error:

            st.error(
                f"Unable to process document: {error}"
            )


# ============================================================
# DOCUMENT STATUS
# ============================================================

if st.session_state.chunks:

    st.markdown(
        '<div class="section-label">'
        'Document Analysis'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Document ready'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'The specification has been prepared for '
        'evidence retrieval.'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    pages_count = len(
        set(
            item["page"]
            for item in st.session_state.chunks
        )
    )

    chunks_count = len(
        st.session_state.chunks
    )

    dimensions = (
        st.session_state.embeddings.shape[1]
    )

    with c1:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Pages</div>
                <div class="metric-value">
                    {pages_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Document Chunks</div>
                <div class="metric-value">
                    {chunks_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Vector Dimensions</div>
                <div class="metric-value">
                    {dimensions}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# GENERATION
# ============================================================

if st.session_state.chunks:

    st.markdown(
        '<div class="section-label">'
        'Method Statement'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Generate document'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Generate a structured method statement using '
        'evidence retrieved from the selected specification.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "Generate Method Statement",
        type="primary",
        use_container_width=True,
    ):

        try:

            model = load_embedding_model()

            with st.spinner(
                "Retrieving specification evidence..."
            ):

                evidence = build_evidence(
                    st.session_state.chunks,
                    st.session_state.embeddings,
                    model,
                )

            with st.spinner(
                "Generating method statement..."
            ):

                result = generate_method_statement(
                    evidence,
                    st.session_state.pdf_name,
                )

            st.session_state.method_statement = (
                result
            )

            st.success(
                "Method statement generated."
            )

        except Exception as error:

            st.error(
                f"Generation failed: {error}"
            )


# ============================================================
# PREVIEW
# ============================================================

if st.session_state.method_statement:

    result = (
        st.session_state.method_statement
    )

    st.markdown(
        '<div class="section-label">'
        'Preview'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Generated method statement'
        '</div>',
        unsafe_allow_html=True,
    )

    sections = [
        (
            "purpose",
            "Purpose",
        ),
        (
            "scope",
            "Scope",
        ),
        (
            "acronyms_and_definitions",
            "Acronyms & Definitions",
        ),
        (
            "reference_documents",
            "Reference Documents",
        ),
        (
            "procedure_for_concreting",
            "Procedure for Concreting",
        ),
        (
            "equipment_used",
            "Equipment Used",
        ),
        (
            "key_people_involved",
            "Key People Involved",
        ),
        (
            "other_relevant_information",
            "Other Relevant Information",
        ),
    ]

    for key, title in sections:

        section = result.get(
            key,
            {},
        )

        if not isinstance(
            section,
            dict,
        ):
            continue

        content = section.get(
            "content",
            "",
        )

        with st.expander(
            title,
            expanded=True,
        ):

            if isinstance(
                content,
                str,
            ):

                st.markdown(
                    f"""
                    <div class="preview-text">
                    {content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif isinstance(
                content,
                list,
            ):

                for item in content:

                    if isinstance(
                        item,
                        dict,
                    ):

                        title_text = (
                            item.get("title")
                            or item.get("item")
                            or item.get("role")
                            or ""
                        )

                        description = (
                            item.get("description")
                            or item.get("responsibility")
                            or ""
                        )

                        if title_text:

                            st.markdown(
                                f"**{title_text}**"
                            )

                        if description:

                            st.write(
                                description
                            )

                    else:

                        st.write(
                            item
                        )

            sources = section.get(
                "sources",
                [],
            )

            if sources:

                source_items = []

                for source in sources:

                    if isinstance(
                        source,
                        dict,
                    ):

                        source_items.append(
                            f"{source.get('document', st.session_state.pdf_name)}"
                            f" — Page {source.get('page', '?')}"
                        )

                if source_items:

                    st.caption(
                        "Source: "
                        + "; ".join(
                            source_items
                        )
                    )


# ============================================================
# EXPORT
# ============================================================

if st.session_state.method_statement:

    st.markdown(
        '<div class="section-label">'
        'Output'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Export document'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Create the formatted Word document for submission or review.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "Create Word Document",
        type="primary",
        use_container_width=True,
    ):

        try:

            from method_statement.docx_generator import (
                generate_docx
            )

            temp_dir = Path(
                tempfile.mkdtemp()
            )

            safe_name = re.sub(
                r"[^a-zA-Z0-9_-]",
                "_",
                Path(
                    st.session_state.pdf_name
                ).stem,
            )

            output_path = (
                temp_dir
                / f"{safe_name}_Method_Statement.docx"
            )

            generate_docx(
                method_statement_data=(
                    st.session_state.method_statement
                ),
                output_path=output_path,
                source_document=(
                    st.session_state.pdf_name
                ),
            )

            st.session_state.docx_path = (
                output_path
            )

            with open(
                output_path,
                "rb",
            ) as file:

                st.download_button(
                    label="Download Word Document",
                    data=file,
                    file_name=(
                        f"{safe_name}_Method_Statement.docx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.wordprocessingml.document"
                    ),
                    use_container_width=True,
                )

            st.success(
                "Word document created successfully."
            )

        except Exception as error:

            st.error(
                f"DOCX generation failed: {error}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="bottom-line">
        DocMindAI &nbsp;|&nbsp;
        Evidence-Grounded Construction Documentation
    </div>
    """,
    unsafe_allow_html=True,
)