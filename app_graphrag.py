import re
import json
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import ollama

from graph.graph_builder import KnowledgeGraph
from graph.graph_store import GraphStore
from llm.entity_extractor import extract_knowledge
from normalizer.entity_completion import complete_entities
from normalizer.entity_linker import link_facts
from normalizer.entity_normalizer import normalize_entities, normalize_facts
from validator.fact_validator import validate_facts
from retrieval.graph_rag import GraphRAGRetriever

st.set_page_config(page_title="DocMindAI GraphRAG", layout="wide")

@st.cache_resource
def embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

def pages_from_pdf(data):
    reader = PdfReader(data)
    return [{"page": i, "text": re.sub(r"\\s+", " ", p.extract_text() or "").strip()}
            for i, p in enumerate(reader.pages, 1)]

def make_chunks(pages, document, size=1200, overlap=200):
    out = []
    n = 0
    for p in pages:
        text = p["text"]
        start = 0
        while text and start < len(text):
            end = min(start + size, len(text))
            part = text[start:end].strip()
            if part:
                out.append({"chunk": f"chunk_{n}", "page": p["page"], "text": part, "document": document})
                n += 1
            if end >= len(text):
                break
            start = end - overlap
    return out

def make_embeddings(chunks):
    if not chunks:
        return np.empty((0, 384))
    return np.asarray(embedding_model().encode(
        [x["text"] for x in chunks],
        normalize_embeddings=True,
        show_progress_bar=False,
    ))

def build_graph(chunks):
    graph = KnowledgeGraph()
    stats = {"raw_facts": 0, "valid_facts": 0, "rejected": 0}
    progress = st.progress(0.0, text="Building construction knowledge graph...")
    for i, chunk in enumerate(chunks, 1):
        try:
            raw = extract_knowledge(chunk["text"])
            entities = raw.get("entities", [])
            facts = raw.get("facts", [])
            valid, rejected = validate_facts(facts, chunk["text"])
            entities = normalize_entities(complete_entities(entities, valid))
            facts = normalize_facts(valid, entities)
            linked, _ = link_facts(facts, entities)
            graph.add_entities(entities)
            graph.add_facts(linked, document=chunk["document"], page=chunk["page"], chunk_id=chunk["chunk"])
            stats["raw_facts"] += len(facts)
            stats["valid_facts"] += len(linked)
            stats["rejected"] += len(rejected)
        except Exception:
            pass
        progress.progress(i / len(chunks))
    progress.empty()
    stats["nodes"] = graph.number_of_nodes()
    stats["edges"] = graph.number_of_edges()
    return graph, stats

def search(query):
    return GraphRAGRetriever(
        st.session_state.chunks,
        st.session_state.embeddings,
        embedding_model(),
        st.session_state.graph,
        vector_top_k=5,
        graph_top_k=6,
    ).search(query)

def evidence_text(result, limit=3000):
    return GraphRAGRetriever.format_evidence(result, max_chars_per_chunk=limit)

def llm_answer(question, result):
    prompt = f"""
You are DocMindAI.
Answer only from the retrieved evidence.
Do not use outside knowledge.
Use graph relationships for multi-hop reasoning.
If evidence is insufficient, say:
The uploaded document does not provide enough evidence to answer this question.
Preserve numerical values and standards.

QUESTION:
{question}

RETRIEVED EVIDENCE:
{evidence_text(result)}
"""
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()

def parse_json(text):
    text = str(text).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON returned by Llama 3.")
    depth = 0
    quoted = False
    escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if escaped:
            escaped = False
            continue
        if c == "\\" and quoted:
            escaped = True
            continue
        if c == '"':
            quoted = not quoted
        if quoted:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("Incomplete JSON returned by Llama 3.")

SECTION_QUERIES = {
    "purpose": "purpose objective intention method statement work",
    "scope": "scope applicability work covered construction activities",
    "acronyms_and_definitions": "acronyms abbreviations definitions terminology",
    "reference_documents": "reference documents standards specifications codes drawings annexures",
    "procedure_for_concreting": "procedure concreting batching mixing placing compaction curing stressing",
    "equipment_used": "equipment machinery tools mixers vibrators batchers jacks bar bending",
    "key_people_involved": "supervisor engineer inspecting officer personnel responsibilities approvals",
    "other_relevant_information": "inspection testing quality control calibration acceptance requirements",
}

def generate_method_statement():
    evidence = {}
    for section, query in SECTION_QUERIES.items():
        evidence[section] = search(query)

    blocks = []
    for section, result in evidence.items():
        blocks.append("SECTION: " + section.upper() + "\n" + evidence_text(result))

    prompt = f"""
Generate a professional RCC Method Statement using ONLY the supplied GraphRAG evidence.
Do not invent requirements or use outside knowledge.
Preserve numerical values and standards.
Return valid JSON only.

Required keys:
purpose, scope, acronyms_and_definitions, reference_documents,
procedure_for_concreting, equipment_used, key_people_involved,
other_relevant_information.

Each key must contain content and sources.
Sources must contain document, page and chunk.

GRAPH-RAG EVIDENCE:
{chr(10).join(blocks)}
"""
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}], format="json")
    return parse_json(response["message"]["content"])

def sources(items):
    out = []
    seen = set()
    for x in items:
        key = (x.get("document",""), x.get("page"), x.get("chunk",""))
        if key not in seen:
            seen.add(key)
            out.append(f"{key[0]} — Page {key[1]} — {key[2]}")
    return out

st.title("DocMindAI")
st.caption("Construction Specification Intelligence — GraphRAG | Generate + Ask + Verify")

for key, default in {
    "chunks": [], "embeddings": None, "graph": None,
    "graph_stats": None, "method": None, "history": [],
    "pdf_name": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

uploaded = st.file_uploader("Upload construction specification PDF", type=["pdf"], key="graphrag_pdf")

if uploaded and st.button("Process Document", type="primary"):
    pages = pages_from_pdf(uploaded)
    if not any(p["text"] for p in pages):
        st.error("The PDF does not contain readable text.")
        st.stop()
    st.session_state.pdf_name = uploaded.name
    st.session_state.chunks = make_chunks(pages, uploaded.name)
    with st.spinner("Building semantic index..."):
        st.session_state.embeddings = make_embeddings(st.session_state.chunks)
    st.session_state.graph = None
    st.session_state.method = None
    st.session_state.history = []
    st.success("Document processed successfully.")

if st.session_state.chunks:
    a,b,c = st.columns(3)
    a.metric("Pages", len({x["page"] for x in st.session_state.chunks}))
    b.metric("Chunks", len(st.session_state.chunks))
    c.metric("Vector Dimensions", st.session_state.embeddings.shape[1])

    st.header("1. Construction Knowledge Graph")
    st.caption("The graph is built from validated LLM-extracted entities and relationships. Every relationship keeps document, page and chunk provenance.")

    if st.session_state.graph is None and st.button("Build Knowledge Graph", type="primary"):
        try:
            st.session_state.graph, st.session_state.graph_stats = build_graph(st.session_state.chunks)
            path = Path(tempfile.mkdtemp()) / f"{Path(st.session_state.pdf_name).stem}_graph.json"
            GraphStore().save(st.session_state.graph, path)
            st.success(f"Graph built and stored locally: {path.name}")
        except Exception as e:
            st.error(f"Graph construction failed: {e}")

    if st.session_state.graph:
        s = st.session_state.graph_stats
        a,b,c,d = st.columns(4)
        a.metric("Graph Nodes", s["nodes"])
        b.metric("Graph Edges", s["edges"])
        c.metric("Valid Facts", s["valid_facts"])
        d.metric("Rejected Facts", s["rejected"])

        with st.expander("Graph relationships"):
            for i,(u,v,data) in enumerate(st.session_state.graph.graph.edges(data=True)):
                un = st.session_state.graph.graph.nodes[u].get("name",u)
                vn = st.session_state.graph.graph.nodes[v].get("name",v)
                st.write(f"{un} — {data.get('relation')} → {vn} | Page {data.get('page')} | {data.get('chunk_id')}")
                if i >= 99:
                    st.caption("Showing first 100 relationships.")
                    break

        st.header("2. GraphRAG Q&A")
        question = st.text_input("Ask a question about the specification", placeholder="Which standard governs the activity that requires bar bending equipment?")
        if st.button("Ask", type="primary") and question.strip():
            try:
                with st.spinner("Running vector + graph multi-hop retrieval..."):
                    result = search(question.strip())
                    answer = llm_answer(question.strip(), result)
                st.session_state.history.append((question.strip(), answer, result))
            except Exception as e:
                st.error(f"Q&A failed: {e}")

        for q,a,result in reversed(st.session_state.history):
            st.markdown("Question: " + q)
            st.write(a)
            src = sources(result.get("combined_evidence", []))
            if src:
                st.caption("Sources: " + " | ".join(src))
            with st.expander("Graph paths and relationships"):
                for item in result.get("graph_results", []):
                    st.write("Path: " + " → ".join(item.get("path", [])))
                    for rel in item.get("relationships", []):
                        st.write(f"{rel['subject']} — {rel['predicate']} → {rel['object']} | Page {rel.get('page')} | {rel.get('chunk')}")

        st.header("3. GraphRAG Method Statement")
        if st.button("Generate Method Statement", type="primary"):
            try:
                with st.spinner("Running GraphRAG retrieval for all sections and generating with Llama 3..."):
                    st.session_state.method = generate_method_statement()
                st.success("GraphRAG method statement generated.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

if st.session_state.method:
    st.header("4. Method Statement Preview")
    for key, title in [
        ("purpose","Purpose"),("scope","Scope"),
        ("acronyms_and_definitions","Acronyms & Definitions"),
        ("reference_documents","Reference Documents"),
        ("procedure_for_concreting","Procedure for Concreting"),
        ("equipment_used","Equipment Used"),("key_people_involved","Key People Involved"),
        ("other_relevant_information","Other Relevant Information"),
    ]:
        section = st.session_state.method.get(key,{})
        with st.expander(title, expanded=True):
            content = section.get("content","") if isinstance(section,dict) else section
            if isinstance(content,list):
                for item in content:
                    if isinstance(item,dict):
                        st.markdown("**" + str(item.get("title") or item.get("item") or item.get("role") or "") + "**")
                        st.write(item.get("description") or item.get("responsibility") or "")
                    else:
                        st.write(item)
            else:
                st.write(content)
            src = sources(section.get("sources",[])) if isinstance(section,dict) else []
            if src:
                st.caption("Source: " + " | ".join(src))

    if st.button("Create Word Document", type="primary"):
        try:
            from method_statement.docx_generator import generate_docx
            safe = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(st.session_state.pdf_name).stem)
            output = Path(tempfile.mkdtemp()) / f"{safe}_Method_Statement.docx"
            generate_docx(
                method_statement_data=st.session_state.method,
                output_path=output,
                source_document=st.session_state.pdf_name,
            )
            with open(output, "rb") as f:
                st.download_button("Download Word Document", f, file_name=output.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e:
            st.error(f"DOCX generation failed: {e}")
