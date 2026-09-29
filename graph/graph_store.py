import json
from pathlib import Path


class GraphStore:
    """Lightweight persistent storage for a NetworkX knowledge graph."""

    def save(self, graph, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "nodes": [
                {"id": node_id, **node_data}
                for node_id, node_data in graph.graph.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, **edge_data}
                for source, target, edge_data in graph.graph.edges(data=True)
            ],
        }

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, graph, path):
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))

        graph.graph.clear()

        for node in data.get("nodes", []):
            node = dict(node)
            node_id = node.pop("id")
            graph.graph.add_node(node_id, **node)

        for edge in data.get("edges", []):
            edge = dict(edge)
            source = edge.pop("source")
            target = edge.pop("target")
            graph.graph.add_edge(source, target, **edge)

        return graph
