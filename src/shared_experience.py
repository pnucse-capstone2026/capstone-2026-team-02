"""Hallucination 주요 구현 발췌. SOURCE_GUIDE.md와 함께 읽는다."""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

class EdgeType(str, Enum):
    """Types of relationships (hyperedges) between nodes."""
    PARTICIPATED_IN = "participated_in"
    WITNESSED = "witnessed"
    CAUSED = "caused"

@dataclass
class HyperEdge:
    """A hyperedge connecting multiple nodes with roles.

    Unlike a simple edge that connects exactly two nodes, a hyperedge can
    connect any number of nodes, each playing a distinct role in the
    relationship. For example, a WITNESSED event might have a "subject"
    (the actor), an "object" (what happened), and multiple "witness" nodes.

    Attributes:
        id: Unique identifier for this edge.
        edge_type: The category of relationship this edge represents.
        members: Mapping of node_id -> role (e.g., "subject", "object", "witness").
        properties: Arbitrary key-value metadata attached to the edge.
        weight: Numeric strength/importance of this relationship (default 1.0).
        memory_ids: List of linked memory IDs for cross-referencing with the
                     memory subsystem.
    """
    id: str
    edge_type: EdgeType
    members: Dict[str, str]  # node_id -> role
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    memory_ids: List[str] = field(default_factory=list)

class HyperGraph:
    def add_edge(self, edge: HyperEdge) -> None:
        """Add a hyperedge.  All referenced node IDs must already exist."""
        for node_id in edge.members:
            if node_id not in self._nodes:
                raise KeyError(
                    f"Cannot add edge '{edge.id}': node '{node_id}' does not exist."
                )

        self._edges[edge.id] = edge
        for node_id in edge.members:
            self._node_to_edges.setdefault(node_id, set()).add(edge.id)

    def get_edges_for_node(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
    ) -> List[HyperEdge]:
        """Return all edges incident to *node_id*, optionally filtered by type."""
        edge_ids = self._node_to_edges.get(node_id, set())
        result: List[HyperEdge] = []
        for eid in edge_ids:
            edge = self._edges.get(eid)
            if edge is None:
                continue
            if edge_type is not None and edge.edge_type != edge_type:
                continue
            result.append(edge)
        return result

def get_shared_events(
    graph: HyperGraph,
    node_id_a: str,
    node_id_b: str,
) -> List[HyperEdge]:
    """Find all event-related edges that both nodes participate in.

    Looks for PARTICIPATED_IN, WITNESSED, and CAUSED edges where both
    *node_id_a* and *node_id_b* are members.

    Returns:
        A list of HyperEdge objects representing shared events, sorted
        by weight descending (most significant first).
    """
    event_types = {EdgeType.PARTICIPATED_IN, EdgeType.WITNESSED, EdgeType.CAUSED}
    shared: List[HyperEdge] = []

    # Iterate over the edges of whichever node has fewer edges (optimisation)
    edges_a = graph.get_edges_for_node(node_id_a)
    edges_b = graph.get_edges_for_node(node_id_b)

    if len(edges_a) <= len(edges_b):
        search_edges = edges_a
        target_id = node_id_b
    else:
        search_edges = edges_b
        target_id = node_id_a

    for edge in search_edges:
        if edge.edge_type not in event_types:
            continue
        if target_id in edge.members:
            shared.append(edge)

    # Sort by weight descending
    shared.sort(key=lambda e: e.weight, reverse=True)
    return shared
