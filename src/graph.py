from __future__ import annotations

import json
from collections import defaultdict

from src.models import Edge, Node


class Graph:
    """Weighted directed graph stored as an adjacency list."""

    def __init__(self) -> None:
        self.nodes: dict[int, Node] = {}
        self.edges: list[Edge] = []
        self.adj: dict[int, list[Edge]] = defaultdict(list)

    def add_node(self, node: Node) -> None:
        """Register a location in the graph."""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add a directed, weighted connection.

        Computes ``edge.final_weight`` using the destination node's reward::

            final_weight = time_cost - edge_reward - dest_node.reward
        """
        dest_node = self.nodes[edge.to_id]
        edge.final_weight = edge.time_cost - edge.edge_reward - dest_node.reward
        self.edges.append(edge)
        self.adj[edge.from_id].append(edge)

    def load_from_json(self, filepath: str) -> None:
        """Load graph from a JSON file.

        Expected schema::

            {
              "nodes": [{"node_id": 0, "name": "Home", "node_type": "home", "reward": 0}],
              "edges": [{"from_id": 0, "to_id": 1, "time_cost": 6.0, "edge_reward": 1.0}]
            }
        """
        with open(filepath) as f:
            data = json.load(f)

        for n in data["nodes"]:
            self.add_node(Node(**n))

        for e in data["edges"]:
            self.add_edge(Edge(**e))

    def get_node_count(self) -> int:
        return len(self.nodes)

    def get_edge_count(self) -> int:
        return len(self.edges)
