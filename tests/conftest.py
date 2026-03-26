"""Shared fixtures for all test modules."""
from __future__ import annotations

import pytest

from src.graph import Graph
from src.models import Edge, Node


# ---------------------------------------------------------------------------
# Hand-verified 5-node graph from design_specification.md §4
# ---------------------------------------------------------------------------
#
#   Node  Name          Type          Reward  x     y
#   ----  ------------  ------------  ------  ----  ----
#   0     Home          home               0   0.0   0.0
#   1     Main St       intersection       0   3.0   0.0
#   2     Elm Park      park               8   1.5   3.0
#   3     Construction  trigger_zone     -10   5.0   2.0
#   4     Dog Café      rest_stop          2   6.0   0.0
#
#   Edge       time  edge_reward  final_weight
#   ---------  ----  -----------  ------------
#   0 → 1       3        0           3   (3 - 0 - 0)
#   0 → 2       6        1          -3   (6 - 1 - 8)   ← park bonus
#   1 → 3       2        0          12   (2 - 0 - (-10)) ← trigger penalty
#   1 → 4       5        0           3   (5 - 0 - 2)
#   2 → 4       4        1           1   (4 - 1 - 2)
#   3 → 4       1        0          -1   (1 - 0 - 2)
#
#   Best path 0→4:
#     0→2→4         : -3 + 1 = -2  ← optimal
#     0→1→4         :  3 + 3 =  6
#     0→1→3→4       :  3 + 12 + (-1) = 14


@pytest.fixture
def sample_graph() -> Graph:
    """5-node graph with hand-verified expected results."""
    g = Graph()
    g.add_node(Node(0, "Home",         "home",         reward=0,   x=0.0, y=0.0))
    g.add_node(Node(1, "Main St",      "intersection", reward=0,   x=3.0, y=0.0))
    g.add_node(Node(2, "Elm Park",     "park",         reward=8,   x=1.5, y=3.0))
    g.add_node(Node(3, "Construction", "trigger_zone", reward=-10, x=5.0, y=2.0))
    g.add_node(Node(4, "Dog Café",     "rest_stop",    reward=2,   x=6.0, y=0.0))

    g.add_edge(Edge(0, 1, time_cost=3, edge_reward=0))
    g.add_edge(Edge(0, 2, time_cost=6, edge_reward=1))
    g.add_edge(Edge(1, 3, time_cost=2, edge_reward=0))
    g.add_edge(Edge(1, 4, time_cost=5, edge_reward=0))
    g.add_edge(Edge(2, 4, time_cost=4, edge_reward=1))
    g.add_edge(Edge(3, 4, time_cost=1, edge_reward=0))
    return g


@pytest.fixture
def negative_cycle_graph() -> Graph:
    """
    3-node graph containing a negative-weight cycle between nodes 1 and 2.

    Nodes:
      0  Home   (reward  0)
      1  ParkA  (reward  5)
      2  Trail  (reward  4)

    Edges:
      0 → 1  time=3, edge_reward=0  →  final = 3 - 0 - 5  = -2
      1 → 2  time=1, edge_reward=0  →  final = 1 - 0 - 4  = -3
      2 → 1  time=1, edge_reward=0  →  final = 1 - 0 - 5  = -4

    Cycle 1→2→1 has total weight -3 + (-4) = -7 < 0.
    """
    g = Graph()
    g.add_node(Node(0, "Home",  "home",  reward=0))
    g.add_node(Node(1, "ParkA", "park",  reward=5))
    g.add_node(Node(2, "Trail", "trail", reward=4))

    g.add_edge(Edge(0, 1, time_cost=3, edge_reward=0))
    g.add_edge(Edge(1, 2, time_cost=1, edge_reward=0))
    g.add_edge(Edge(2, 1, time_cost=1, edge_reward=0))
    return g


@pytest.fixture
def disconnected_graph() -> Graph:
    """
    Graph where node 2 is unreachable from node 0.

    Nodes:  0 (Home), 1 (Park), 2 (isolated — no incoming edges from 0/1)
    Edges:  0 → 1 only
    """
    g = Graph()
    g.add_node(Node(0, "Home",     "home",         reward=0))
    g.add_node(Node(1, "Park",     "park",         reward=5))
    g.add_node(Node(2, "Isolated", "intersection", reward=0))

    g.add_edge(Edge(0, 1, time_cost=3, edge_reward=0))
    return g
