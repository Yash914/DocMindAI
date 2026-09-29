import re
import json
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
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


def render_interactive_graph(graph):
    """Professional interactive SVG view of the actual NetworkX GraphRAG graph."""
    nodes = [
        {"id": n, "name": d.get("name", n), "type": d.get("entity_type", "Entity")}
        for n, d in graph.graph.nodes(data=True)
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "relation": d.get("relation", "RELATED_TO"),
            "confidence": float(d.get("confidence", 0.0)),
            "document": d.get("document", ""),
            "page": d.get("page", ""),
            "chunk": d.get("chunk_id", ""),
            "evidence": d.get("evidence", ""),
        }
        for u, v, d in graph.graph.edges(data=True)
    ]
    payload = json.dumps({"nodes": nodes, "edges": edges})

    html = """<!doctype html><html><head><meta charset="utf-8">
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#172033;background:#fff}
.shell{border:1px solid #d9dee7;border-radius:8px;overflow:hidden;background:#fff}
.toolbar{height:48px;display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid #e4e7ec;background:#fafbfc}
button{border:1px solid #cfd5df;background:#fff;color:#263247;border-radius:5px;padding:6px 10px;font-size:13px;cursor:pointer}
button:hover{background:#f1f4f8}.status{margin-left:auto;color:#667085;font-size:12px}
.main{display:flex;min-height:610px}.viewport{flex:1;min-width:0;height:610px;overflow:hidden;background:#fcfcfd}
svg{width:100%;height:100%;display:block;cursor:grab}svg.dragging{cursor:grabbing}
.edge{stroke:#98a2b3;fill:none}.edge-label{font-size:10px;fill:#667085;text-anchor:middle;pointer-events:none}
.node{stroke:#fff;stroke-width:2;cursor:pointer}.node-label{font-size:11px;font-weight:600;fill:#344054;text-anchor:middle;pointer-events:none}
.detail{width:285px;border-left:1px solid #e4e7ec;background:#fff;padding:18px}
.detail h3{margin:0 0 5px;font-size:15px;color:#101828}.detail .type{color:#667085;font-size:12px;margin-bottom:18px}
.row{padding:9px 0;border-top:1px solid #edf0f4}.label{display:block;color:#667085;font-size:11px;margin-bottom:3px;text-transform:uppercase;letter-spacing:.04em}
.value{color:#1d2939;font-size:13px;line-height:1.4;word-break:break-word}.conf{font-weight:700;color:#175cd3}
.legend{display:flex;gap:14px;flex-wrap:wrap;padding:9px 12px;border-bottom:1px solid #e4e7ec;color:#667085;font-size:11px}
.dot{width:8px;height:8px;display:inline-block;border-radius:50%;margin-right:4px}.note{padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid #e4e7ec}
</style></head><body><div class="shell">
<div class="toolbar"><button id="zin">Zoom in</button><button id="zout">Zoom out</button><button id="fit">Fit graph</button><button id="reset">Reset</button><span class="status" id="status"></span></div>
<div class="legend"><span><i class="dot" style="background:#3b82f6"></i>Activity</span><span><i class="dot" style="background:#16a34a"></i>Material</span><span><i class="dot" style="background:#d97706"></i>Equipment</span><span><i class="dot" style="background:#7c3aed"></i>Standard</span><span><i class="dot" style="background:#dc2626"></i>Requirement</span><span><i class="dot" style="background:#64748b"></i>Other</span></div>
<div class="main"><div class="viewport"><svg id="graph" viewBox="0 0 1000 650"></svg></div><aside class="detail" id="detail"><h3>Knowledge Graph</h3><div class="type">Select a node or relationship</div><div class="row"><span class="label">Interaction</span><span class="value">Drag nodes, scroll to zoom, and select a relationship for provenance.</span></div></aside></div>
<div class="note">Confidence represents evidence support for the extracted relationship; it is not a statistical probability.</div></div>
<script>
const DATA=__DATA__;
const svg=document.getElementById("graph"),detail=document.getElementById("detail"),status=document.getElementById("status"),ns="http://www.w3.org/2000/svg";
const colors={Activity:"#3b82f6",Material:"#16a34a",Equipment:"#d97706",Standard:"#7c3aed",Requirement:"#dc2626"};
let scale=1,ox=0,oy=0,drag=null;
const nodes=DATA.nodes.map(n=>Object.assign({},n,{x:0,y:0})),map=Object.fromEntries(nodes.map(n=>[n.id,n])),edges=DATA.edges;
function init(){nodes.forEach((n,i)=>{const a=i*2.399963,r=150+Math.min(180,i*6);n.x=500+Math.cos(a)*r;n.y=325+Math.sin(a)*r*.72});}
function esc(s){return String(s||"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));}
function render(){
 svg.innerHTML="";const g=document.createElementNS(ns,"g");g.setAttribute("transform","translate("+ox+","+oy+") scale("+scale+")");svg.appendChild(g);
 edges.forEach(e=>{const a=map[e.source],b=map[e.target];if(!a||!b)return;
  const l=document.createElementNS(ns,"line");l.classList.add("edge");l.setAttribute("x1",a.x);l.setAttribute("y1",a.y);l.setAttribute("x2",b.x);l.setAttribute("y2",b.y);l.style.strokeWidth=String(1+e.confidence*2);l.style.opacity=String(.35+e.confidence*.55);l.onclick=x=>{x.stopPropagation();showEdge(e,a,b)};g.appendChild(l);
  const t=document.createElementNS(ns,"text");t.classList.add("edge-label");t.setAttribute("x",(a.x+b.x)/2);t.setAttribute("y",(a.y+b.y)/2-5);t.textContent=e.relation+" · "+Math.round(e.confidence*100)+"%";g.appendChild(t);
 });
 nodes.forEach(n=>{const c=document.createElementNS(ns,"circle");c.classList.add("node");c.setAttribute("cx",n.x);c.setAttribute("cy",n.y);c.setAttribute("r",24);c.setAttribute("fill",colors[n.type]||"#64748b");c.onpointerdown=e=>{drag={n:n,x:e.clientX,y:e.clientY};e.stopPropagation()};c.onclick=e=>{e.stopPropagation();showNode(n)};g.appendChild(c);
  const t=document.createElementNS(ns,"text");t.classList.add("node-label");t.setAttribute("x",n.x);t.setAttribute("y",n.y+40);t.textContent=n.name.length>27?n.name.slice(0,25)+"…":n.name;g.appendChild(t);
 });
 status.textContent=nodes.length+" nodes · "+edges.length+" relationships";
}
function showNode(n){const links=edges.filter(e=>e.source===n.id||e.target===n.id);detail.innerHTML="<h3>"+esc(n.name)+"</h3><div class='type'>"+esc(n.type)+"</div>"+links.slice(0,12).map(e=>"<div class='row'><span class='label'>"+esc(e.relation)+"</span><span class='value conf'>"+Math.round(e.confidence*100)+"% confidence</span><span class='value'>"+esc(e.document)+" · Page "+esc(e.page)+" · "+esc(e.chunk)+"</span></div>").join("");}
function showEdge(e,a,b){detail.innerHTML="<h3>"+esc(e.relation)+"</h3><div class='type'>"+esc(a.name)+" → "+esc(b.name)+"</div><div class='row'><span class='label'>Confidence</span><span class='value conf'>"+Math.round(e.confidence*100)+"%</span></div><div class='row'><span class='label'>Source</span><span class='value'>"+esc(e.document)+"<br>Page "+esc(e.page)+" · "+esc(e.chunk)+"</span></div><div class='row'><span class='label'>Evidence</span><span class='value'>"+esc(e.evidence)+"</span></div>";}
svg.onpointermove=e=>{if(!drag)return;drag.n.x+=(e.clientX-drag.x)/scale;drag.n.y+=(e.clientY-drag.y)/scale;drag.x=e.clientX;drag.y=e.clientY;render()};svg.onpointerup=()=>drag=null;svg.onpointerleave=()=>drag=null;
svg.onwheel=e=>{e.preventDefault();scale=Math.max(.45,Math.min(2.2,scale*(e.deltaY<0?1.1:.9)));render()}; 
function fit(){if(!nodes.length)return;const xs=nodes.map(n=>n.x),ys=nodes.map(n=>n.y),minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);scale=Math.min(.95,Math.min(900/Math.max(1,maxx-minx),560/Math.max(1,maxy-miny)));ox=500-(minx+maxx)*scale/2;oy=325-(miny+maxy)*scale/2;render();}
document.getElementById("zin").onclick=()=>{scale=Math.min(2.2,scale*1.2);render()};document.getElementById("zout").onclick=()=>{scale=Math.max(.45,scale/1.2);render()};document.getElementById("fit").onclick=fit;document.getElementById("reset").onclick=()=>{scale=1;ox=0;oy=0;init();render()};init();render();fit();
</script></body></html>"""
    html = html.replace("__DATA__", payload)
    components.html(html, height=700, scrolling=False)

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

        st.subheader("Interactive Knowledge Graph")
        st.caption("Drag nodes • scroll to zoom • select a relationship for confidence and document provenance.")
        render_interactive_graph(st.session_state.graph)

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
