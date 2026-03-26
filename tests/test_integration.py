"""
tests/test_integration.py
--------------------------
End-to-end tests: load real JSON datasets from data/ and verify that the
full pipeline (Graph → bellman_ford → reconstruct_path) behaves correctly.

These tests require the JSON files to exist on disk.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from src.bellman_ford import bellman_ford, reconstruct_path
from src.graph import Graph

# ---------------------------------------------------------------------------
# Paths — relative to project root (where pytest is invoked from)
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data"
SAMPLE_JSON        = DATA_DIR / "sample_data.json"
URBAN_JSON         = DATA_DIR / "sample_data" / "urban_downtown.json"
SUBURBAN_JSON      = DATA_DIR / "sample_data" / "suburban_park_district.json"
LARGE_CITY_JSON    = DATA_DIR / "sample_data" / "large_city_loop.json"


def _skip_if_missing(path: Path):
    return pytest.mark.skipif(
        not path.exists(),
        reason=f"Data file not found: {path}",
    )


# ===========================================================================
# sample_data.json  (5 nodes, 6 edges — matches the design-spec example)
# ===========================================================================

@_skip_if_missing(SAMPLE_JSON)
class TestSampleData:

    @pytest.fixture
    def g(self) -> Graph:
        graph = Graph()
        graph.load_from_json(str(SAMPLE_JSON))
        return graph

    def test_node_count(self, g):
        assert g.get_node_count() == 5

    def test_edge_count(self, g):
        assert g.get_edge_count() == 6

    def test_node_types_present(self, g):
        types = {n.node_type for n in g.nodes.values()}
        assert "home"         in types
        assert "park"         in types
        assert "intersection" in types
        assert "trigger_zone" in types
        assert "rest_stop"    in types

    def test_optimal_cost_home_to_cafe(self, g):
        """dist[4] must equal -2 (design-spec §4 expected result)."""
        result = bellman_ford(g, source=0)
        assert result.dist[4] == pytest.approx(-2.0)

    def test_optimal_path_home_to_cafe(self, g):
        """Optimal path must be [0, 2, 4] (park route dominates)."""
        result = bellman_ford(g, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert path == [0, 2, 4]

    def test_no_negative_cycle(self, g):
        result = bellman_ford(g, source=0)
        assert result.has_negative_cycle is False

    def test_all_nodes_reachable_from_home(self, g):
        """Every node in the sample graph is reachable from node 0."""
        result = bellman_ford(g, source=0)
        for nid in g.nodes:
            assert not math.isinf(result.dist[nid]), (
                f"Node {nid} ({g.nodes[nid].name}) unexpectedly unreachable"
            )

    def test_trigger_zone_has_highest_cost(self, g):
        """
        The trigger zone (Construction, node 3) should have the worst
        distance from Home — the penalty reward=-10 makes all edges into
        it expensive.
        """
        result = bellman_ford(g, source=0)
        reachable = {
            nid: d for nid, d in result.dist.items()
            if not math.isinf(d) and nid != 0
        }
        worst_node = max(reachable, key=reachable.__getitem__)
        assert g.nodes[worst_node].node_type == "trigger_zone"

    def test_park_path_cheaper_than_direct_route(self, g):
        """
        0→2→4 (via park, cost -2) must beat 0→1→4 (direct, cost 6).
        """
        result = bellman_ford(g, source=0)
        path = reconstruct_path(result, source=0, dest=4)
        assert 2 in path        # park node on optimal path
        assert result.dist[4] < 0   # net reward exceeds time cost


# ===========================================================================
# urban_downtown.json  (20 nodes, 31 edges)
# ===========================================================================

@_skip_if_missing(URBAN_JSON)
class TestUrbanDowntown:

    @pytest.fixture
    def g(self) -> Graph:
        graph = Graph()
        graph.load_from_json(str(URBAN_JSON))
        return graph

    def test_load_node_count(self, g):
        assert g.get_node_count() == 20

    def test_load_edge_count(self, g):
        assert g.get_edge_count() == 31

    def test_no_negative_cycle(self, g):
        result = bellman_ford(g, source=0)
        assert result.has_negative_cycle is False

    def test_source_distance_zero(self, g):
        result = bellman_ford(g, source=0)
        assert result.dist[0] == pytest.approx(0.0)

    def test_path_is_valid_sequence(self, g):
        """Every step in the reconstructed path must be a real edge."""
        result = bellman_ford(g, source=0)
        # Find a reachable destination
        dest = max(
            (nid for nid in g.nodes if nid != 0
             and not math.isinf(result.dist[nid])),
            key=lambda nid: -result.dist[nid],  # pick a distant node
        )
        path = reconstruct_path(result, source=0, dest=dest)
        edge_set = {(e.from_id, e.to_id) for e in g.edges}
        for i in range(len(path) - 1):
            assert (path[i], path[i + 1]) in edge_set

    def test_trigger_zones_penalised(self, g):
        """
        Distances into trigger_zone nodes should be higher than neutral
        nodes at similar graph depth — the reward=-10 inflates entry weight.
        """
        result = bellman_ford(g, source=0)
        trigger_ids = [
            nid for nid, n in g.nodes.items()
            if n.node_type == "trigger_zone"
        ]
        park_ids = [
            nid for nid, n in g.nodes.items()
            if n.node_type == "park"
        ]
        reachable_triggers = [
            result.dist[nid] for nid in trigger_ids
            if not math.isinf(result.dist[nid])
        ]
        reachable_parks = [
            result.dist[nid] for nid in park_ids
            if not math.isinf(result.dist[nid])
        ]
        if reachable_triggers and reachable_parks:
            # On average, reaching a trigger zone should cost more than a park
            assert sum(reachable_triggers) / len(reachable_triggers) > \
                   sum(reachable_parks) / len(reachable_parks)

    def test_final_weights_all_computed(self, g):
        """No edge should have final_weight=None after loading."""
        for edge in g.edges:
            assert edge.final_weight is not None


# ===========================================================================
# suburban_park_district.json  (20 nodes, 30 edges)
# ===========================================================================

@_skip_if_missing(SUBURBAN_JSON)
class TestSuburbanParkDistrict:

    @pytest.fixture
    def g(self) -> Graph:
        graph = Graph()
        graph.load_from_json(str(SUBURBAN_JSON))
        return graph

    def test_load_node_count(self, g):
        assert g.get_node_count() == 20

    def test_load_edge_count(self, g):
        assert g.get_edge_count() == 30

    def test_no_negative_cycle(self, g):
        result = bellman_ford(g, source=0)
        assert result.has_negative_cycle is False

    def test_off_leash_park_has_lowest_dist(self, g):
        """
        The Off-Leash Dog Park (reward=10, the maximum) should produce one
        of the most attractive (lowest) distances from Home.
        """
        result = bellman_ford(g, source=0)
        park_ids = [
            nid for nid, n in g.nodes.items()
            if n.node_type == "park" and not math.isinf(result.dist[nid])
        ]
        if park_ids:
            best_park_dist = min(result.dist[nid] for nid in park_ids)
            # Best park distance must be better (lower) than a neutral node
            neutral_ids = [
                nid for nid, n in g.nodes.items()
                if n.node_type == "intersection"
                and not math.isinf(result.dist[nid]) and nid != 0
            ]
            if neutral_ids:
                avg_neutral = sum(result.dist[nid] for nid in neutral_ids) / len(neutral_ids)
                assert best_park_dist < avg_neutral

    def test_construction_zone_not_on_optimal_to_sniff_garden(self, g):
        """
        The Sniff Garden (reward=9) should be reachable without passing
        through the Construction Zone (reward=-10).
        """
        result = bellman_ford(g, source=0)
        sniff_id = next(
            nid for nid, n in g.nodes.items() if n.name == "Sniff Garden"
        )
        construction_id = next(
            nid for nid, n in g.nodes.items()
            if n.node_type == "trigger_zone"
        )
        if not math.isinf(result.dist[sniff_id]):
            path = reconstruct_path(result, source=0, dest=sniff_id)
            assert construction_id not in path


# ===========================================================================
# large_city_loop.json  (30 nodes, 55 edges)
# ===========================================================================

@_skip_if_missing(LARGE_CITY_JSON)
class TestLargeCityLoop:

    @pytest.fixture
    def g(self) -> Graph:
        graph = Graph()
        graph.load_from_json(str(LARGE_CITY_JSON))
        return graph

    def test_load_node_count(self, g):
        assert g.get_node_count() == 30

    def test_load_edge_count(self, g):
        assert g.get_edge_count() == 55

    def test_no_negative_cycle(self, g):
        result = bellman_ford(g, source=0)
        assert result.has_negative_cycle is False

    def test_off_leash_park_reachable(self, g):
        """Off-Leash Park (node 23, reward=10) must be reachable from Home."""
        result = bellman_ford(g, source=0)
        assert not math.isinf(result.dist[23])

    def test_off_leash_park_has_negative_distance(self, g):
        """
        The Off-Leash Park has reward=10 — its high reward should make
        the path cost negative (net reward exceeds walking time).
        """
        result = bellman_ford(g, source=0)
        assert result.dist[23] < 0

    def test_all_paths_valid(self, g):
        """Every non-trivial reconstructed path must consist of real edges."""
        result = bellman_ford(g, source=0)
        edge_set = {(e.from_id, e.to_id) for e in g.edges}
        for dest in g.nodes:
            if dest == 0 or math.isinf(result.dist[dest]):
                continue
            path = reconstruct_path(result, source=0, dest=dest)
            for i in range(len(path) - 1):
                assert (path[i], path[i + 1]) in edge_set, (
                    f"Invalid edge ({path[i]}, {path[i+1]}) in path to node {dest}"
                )

    def test_bellman_ford_complexity_tractable(self, g):
        """
        Bellman-Ford on 30 nodes × 55 edges = 1,650 operations — must
        complete in well under 1 second.
        """
        import time
        start = time.perf_counter()
        bellman_ford(g, source=0)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"bellman_ford took {elapsed:.3f}s on 30-node graph"
