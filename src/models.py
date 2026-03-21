from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Node:
    node_id: int
    name: str
    node_type: str  # e.g. "home", "park", "intersection", "rest_stop", "trigger_zone", "trail"
    reward: float = 0.0
    x: float | None = None  # auto-generated via spring layout when not provided
    y: float | None = None  # auto-generated via spring layout when not provided


@dataclass
class Edge:
    from_id: int
    to_id: int
    time_cost: float
    edge_reward: float
    final_weight: float | None = None  # computed by Graph.add_edge: time_cost - edge_reward - dest.reward
