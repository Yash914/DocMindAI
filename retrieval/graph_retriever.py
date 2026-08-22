from pathlib import Path
import sys
import re


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# QUERY → PREDICATE HINTS
# ============================================================

PREDICATE_HINTS = {
    "conform": ["CONFORMS_TO"],
    "standard": ["CONFORMS_TO"],
    "comply": ["CONFORMS_TO"],

    "require": ["REQUIRES"],
    "requires": ["REQUIRES"],
    "requirement": ["REQUIRES"],

    "test": [
        "TESTED_AT",
        "TESTED_FOR",
        "MUST_TEST",
        "REQUIRED_TO_TEST"
    ],

    "tested": [
        "TESTED_AT",
        "TESTED_FOR"
    ],

    "testing": [
        "TESTED_AT",
        "TESTED_FOR"
    ],

    "approve": ["APPROVED_BY"],
    "approval": ["APPROVED_BY"],
    "approved": ["APPROVED_BY"],

    "store": [
        "STORED_AT",
        "STORED_SEPARATELY"
    ],

    "stored": [
        "STORED_AT",
        "STORED_SEPARATELY"
    ]
}


# ============================================================
# GRAPH RETRIEVER
# ============================================================

class GraphRetriever:

    def __init__(self, graph):

        self.graph = graph

    # ========================================================
    # FIND ENTITY
    # ========================================================

    def find_entity(self, query):

        query = query.lower().strip()

        matches = []

        for node_id, node_data in self.graph.graph.nodes(
            data=True
        ):

            name = node_data.get(
                "name",
                node_id
            )

            if query in name.lower():

                matches.append(
                    {
                        "node_id": node_id,
                        "name": name,
                        "type": node_data.get(
                            "type",
                            "Entity"
                        )
                    }
                )

        return matches

    # ========================================================
    # GET ENTITY RELATIONSHIPS
    # ========================================================

    def search_entity(self, entity_name):

        entity_name = entity_name.lower().strip()

        results = []

        for node_id, node_data in self.graph.graph.nodes(
            data=True
        ):

            name = node_data.get(
                "name",
                node_id
            )

            if name.lower() != entity_name:
                continue

            # ------------------------------------------------
            # Outgoing relationships
            # ------------------------------------------------

            for _, target, edge_data in self.graph.graph.out_edges(
                node_id,
                data=True
            ):

                target_data = self.graph.graph.nodes[
                    target
                ]

                results.append(
                    {
                        "subject": name,

                        "predicate": edge_data.get(
                            "predicate",
                            edge_data.get(
                                "relation",
                                ""
                            )
                        ),

                        "object": target_data.get(
                            "name",
                            target
                        ),

                        "evidence": edge_data.get(
                            "evidence",
                            ""
                        ),

                        "document": edge_data.get(
                            "document",
                            ""
                        ),

                        "page": edge_data.get(
                            "page",
                            None
                        ),

                        "chunk": edge_data.get(
                            "chunk",
                            ""
                        )
                    }
                )

            # ------------------------------------------------
            # Incoming relationships
            # ------------------------------------------------

            for source, _, edge_data in self.graph.graph.in_edges(
                node_id,
                data=True
            ):

                source_data = self.graph.graph.nodes[
                    source
                ]

                results.append(
                    {
                        "subject": source_data.get(
                            "name",
                            source
                        ),

                        "predicate": edge_data.get(
                            "predicate",
                            edge_data.get(
                                "relation",
                                ""
                            )
                        ),

                        "object": name,

                        "evidence": edge_data.get(
                            "evidence",
                            ""
                        ),

                        "document": edge_data.get(
                            "document",
                            ""
                        ),

                        "page": edge_data.get(
                            "page",
                            None
                        ),

                        "chunk": edge_data.get(
                            "chunk",
                            ""
                        )
                    }
                )

        return results

    # ========================================================
    # EXTRACT QUERY HINTS
    # ========================================================

    def get_predicate_hints(self, query):

        words = re.findall(
            r"[a-zA-Z]+",
            query.lower()
        )

        predicates = set()

        for word in words:

            if word in PREDICATE_HINTS:

                predicates.update(
                    PREDICATE_HINTS[word]
                )

        return predicates

    # ========================================================
    # SCORE RELATIONSHIP
    # ========================================================

    def score_relationship(
        self,
        relationship,
        query
    ):

        query_lower = query.lower()

        predicate = relationship[
            "predicate"
        ].upper()

        subject = relationship[
            "subject"
        ].lower()

        object_value = relationship[
            "object"
        ].lower()

        evidence = relationship[
            "evidence"
        ].lower()

        score = 0.0

        # ----------------------------------------------------
        # Predicate hints
        # ----------------------------------------------------

        hints = self.get_predicate_hints(
            query
        )

        if predicate in hints:

            score += 5.0

        # ----------------------------------------------------
        # Entity matches
        # ----------------------------------------------------

        query_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                query_lower
            )
        )

        subject_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                subject
            )
        )

        object_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                object_value
            )
        )

        evidence_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                evidence
            )
        )

        score += len(
            query_words & subject_words
        ) * 2.0

        score += len(
            query_words & object_words
        ) * 1.5

        score += len(
            query_words & evidence_words
        ) * 0.25

        return score

    # ========================================================
    # QUERY-AWARE SEARCH
    # ========================================================

    def search(
        self,
        query,
        top_k=5
    ):

        query_words = re.findall(
            r"[a-zA-Z0-9]+",
            query.lower()
        )

        relationships = []

        seen_entities = set()

        # ----------------------------------------------------
        # Find entities from query
        # ----------------------------------------------------

        for word in query_words:

            if len(word) < 3:
                continue

            matches = self.find_entity(
                word
            )

            for match in matches:

                entity_name = match[
                    "name"
                ]

                key = entity_name.lower()

                if key in seen_entities:
                    continue

                seen_entities.add(key)

                relationships.extend(
                    self.search_entity(
                        entity_name
                    )
                )

        # ----------------------------------------------------
        # Score relationships
        # ----------------------------------------------------

        scored = []

        for relationship in relationships:

            score = self.score_relationship(
                relationship,
                query
            )

            item = relationship.copy()

            item["score"] = score

            scored.append(
                item
            )

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        scored.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return scored[:top_k]