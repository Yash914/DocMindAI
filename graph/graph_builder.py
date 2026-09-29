import re
import networkx as nx


class KnowledgeGraph:
    """Construction knowledge graph with provenance-aware relationships."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    @staticmethod
    def _make_node_id(name):
        normalized = re.sub(r"\s+", " ", str(name).strip().lower())
        normalized = re.sub(r"[^a-z0-9:_./-]+", "_", normalized)
        return normalized.strip("_") or "entity"

    def add_node(self, name, entity_type="Entity", properties=None):
        if not name:
            return ""
        properties = dict(properties or {})
        node_id = self._make_node_id(name)
        existing = dict(self.graph.nodes.get(node_id, {}))
        merged = dict(existing)
        merged.update({"name": name, "entity_type": entity_type or existing.get("entity_type", "Entity")})
        merged.update(properties)
        self.graph.add_node(node_id, **merged)
        return node_id

    def add_entities(self, entities):
        for entity in entities or []:
            name = entity.get("name")
            if name:
                self.add_node(name, entity.get("type", "Entity"), {"aliases": entity.get("aliases", [])})

    def add_edge(self, source, relation, target, document="", page=0, chunk_id="", evidence=""):
        if not source or not target or not relation:
            return
        source_id = self.add_node(source)
        target_id = self.add_node(target)
        self.graph.add_edge(
            source_id, target_id,
            relation=str(relation).upper(),
            document=document or "",
            page=page or 0,
            chunk_id=chunk_id or "",
            evidence=evidence or "",
        )

    def add_facts(self, facts, document="", page=0, chunk_id=""):
        for fact in facts or []:
            self.add_edge(
                fact.get("subject", ""),
                fact.get("predicate", ""),
                fact.get("object", ""),
                fact.get("document", document),
                fact.get("page", page),
                fact.get("chunk_id", fact.get("chunk", chunk_id)),
                fact.get("evidence", ""),
            )

    def build(self, entities, facts, document="", page=0, chunk_id=""):
        self.add_entities(entities)
        self.add_facts(facts, document, page, chunk_id)
        return self

    def number_of_nodes(self):
        return self.graph.number_of_nodes()

    def number_of_edges(self):
        return self.graph.number_of_edges()

    def get_provenance(self, source, target, relation=None):
        source_id = self._make_node_id(source)
        target_id = self._make_node_id(target)
        if not self.graph.has_edge(source_id, target_id):
            return []
        out = []
        for _, data in self.graph[source_id][target_id].items():
            if relation and data.get("relation", "").upper() != relation.upper():
                continue
            out.append(dict(data))
        return out

    def print_graph(self):
        print(f"\nKnowledge Graph: {self.number_of_nodes()} nodes, {self.number_of_edges()} edges")
        for source, target, data in self.graph.edges(data=True):
            s = self.graph.nodes[source].get("name", source)
            t = self.graph.nodes[target].get("name", target)
            print(f"{s} --{data.get('relation')}--> {t}")
            print(f"  Source: {data.get('document')} | Page {data.get('page')} | Chunk {data.get('chunk_id')}")
            print(f"  Evidence: {data.get('evidence')}")
