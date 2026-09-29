import re
import json
from io import BytesIO
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader

from graph.graph_builder import KnowledgeGraph
from llm.entity_extractor import extract_knowledge
from normalizer.entity_completion import complete_entities
from normalizer.entity_linker import link_facts
from normalizer.entity_normalizer import normalize_entities, normalize_facts
from validator.fact_validator import validate_facts

st.set_page_config(page_title="DocMindAI — Knowledge Graph", layout="wide")

def pages_from_pdf(data):
    reader = PdfReader(BytesIO(data))
    return [
        {
            "page": i,
            "text": re.sub(r"\s+", " ", page.extract_text() or "").strip(),
        }
        for i, page in enumerate(reader.pages, 1)
    ]

def make_chunks(pages, document, size=1400, overlap=200):
    chunks = []
    index = 0

    for page in pages:
        text = page["text"]
        start = 0

        while text and start < len(text):
            end = min(start + size, len(text))
            part = text[start:end].strip()

            if part:
                chunks.append({
                    "chunk": f"chunk_{index}",
                    "page": page["page"],
                    "text": part,
                    "document": document,
                })
                index += 1

            if end >= len(text):
                break

            start = end - overlap

    return chunks

def build_graph(chunks):
    graph = KnowledgeGraph()
    errors = []

    progress = st.progress(0.0, text="Building construction knowledge graph...")

    for i, chunk in enumerate(chunks, 1):
        try:
            raw = extract_knowledge(chunk["text"])

            entities = raw.get("entities", [])
            facts = raw.get("facts", [])

            valid, rejected = validate_facts(facts, chunk["text"])
            entities = normalize_entities(
                complete_entities(entities, valid)
            )
            facts = normalize_facts(valid, entities)
            linked, _ = link_facts(facts, entities)

            graph.add_entities(entities)
            graph.add_facts(
                linked,
                document=chunk["document"],
                page=chunk["page"],
                chunk_id=chunk["chunk"],
            )

        except Exception as exc:
            errors.append({
                "page": chunk["page"],
                "chunk": chunk["chunk"],
                "error": str(exc),
            })

        progress.progress(i / len(chunks))

    progress.empty()
    return graph, errors

def render_graph(graph):
    nodes = [
        {
            "id": node,
            "name": data.get("name", node),
            "type": data.get("entity_type", "Entity"),
        }
        for node, data in graph.graph.nodes(data=True)
    ]

    edges = [
        {
            "source": source,
            "target": target,
            "relation": data.get("relation", "RELATED_TO"),
            "confidence": float(data.get("confidence", 0.0)),
            "document": data.get("document", ""),
            "page": data.get("page", ""),
            "chunk": data.get("chunk_id", ""),
            "evidence": data.get("evidence", ""),
        }
        for source, target, data in graph.graph.edges(data=True)
    ]

    payload = json.dumps({"nodes": nodes, "edges": edges})

    html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#172033;background:#fff}
.shell{border:1px solid #d9dee7;border-radius:8px;overflow:hidden;background:#fff}
.toolbar{height:48px;display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid #e4e7ec;background:#fafbfc}
button{border:1px solid #cfd5df;background:#fff;color:#263247;border-radius:5px;padding:6px 10px;font-size:13px;cursor:pointer}
button:hover{background:#f1f4f8}
.status{margin-left:auto;color:#667085;font-size:12px}
.main{display:flex;min-height:620px}
.viewport{flex:1;min-width:0;height:620px;overflow:hidden;background:#fcfcfd}
svg{width:100%;height:100%;display:block;cursor:grab}
svg.dragging{cursor:grabbing}
.edge{stroke:#98a2b3;fill:none}
.edge-label{font-size:10px;fill:#667085;text-anchor:middle;pointer-events:none}
.node{stroke:#fff;stroke-width:2;cursor:pointer}
.node-label{font-size:11px;font-weight:600;fill:#344054;text-anchor:middle;pointer-events:none}
.detail{width:300px;border-left:1px solid #e4e7ec;background:#fff;padding:18px}
.detail h3{margin:0 0 5px;font-size:15px;color:#101828}
.detail .type{color:#667085;font-size:12px;margin-bottom:18px}
.row{padding:9px 0;border-top:1px solid #edf0f4}
.label{display:block;color:#667085;font-size:11px;margin-bottom:3px;text-transform:uppercase;letter-spacing:.04em}
.value{color:#1d2939;font-size:13px;line-height:1.4;word-break:break-word}
.conf{font-weight:700;color:#175cd3}
.legend{display:flex;gap:14px;flex-wrap:wrap;padding:9px 12px;border-bottom:1px solid #e4e7ec;color:#667085;font-size:11px}
.dot{width:8px;height:8px;display:inline-block;border-radius:50%;margin-right:4px}
.note{padding:9px 12px;font-size:11px;color:#667085;border-top:1px solid #e4e7ec}
</style>
</head>
<body>
<div class="shell">
<div class="toolbar">
<button id="zin">Zoom in</button>
<button id="zout">Zoom out</button>
<button id="fit">Fit graph</button>
<button id="reset">Reset</button>
<span class="status" id="status"></span>
</div>

<div class="legend">
<span><i class="dot" style="background:#3b82f6"></i>Activity</span>
<span><i class="dot" style="background:#16a34a"></i>Material</span>
<span><i class="dot" style="background:#d97706"></i>Equipment</span>
<span><i class="dot" style="background:#7c3aed"></i>Standard</span>
<span><i class="dot" style="background:#dc2626"></i>Requirement</span>
<span><i class="dot" style="background:#64748b"></i>Other</span>
</div>

<div class="main">
<div class="viewport">
<svg id="graph" viewBox="0 0 1000 650"></svg>
</div>

<aside class="detail" id="detail">
<h3>Knowledge Graph</h3>
<div class="type">Select a node or relationship</div>
<div class="row">
<span class="label">Interaction</span>
<span class="value">Drag nodes, scroll to zoom, and select a relationship to inspect its provenance.</span>
</div>
</aside>
</div>

<div class="note">
Confidence represents evidence support for the extracted relationship; it is not a statistical probability.
</div>
</div>

<script>
const DATA=__DATA__;
const svg=document.getElementById("graph");
const detail=document.getElementById("detail");
const status=document.getElementById("status");
const ns="http://www.w3.org/2000/svg";

const colors={
Activity:"#3b82f6",
Material:"#16a34a",
Equipment:"#d97706",
Standard:"#7c3aed",
Requirement:"#dc2626"
};

let scale=1, ox=0, oy=0, drag=null;

const nodes=DATA.nodes.map(n=>Object.assign({},n,{x:0,y:0}));
const map=Object.fromEntries(nodes.map(n=>[n.id,n]));
const edges=DATA.edges;

function init(){
    nodes.forEach((n,i)=>{
        const a=i*2.399963;
        const r=150+Math.min(180,i*6);
        n.x=500+Math.cos(a)*r;
        n.y=325+Math.sin(a)*r*.72;
    });
}

function esc(s){
    return String(s||"").replace(/[&<>"]/g,m=>({
        "&":"&amp;",
        "<":"&lt;",
        ">":"&gt;",
        '"':"&quot;"
    }[m]));
}

function render(){
    svg.innerHTML="";
    const g=document.createElementNS(ns,"g");
    g.setAttribute("transform","translate("+ox+","+oy+") scale("+scale+")");
    svg.appendChild(g);

    edges.forEach(e=>{
        const a=map[e.source], b=map[e.target];
        if(!a||!b)return;

        const line=document.createElementNS(ns,"line");
        line.classList.add("edge");
        line.setAttribute("x1",a.x);
        line.setAttribute("y1",a.y);
        line.setAttribute("x2",b.x);
        line.setAttribute("y2",b.y);
        line.style.strokeWidth=String(1+e.confidence*2);
        line.style.opacity=String(.35+e.confidence*.55);
        line.onclick=x=>{
            x.stopPropagation();
            showEdge(e,a,b);
        };
        g.appendChild(line);

        const label=document.createElementNS(ns,"text");
        label.classList.add("edge-label");
        label.setAttribute("x",(a.x+b.x)/2);
        label.setAttribute("y",(a.y+b.y)/2-5);
        label.textContent=e.relation+" · "+Math.round(e.confidence*100)+"%";
        g.appendChild(label);
    });

    nodes.forEach(n=>{
        const circle=document.createElementNS(ns,"circle");
        circle.classList.add("node");
        circle.setAttribute("cx",n.x);
        circle.setAttribute("cy",n.y);
        circle.setAttribute("r",24);
        circle.setAttribute("fill",colors[n.type]||"#64748b");

        circle.onpointerdown=e=>{
            drag={n:n,x:e.clientX,y:e.clientY};
            e.stopPropagation();
        };

        circle.onclick=e=>{
            e.stopPropagation();
            showNode(n);
        };

        g.appendChild(circle);

        const label=document.createElementNS(ns,"text");
        label.classList.add("node-label");
        label.setAttribute("x",n.x);
        label.setAttribute("y",n.y+40);
        label.textContent=n.name.length>27?n.name.slice(0,25)+"…":n.name;
        g.appendChild(label);
    });

    status.textContent=nodes.length+" nodes · "+edges.length+" relationships";
}

function showNode(n){
    const links=edges.filter(e=>e.source===n.id||e.target===n.id);

    detail.innerHTML="<h3>"+esc(n.name)+"</h3><div class='type'>"+esc(n.type)+"</div>"+
        links.slice(0,12).map(e=>
            "<div class='row'>"+
            "<span class='label'>"+esc(e.relation)+"</span>"+
            "<span class='value conf'>"+Math.round(e.confidence*100)+"% confidence</span>"+
            "<span class='value'>"+esc(e.document)+" · Page "+esc(e.page)+" · "+esc(e.chunk)+"</span>"+
            "</div>"
        ).join("");
}

function showEdge(e,a,b){
    detail.innerHTML=
        "<h3>"+esc(e.relation)+"</h3>"+
        "<div class='type'>"+esc(a.name)+" → "+esc(b.name)+"</div>"+
        "<div class='row'><span class='label'>Confidence</span><span class='value conf'>"+
        Math.round(e.confidence*100)+"%</span></div>"+
        "<div class='row'><span class='label'>Source</span><span class='value'>"+
        esc(e.document)+"<br>Page "+esc(e.page)+" · "+esc(e.chunk)+"</span></div>"+
        "<div class='row'><span class='label'>Evidence</span><span class='value'>"+
        esc(e.evidence)+"</span></div>";
}

svg.onpointermove=e=>{
    if(!drag)return;
    drag.n.x+=(e.clientX-drag.x)/scale;
    drag.n.y+=(e.clientY-drag.y)/scale;
    drag.x=e.clientX;
    drag.y=e.clientY;
    render();
};

svg.onpointerup=()=>drag=null;
svg.onpointerleave=()=>drag=null;

svg.onwheel=e=>{
    e.preventDefault();
    scale=Math.max(.45,Math.min(2.2,scale*(e.deltaY<0?1.1:.9)));
    render();
};

function fit(){
    if(!nodes.length)return;

    const xs=nodes.map(n=>n.x);
    const ys=nodes.map(n=>n.y);
    const minx=Math.min(...xs),maxx=Math.max(...xs);
    const miny=Math.min(...ys),maxy=Math.max(...ys);

    scale=Math.min(
        .95,
        Math.min(
            900/Math.max(1,maxx-minx),
            560/Math.max(1,maxy-miny)
        )
    );

    ox=500-(minx+maxx)*scale/2;
    oy=325-(miny+maxy)*scale/2;
    render();
}

document.getElementById("zin").onclick=()=>{
    scale=Math.min(2.2,scale*1.2);
    render();
};

document.getElementById("zout").onclick=()=>{
    scale=Math.max(.45,scale/1.2);
    render();
};

document.getElementById("fit").onclick=fit;

document.getElementById("reset").onclick=()=>{
    scale=1;
    ox=0;
    oy=0;
    init();
    render();
};

init();
render();
fit();
</script>
</body>
</html>"""

    components.html(
        html.replace("__DATA__", payload),
        height=700,
        scrolling=False,
    )

st.title("DocMindAI")
st.caption("Construction Specification Intelligence — Knowledge Graph")

for key, default in {
    "graph": None,
    "graph_errors": [],
    "pdf_name": None,
    "pages": 0,
    "chunks": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

uploaded = st.file_uploader(
    "Upload construction specification PDF",
    type=["pdf"],
    key="knowledge_graph_pdf",
)

if uploaded and st.button("Process PDF & Build Graph", type="primary"):
    try:
        pdf_bytes = uploaded.getvalue()

        with st.spinner("Reading construction specification..."):
            pages = pages_from_pdf(pdf_bytes)

        readable_pages = [p for p in pages if p["text"]]

        if not readable_pages:
            st.error("No readable text was found in this PDF.")
            st.stop()

        chunks = make_chunks(readable_pages, uploaded.name)

        st.session_state.pdf_name = uploaded.name
        st.session_state.pages = len(pages)
        st.session_state.chunks = len(chunks)

        with st.spinner(
            f"Extracting construction entities and relationships from {len(chunks)} chunks..."
        ):
            graph, errors = build_graph(chunks)

        st.session_state.graph = graph
        st.session_state.graph_errors = errors

        if graph.number_of_nodes() == 0:
            st.error(
                "No graph entities were extracted. Make sure Ollama is running and Llama 3 is available."
            )
        else:
            st.success(
                f"Knowledge graph created from {len(pages)} pages and {len(chunks)} chunks."
            )

    except Exception as exc:
        st.error("Graph construction failed.")
        st.exception(exc)

if st.session_state.graph is not None:
    graph = st.session_state.graph

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages", st.session_state.pages)
    c2.metric("Chunks", st.session_state.chunks)
    c3.metric("Graph Nodes", graph.number_of_nodes())
    c4.metric("Relationships", graph.number_of_edges())

    if st.session_state.graph_errors:
        with st.expander(
            f"Skipped chunks ({len(st.session_state.graph_errors)})"
        ):
            for item in st.session_state.graph_errors[:20]:
                st.write(
                    f"Page {item['page']} · {item['chunk']}: {item['error']}"
                )

    st.subheader("Interactive Construction Knowledge Graph")
    st.caption(
        "Drag nodes • scroll to zoom • use Fit Graph • click nodes or relationships for provenance."
    )
    render_graph(graph)
