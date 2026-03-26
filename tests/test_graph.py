"""
tests/test_graph.py
-------------------
Unit tests for src.graph.Graph:
  - Node registration
  - Edge insertion and final_weight computation
  - Counts
  - JSON loading
"""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from src.graph import Graph
from src.models import Edge, Node


# ===========================================================================
# Helpers
# ===========================================================================

def _minimal_graph() -> Graph:
    """Two-node, one-edge graph used for targeted weight checks."""
    g = Graph()
    g.add_node(Node(0, "A", "home",         reward=0))
    g.add_node(Node(1, "B", "park",         reward=8))
    return g


# ===========================================================================
# Node registration
# ===========================================================================

class TestAddNode:

    def test_node_stored_by_id(self):
        g = Graph()
        node = Node(0, "Home", "home", reward=0)
        g.add_node(node)
        assert 0 in g.nodes
        assert g.nodes[0] is node

    def test_multiple_nodes_all_stored(self):
        g = Graph()
        for i in range(5):
            g.add_node(Node(i, f"Node{i}", "intersection", reward=0))
        assert set(g.nodes.keys()) == {0, 1, 2, 3, 4}

    def test_node_fields_preserved(self):
        g = Graph()
        g.add_node(Node(7, "Elm Park", "park", reward=8, x=1.5, y=3.0))
        n = g.nodes[7]
        assert n.name == "Elm Park"
        assert n.node_type == "park"
        assert n.reward == 8
        assert n.x == 1.5
        assert n.y == 3.0

    def test_overwrite_node_by_same_id(self):
        """Re-adding a node with the same id replaces the old one."""
        g = Graph()
        g.add_node(Node(0, "Old", "home", reward=0))
        g.add_node(Node(0, "New", "park", reward=5))
        assert g.nodes[0].name == "New"


# ===========================================================================
# Edge insertion and final_weight computation
# ===========================================================================

class TestAddEdge:
    """
    Weight formula: final_weight = time_cost - edge_reward - dest_node.reward
    """

    def test_neutral_edge_weight(self):
        """time=3, edge_reward=0, dest.reward=0  →  final=3."""
        g = Graph()
        g.add_node(Node(0, "A", "home",         reward=0))
        g.add_node(Node(1, "B", "intersection", reward=0))
        g.add_edge(Edge(0, 1, time_cost=3, edge_reward=0))
        assert g.edges[0].final_weight == pytest.approx(3.0)

    def test_park_destination_lowers_weight(self):
        """time=6, edge_reward=1, dest.reward=8  →  final=6-1-8=-3."""
        g = _minimal_graph()
        g.add_edge(Edge(0, 1, time_cost=6, edge_reward=1))
        assert g.edges[0].final_weight == pytest.approx(-3.0)

    def test_trigger_zone_raises_weight(self):
        """Trigger zone has reward=-10, so entering it is costly."""
        g = Graph()
        g.add_node(Node(0, "A", "home",         reward=0))
        g.add_node(Node(1, "B", "trigger_zone", reward=-10))
        g.add_edge(Edge(0, 1, time_cost=2, edge_reward=0))
        # final = 2 - 0 - (-10) = 12
        assert g.edges[0].final_weight == pytest.approx(12.0)

    def test_edge_reward_reduces_final_weight(self):
        """A high edge_reward (scenic path) should lower the final weight."""
        g = Graph()
        g.add_node(Node(0, "A", "home",  reward=0))
        g.add_node(Node(1, "B", "trail", reward=0))
        g.add_edge(Edge(0, 1, time_cost=5, edge_reward=4))
        # final = 5 - 4 - 0 = 1
        assert g.edges[0].final_weight == pytest.approx(1.0)

    def test_final_weight_set_on_edge_object(self):
        """final_weight must be written back to the Edge dataclass."""
        g = _minimal_graph()
        edge = Edge(0, 1, time_cost=6, edge_reward=1)
        assert edge.final_weight is None        # not set before insertion
        g.add_edge(edge)
        assert edge.final_weight is not None    # set after insertion

    def test_edge_added_to_adj_list(self):
        g = _minimal_graph()
        g.add_edge(Edge(0, 1, time_cost=6, edge_reward=1))
        assert len(g.adj[0]) == 1
        assert g.adj[0][0].to_id == 1

    def test_multiple_edges_from_same_node(self):
        g = Graph()
        g.add_node(Node(0, "A", "home",  reward=0))
        g.add_node(Node(1, "B", "park",  reward=8))
        g.add_node(Node(2, "C", "trail", reward=4))
        g.add_edge(Edge(0, 1, time_cost=6, edge_reward=1))
        g.add_edge(Edge(0, 2, time_cost=3, edge_reward=0))
        assert len(g.adj[0]) == 2

    def test_all_edges_stored_in_edges_list(self, sample_graph):
        assert len(sample_graph.edges) == 6

    def test_sample_graph_weights(self, sample_graph):
        """Cross-check every final_weight in the hand-verified sample graph."""
        weight_map = {
            (e.from_id, e.to_id): e.final_weight for e in sample_graph.edges
        }
        assert weight_map[(0, 1)] == pytest.approx(3.0)
        assert weight_map[(0, 2)] == pytest.approx(-3.0)
        assert weight_map[(1, 3)] == pytest.approx(12.0)
        assert weight_map[(1, 4)] == pytest.approx(3.0)
        assert weight_map[(2, 4)] == pytest.approx(1.0)
        assert weight_map[(3, 4)] == pytest.approx(-1.0)


# ===========================================================================
# Counts
# ===========================================================================

class TestCounts:

    def test_node_count_empty(self):
        assert Graph().get_node_count() == 0

    def test_edge_count_empty(self):
        assert Graph().get_edge_count() == 0

    def test_node_count_sample(self, sample_graph):
        assert sample_graph.get_node_count() == 5

    def test_edge_count_sample(self, sample_graph):
        assert sample_graph.get_edge_count() == 6


# ===========================================================================
# JSON loading
# ===========================================================================

class TestLoadFromJson:

    # ---- helpers ----

    @staticmethod
    def _write_json(data: dict) -> str:
        """Write data to a temp file and return the path."""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        json.dump(data, tmp)
        tmp.close()
        return tmp.name

    @staticmethod
    def _minimal_json() -> dict:
        return {
            "nodes": [
                {"node_id": 0, "name": "Home", "node_type": "home",
                 "reward": 0, "x": 0.0, "y": 0.0},
                {"node_id": 1, "name": "Park", "node_type": "park",
                 "reward": 8, "x": 1.0, "y": 1.0},
            ],
            "edges": [
                {"from_id": 0, "to_id": 1, "time_cost": 5.0,
                 "edge_reward": 1.0},
            ],
        }

    # ---- tests ----

    def test_nodes_loaded(self):
        path = self._write_json(self._minimal_json())
        g = Graph()
        g.load_from_json(path)
        assert g.get_node_count() == 2

    def test_edges_loaded(self):
        path = self._write_json(self._minimal_json())
        g = Graph()
        g.load_from_json(path)
        assert g.get_edge_count() == 1

    def test_final_weight_computed_on_load(self):
        """load_from_json must call add_edge which computes final_weight."""
        path = self._write_json(self._minimal_json())
        g = Graph()
        g.load_from_json(path)
        # final = 5 - 1 - 8 = -4
        assert g.edges[0].final_weight == pytest.approx(-4.0)

    def test_node_types_preserved(self):
        path = self._write_json(self._minimal_json())
        g = Graph()
        g.load_from_json(path)
        assert g.nodes[0].node_type == "home"
        assert g.nodes[1].node_type == "park"

    def test_node_rewards_preserved(self):
        path = self._write_json(self._minimal_json())
        g = Graph()
        g.load_from_json(path)
        assert g.nodes[1].reward == 8

    def test_spatial_coords_optional(self):
        """Nodes without x/y should load without error (x=y=None)."""
        data = {
            "nodes": [
                {"node_id": 0, "name": "A", "node_type": "home", "reward": 0},
                {"node_id": 1, "name": "B", "node_type": "park", "reward": 5},
            ],
            "edges": [
                {"from_id": 0, "to_id": 1, "time_cost": 3.0,
                 "edge_reward": 0.0},
            ],
        }
        path = self._write_json(data)
        g = Graph()
        g.load_from_json(path)
        assert g.nodes[0].x is None
        assert g.nodes[0].y is None

    def test_all_node_types_round_trip(self):
        """Every supported node_type survives a JSON round-trip."""
        types = ["home", "park", "intersection", "rest_stop",
                 "trigger_zone", "trail"]
        nodes = [
            {"node_id": i, "name": t, "node_type": t, "reward": 0}
            for i, t in enumerate(types)
        ]
        edges = [
            {"from_id": i, "to_id": i + 1, "time_cost": 1.0,
             "edge_reward": 0.0}
            for i in range(len(types) - 1)
        ]
        path = self._write_json({"nodes": nodes, "edges": edges})
        g = Graph()
        g.load_from_json(path)
        loaded_types = {n.node_type for n in g.nodes.values()}
        assert loaded_types == set(types)
