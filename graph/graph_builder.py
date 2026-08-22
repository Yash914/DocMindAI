import networkx as nx

from graph.graph_model import GraphNode, GraphEdge


class KnowledgeGraph:

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    # --------------------------------------------------
    # CREATE NODE ID
    # --------------------------------------------------

    @staticmethod
    def _make_node_id(name):
        return (
            name.lower()
            .strip()
            .replace(" ", "_")
        )

    # --------------------------------------------------
    # ADD NODE
    # --------------------------------------------------

    def add_node(
        self,
        name,
        entity_type="Entity",
        properties=None
    ):

        if properties is None:
            properties = {}

        node_id = self._make_node_id(name)

        self.graph.add_node(
            node_id,
            name=name,
            entity_type=entity_type,
            **properties
        )

        return node_id

    # --------------------------------------------------
    # ADD ENTITIES
    # --------------------------------------------------

    def add_entities(self, entities):

        for entity in entities:

            name = entity.get("name")

            entity_type = entity.get(
                "type",
                "Entity"
            )

            if not name:
                continue

            self.add_node(
                name=name,
                entity_type=entity_type
            )

    # --------------------------------------------------
    # ADD EDGE
    # --------------------------------------------------

    def add_edge(
        self,
        source,
        relation,
        target,
        document="",
        page=0,
        chunk_id="",
        evidence=""
    ):

        source_id = self._make_node_id(source)
        target_id = self._make_node_id(target)

        # Make sure nodes exist
        if source_id not in self.graph:

            self.add_node(
                source,
                "Entity"
            )

        if target_id not in self.graph:

            self.add_node(
                target,
                "Entity"
            )

        self.graph.add_edge(
            source_id,
            target_id,
            relation=relation,
            document=document,
            page=page,
            chunk_id=chunk_id,
            evidence=evidence
        )

    # --------------------------------------------------
    # ADD VALIDATED FACTS
    # --------------------------------------------------

    def add_facts(
        self,
        facts,
        document="",
        page=0,
        chunk_id=""
    ):

        for fact in facts:

            subject = fact.get(
                "subject"
            )

            predicate = fact.get(
                "predicate"
            )

            object_value = fact.get(
                "object"
            )

            evidence = fact.get(
                "evidence",
                ""
            )

            if not subject or not predicate or not object_value:
                continue

            self.add_edge(
                source=subject,
                relation=predicate,
                target=object_value,
                document=document,
                page=page,
                chunk_id=chunk_id,
                evidence=evidence
            )

    # --------------------------------------------------
    # BUILD COMPLETE GRAPH
    # --------------------------------------------------

    def build(
        self,
        entities,
        facts,
        document="",
        page=0,
        chunk_id=""
    ):

        self.add_entities(
            entities
        )

        self.add_facts(
            facts=facts,
            document=document,
            page=page,
            chunk_id=chunk_id
        )

    # --------------------------------------------------
    # GRAPH STATISTICS
    # --------------------------------------------------

    def number_of_nodes(self):
        return self.graph.number_of_nodes()

    def number_of_edges(self):
        return self.graph.number_of_edges()

    # --------------------------------------------------
    # PRINT GRAPH
    # --------------------------------------------------

    def print_graph(self):

        print("\n" + "=" * 70)
        print("KNOWLEDGE GRAPH")
        print("=" * 70)

        print(
            f"Nodes: {self.number_of_nodes()}"
        )

        print(
            f"Edges: {self.number_of_edges()}"
        )

        # --------------------------------------------------
        # NODES
        # --------------------------------------------------

        print("\nNodes:")

        for node_id, data in self.graph.nodes(
            data=True
        ):

            print(
                f"  - {data.get('name')} "
                f"[{data.get('entity_type')}]"
            )

        # --------------------------------------------------
        # EDGES
        # --------------------------------------------------

        print("\nRelationships:")

        for source, target, data in self.graph.edges(
            data=True
        ):

            source_name = self.graph.nodes[
                source
            ].get("name", source)

            target_name = self.graph.nodes[
                target
            ].get("name", target)

            print(
                f"  - {source_name} "
                f"--{data.get('relation')}--> "
                f"{target_name}"
            )

            print(
                f"    Document: "
                f"{data.get('document')}"
            )

            print(
                f"    Page: "
                f"{data.get('page')}"
            )

            print(
                f"    Chunk: "
                f"{data.get('chunk_id')}"
            )

            print(
                f"    Evidence: "
                f"{data.get('evidence')}"
            )