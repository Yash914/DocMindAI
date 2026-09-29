import re
from collections import deque

STOPWORDS = {
    "what","which","where","when","why","how","does","do","the","a","an",
    "is","are","was","were","for","to","of","in","on","and","or","that",
    "this","with","from","must","should","can","be","by","about","requirements",
}


class GraphRetriever:
    """Multi-hop retrieval over the construction knowledge graph."""

    def __init__(self, graph, max_hops=3):
        self.graph = graph
        self.max_hops = max_hops

    @staticmethod
    def _tokens(text):
        return {
            x for x in re.findall(r"[a-zA-Z0-9:_./-]+", str(text).lower())
            if len(x) > 2 and x not in STOPWORDS
        }

    def _entity_score(self, name, query):
        a, b = self._tokens(name), self._tokens(query)
        if not a or not b:
            return 0.0
        return len(a & b) * 2.0 + (3.0 if str(name).lower() in str(query).lower() else 0.0)

    def find_entities(self, query, limit=8):
        rows = []
        for node_id, data in self.graph.graph.nodes(data=True):
            name = data.get("name", node_id)
            score = self._entity_score(name, query)
            if score > 0:
                rows.append((score, node_id, name, data.get("entity_type", "Entity")))
        rows.sort(reverse=True)
        return [
            {"node_id": n, "name": name, "type": typ, "score": score}
            for score, n, name, typ in rows[:limit]
        ]

    def _neighbors(self, node_id):
        for target, keyed in self.graph.graph[node_id].items():
            for edge in keyed.values():
                yield node_id, target, edge
        for source, keyed in self.graph.graph.pred[node_id].items():
            for edge in keyed.values():
                yield source, node_id, edge

    def _result(self, nodes, edges, score):
        path = [self.graph.graph.nodes[n].get("name", n) for n in nodes]
        relationships, provenance = [], []
        for source, target, edge in edges:
            rel = {
                "subject": self.graph.graph.nodes[source].get("name", source),
                "predicate": edge.get("relation", ""),
                "object": self.graph.graph.nodes[target].get("name", target),
                "evidence": edge.get("evidence", ""),
                "document": edge.get("document", ""),
                "page": edge.get("page"),
                "chunk": edge.get("chunk_id", ""),
            }
            relationships.append(rel)
            provenance.append({
                "document": rel["document"],
                "page": rel["page"],
                "chunk": rel["chunk"],
            })
        return {
            "type": "graph",
            "score": round(float(score), 4),
            "path": path,
            "relationships": relationships,
            "provenance": provenance,
            "subject": relationships[0]["subject"] if relationships else path[0],
            "predicate": relationships[0]["predicate"] if relationships else "",
            "object": relationships[-1]["object"] if relationships else path[-1],
            "evidence": " ".join(x["evidence"] for x in relationships if x["evidence"]),
            "document": provenance[0]["document"] if provenance else "",
            "page": provenance[0]["page"] if provenance else None,
            "chunk": provenance[0]["chunk"] if provenance else "",
            "hops": len(relationships),
        }

    def search(self, query, top_k=6):
        seeds = self.find_entities(query)
        if not seeds:
            return []

        qtokens = self._tokens(query)
        candidates = []

        for seed in seeds:
            queue = deque([(seed["node_id"], [seed["node_id"]], [], 0)])
            visited = {(seed["node_id"], 0)}

            while queue:
                node_id, nodes, edges, depth = queue.popleft()
                if edges:
                    endpoint = self.graph.graph.nodes[node_id].get("name", node_id)
                    score = seed["score"] + 1.5 * len(qtokens & self._tokens(endpoint)) - 0.5 * (depth - 1)
                    candidates.append(self._result(nodes, edges, score))

                if depth >= self.max_hops:
                    continue

                for source, target, edge in self._neighbors(node_id):
                    nxt = target if source == node_id else source
                    state = (nxt, depth + 1)
                    if state in visited:
                        continue
                    visited.add(state)
                    queue.append((nxt, nodes + [nxt], edges + [(source, target, edge)], depth + 1))

        unique = {}
        for item in candidates:
            key = (
                tuple(item["path"]),
                tuple(r["predicate"] for r in item["relationships"]),
                tuple((p["document"], p["page"], p["chunk"]) for p in item["provenance"]),
            )
            if key not in unique or item["score"] > unique[key]["score"]:
                unique[key] = item

        return sorted(unique.values(), key=lambda x: x["score"], reverse=True)[:top_k]
