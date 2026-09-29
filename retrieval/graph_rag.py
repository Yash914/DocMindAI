import numpy as np
from retrieval.graph_retriever import GraphRetriever


class GraphRAGRetriever:
    """Hybrid Vector + Knowledge Graph retrieval with source-chunk recovery."""

    def __init__(self, chunks, embeddings, embedding_model, graph, vector_top_k=5, graph_top_k=6):
        self.chunks = chunks
        self.embeddings = np.asarray(embeddings)
        self.embedding_model = embedding_model
        self.graph = graph
        self.graph_retriever = GraphRetriever(graph, max_hops=3)
        self.vector_top_k = vector_top_k
        self.graph_top_k = graph_top_k

    @staticmethod
    def _chunk_id(chunk):
        return chunk.get("chunk", chunk.get("chunk_id", ""))

    @staticmethod
    def _page(chunk):
        return chunk.get("page", chunk.get("page_number"))

    def vector_search(self, query, top_k=None):
        top_k = top_k or self.vector_top_k
        if not self.chunks or self.embeddings.size == 0:
            return []
        q = self.embedding_model.encode(query, normalize_embeddings=True, show_progress_bar=False)
        scores = np.dot(self.embeddings, q)
        indices = np.argsort(scores)[::-1][:top_k]
        return [{
            "type": "vector",
            "score": float(scores[int(i)]),
            "document": self.chunks[int(i)].get("document", ""),
            "page": self._page(self.chunks[int(i)]),
            "chunk": self._chunk_id(self.chunks[int(i)]),
            "text": self.chunks[int(i)].get("text", ""),
            "retrieval_modes": ["vector"],
        } for i in indices]

    def _graph_to_chunks(self, graph_results):
        lookup = {
            (c.get("document", ""), self._page(c), self._chunk_id(c)): c
            for c in self.chunks
        }
        by_key = {}
        for item in graph_results:
            for p in item.get("provenance", []):
                key = (p.get("document", ""), p.get("page"), p.get("chunk", ""))
                chunk = lookup.get(key)
                if not chunk and p.get("chunk"):
                    chunk = next(
                        (c for c in self.chunks if self._chunk_id(c) == p["chunk"]),
                        None,
                    )
                if chunk:
                    by_key[key] = {
                        "type": "graph_evidence",
                        "score": float(item.get("score", 0)),
                        "document": chunk.get("document", p.get("document", "")),
                        "page": self._page(chunk),
                        "chunk": self._chunk_id(chunk),
                        "text": chunk.get("text", ""),
                        "path": item.get("path", []),
                        "relationships": item.get("relationships", []),
                        "retrieval_modes": ["graph"],
                    }
        return list(by_key.values())

    def search(self, query):
        vector_results = self.vector_search(query)
        graph_results = self.graph_retriever.search(query, self.graph_top_k)
        graph_chunks = self._graph_to_chunks(graph_results)

        by_key = {}
        for item in vector_results:
            key = (item["document"], item["page"], item["chunk"])
            by_key[key] = dict(item)

        for item in graph_chunks:
            key = (item["document"], item["page"], item["chunk"])
            if key in by_key:
                by_key[key]["graph_score"] = item["score"]
                by_key[key]["retrieval_modes"] = ["vector", "graph"]
                by_key[key]["retrieval_score"] = by_key[key]["score"] + 0.25 * item["score"]
                by_key[key]["graph_paths"] = [item["path"]]
                by_key[key]["graph_relationships"] = item["relationships"]
            else:
                item["retrieval_score"] = 0.75 * item["score"]
                by_key[key] = item

        for item in by_key.values():
            item.setdefault("retrieval_score", item["score"])

        return {
            "query": query,
            "vector_results": vector_results,
            "graph_results": graph_results,
            "graph_chunks": graph_chunks,
            "combined_evidence": sorted(
                by_key.values(),
                key=lambda x: x.get("retrieval_score", 0),
                reverse=True,
            ),
        }

    @staticmethod
    def format_evidence(results, max_chars_per_chunk=3500):
        blocks = []
        for item in results.get("combined_evidence", []):
            text = item.get("text", "")
            if len(text) > max_chars_per_chunk:
                text = text[:max_chars_per_chunk] + "..."
            blocks.append(
                f"SOURCE TYPE: {item.get('type')}\n"
                f"DOCUMENT: {item.get('document', '')}\n"
                f"PAGE: {item.get('page', '')}\n"
                f"CHUNK: {item.get('chunk', '')}\n"
                f"RETRIEVAL MODES: {', '.join(item.get('retrieval_modes', []))}\n"
                f"GRAPH PATH: {' -> '.join(item.get('path', []))}\n"
                f"TEXT:\n{text}\n"
            )

        for item in results.get("graph_results", []):
            for rel in item.get("relationships", []):
                blocks.append(
                    f"GRAPH FACT\n"
                    f"{rel['subject']} --{rel['predicate']}--> {rel['object']}\n"
                    f"DOCUMENT: {rel.get('document','')}\n"
                    f"PAGE: {rel.get('page','')}\n"
                    f"CHUNK: {rel.get('chunk','')}\n"
                    f"EVIDENCE: {rel.get('evidence','')}\n"
                )
        return "\n".join(blocks)
