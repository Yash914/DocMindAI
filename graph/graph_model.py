from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class GraphNode:
    """
    Represents an entity in the knowledge graph.
    """

    node_id: str
    name: str
    entity_type: str
    properties: Dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """
    Represents a relationship between two entities.
    """

    source: str
    relation: str
    target: str

    # Provenance
    document: str = ""
    page: int = 0
    chunk_id: str = ""
    evidence: str = ""

    properties: Dict = field(default_factory=dict)
    