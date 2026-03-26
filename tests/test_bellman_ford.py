"""
tests/test_bellman_ford.py
--------------------------
Unit tests for src.bellman_ford:
  - bellman_ford()       distance correctness, negative-cycle flag
  - reconstruct_path()   path tracing, edge cases
"""
from __future__ import annotations

import math

import pytest

from src.bellman_ford import BellmanFordResult, bellman_ford, reconstruct_path
from src.graph import Graph
from src.models import Edge, Node


# ===========================================================================
# bellman_ford() — distance table
# ===========================================================================

class TestBellmanFordDistances:

    def test_source_distance_is_zero(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        assert result.dist[0] == pytest.approx(0.0)

    def test_all_nodes_have_distance_entry(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        assert set(result.dist.keys()) == set(sample_graph.nodes.keys())

    def test_optimal_cost_to_dest(self, sample_graph):
        """
        Best path 0→4 is 0→2→4 with total weight -3+1 = -2.
        (Verified manually in design_specification.md §4)
        """
        result = bellman_ford(sample_graph, source=0)
        assert result.dist[4] == pytest.approx(-2.0)

    def test_direct_neighbour_distance(self, sample_graph):
        """Node 1 is reached directly via edge (0,1) with weight 3."""
        result = bellman_ford(sample_graph, source=0)
        assert result.dist[1] == pytest.approx(3.0)

    def test_park_node_distance(self, sample_graph):
        """Node 2 (Elm Park) is reached via (0,2) with weight -3."""
        result = bellman_ford(sample_graph, source=0)
        assert result.dist[2] == pytest.approx(-3.0)

    def test_trigger_zone_distance(self, sample_graph):
        """
        Node 3 (Construction) best path: 0→1→3, weight = 3 + 12 = 15.
        No shorter path exists.
        """
        result = bellman_ford(sample_graph, source=0)
        assert result.dist[3] == pytest.approx(15.0)

    def test_source_stored_on_result(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        assert result.source == 0

    def test_single_node_graph(self):
        """A graph with only the source node — dist[source] = 0, no edges."""
        g = Graph()
        g.add_node(Node(0, "Solo", "home", reward=0))
        result = bellman_ford(g, source=0)
        assert result.dist[0] == pytest.approx(0.0)

    def test_all_positive_weights(self):
        """Graph with only positive edge weights still returns correct dists."""
        g = Graph()
        g.add_node(Node(0, "A", "home",         reward=0))
        g.add_node(Node(1, "B", "intersection", reward=0))
        g.add_node(Node(2, "C", "intersection", reward=0))
        g.add_edge(Edge(0, 1, time_cost=4, edge_reward=0))
        g.add_edge(Edge(0, 2, time_cost=10, edge_reward=0))
        g.add_edge(Edge(1, 2, time_cost=3, edge_reward=0))
        result = bellman_ford(g, source=0)
        # 0→1→2 = 4+3=7, better than direct 0→2=10
        assert result.dist[2] == pytest.approx(7.0)

    def test_unreachable_node_is_inf(self, disconnected_graph):
        """Node 2 has no incoming edges from the source component."""
        result = bellman_ford(disconnected_graph, source=0)
        assert math.isinf(result.dist[2])

    def test_reachable_node_not_inf(self, disconnected_graph):
        result = bellman_ford(disconnected_graph, source=0)
        assert not math.isinf(result.dist[1])


# ===========================================================================
# bellman_ford() — negative cycle detection
# ===========================================================================

class TestNegativeCycleDetection:

    def test_no_negative_cycle_in_sample(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        assert result.has_negative_cycle is False

    def test_negative_cycle_flagged(self, negative_cycle_graph):
        """
        Graph has cycle 1→2→1 with total weight -3 + (-4) = -7 < 0.
        Bellman-Ford must set has_negative_cycle = True.
        """
        result = bellman_ford(negative_cycle_graph, source=0)
        assert result.has_negative_cycle is True

    def test_no_negative_cycle_on_chain(self):
        """A simple chain 0→1→2 with negative weights but no cycle."""
        g = Graph()
        g.add_node(Node(0, "A", "home", reward=0))
        g.add_node(Node(1, "B", "park", reward=8))   # entering lowers weight
        g.add_node(Node(2, "C", "park", reward=6))
        g.add_edge(Edge(0, 1, time_cost=5, edge_reward=0))  # 5-0-8 = -3
        g.add_edge(Edge(1, 2, time_cost=4, edge_reward=0))  # 4-0-6 = -2
        result = bellman_ford(g, source=0)
        assert result.has_negative_cycle is False


# ===========================================================================
# reconstruct_path()
# ===========================================================================

class TestReconstructPath:

    def test_optimal_path_is_correct(self, sample_graph):
        """Expected optimal path: 0 → 2 → 4."""
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert path == [0, 2, 4]

    def test_path_starts_at_source(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert path[0] == 0

    def test_path_ends_at_dest(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert path[-1] == 4

    def test_path_to_direct_neighbour(self, sample_graph):
        """Node 1 is reached directly from 0."""
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=1)
        assert path == [0, 1]

    def test_path_to_source_is_single_node(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=0)
        assert path == [0]

    def test_unreachable_returns_empty(self, disconnected_graph):
        result = bellman_ford(disconnected_graph, source=0)
        path = reconstruct_path(result, source=0, dest=2)
        assert path == []

    def test_raises_on_negative_cycle(self, negative_cycle_graph):
        result = bellman_ford(negative_cycle_graph, source=0)
        with pytest.raises(ValueError, match="Negative cycle"):
            reconstruct_path(result, source=0, dest=1)

    def test_path_avoids_trigger_zone(self, sample_graph):
        """
        The optimal path 0→2→4 must not pass through node 3 (trigger zone).
        The trigger zone route 0→1→3→4 has total weight 14, far worse than -2.
        """
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert 3 not in path

    def test_path_uses_park_bonus(self, sample_graph):
        """The optimal path must pass through node 2 (Elm Park) for the reward."""
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert 2 in path

    def test_path_length_is_valid(self, sample_graph):
        """Every consecutive pair in the path must be a real edge."""
        result = bellman_ford(sample_graph, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        edge_set = {(e.from_id, e.to_id) for e in sample_graph.edges}
        for i in range(len(path) - 1):
            assert (path[i], path[i + 1]) in edge_set


# ===========================================================================
# predecessor table
# ===========================================================================

class TestPredecessors:

    def test_source_predecessor_is_none(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        assert result.predecessor[0] is None

    def test_all_nodes_have_predecessor_entry(self, sample_graph):
        result = bellman_ford(sample_graph, source=0)
        assert set(result.predecessor.keys()) == set(sample_graph.nodes.keys())

    def test_predecessor_of_optimal_dest(self, sample_graph):
        """
        On optimal path 0→2→4, node 4's predecessor must be 2.
        """
        result = bellman_ford(sample_graph, source=0)
        assert result.predecessor[4] == 2

    def test_predecessor_of_park(self, sample_graph):
        """Node 2 (Elm Park) is reached directly from 0."""
        result = bellman_ford(sample_graph, source=0)
        assert result.predecessor[2] == 0
