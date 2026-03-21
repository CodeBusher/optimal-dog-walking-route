from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.graph import Graph


@dataclass
class BellmanFordResult:
    source: int
    dist: dict[int, float] = field(default_factory=dict)
    predecessor: dict[int, int | None] = field(default_factory=dict)
    has_negative_cycle: bool = False


def bellman_ford(graph: Graph, source: int) -> BellmanFordResult:
    """Run Bellman-Ford from *source* using each edge's ``final_weight``.

    Returns a :class:`BellmanFordResult` with shortest distances,
    predecessor pointers, and a negative-cycle flag.
    """
    dist: dict[int, float] = {nid: math.inf for nid in graph.nodes}
    predecessor: dict[int, int | None] = {nid: None for nid in graph.nodes}
    dist[source] = 0.0

    num_nodes = graph.get_node_count()

    # Relax all edges |V| - 1 times
    for _ in range(num_nodes - 1):
        for edge in graph.edges:
            assert edge.final_weight is not None
            if dist[edge.from_id] + edge.final_weight < dist[edge.to_id]:
                dist[edge.to_id] = dist[edge.from_id] + edge.final_weight
                predecessor[edge.to_id] = edge.from_id

    # Check for negative-weight cycles (one more pass)
    has_negative_cycle = False
    for edge in graph.edges:
        assert edge.final_weight is not None
        if dist[edge.from_id] + edge.final_weight < dist[edge.to_id]:
            has_negative_cycle = True
            break

    return BellmanFordResult(
        source=source,
        dist=dist,
        predecessor=predecessor,
        has_negative_cycle=has_negative_cycle,
    )


def reconstruct_path(
    result: BellmanFordResult, source: int, dest: int
) -> list[int]:
    """Trace the predecessor map to build an ordered path ``[source, ..., dest]``.

    Returns an empty list if *dest* is unreachable.
    Raises :class:`ValueError` if a negative cycle was detected.
    """
    if result.has_negative_cycle:
        raise ValueError(
            "Negative cycle detected — shortest paths are undefined."
        )

    if math.isinf(result.dist.get(dest, math.inf)):
        return []

    path: list[int] = []
    current: int | None = dest
    while current is not None:
        path.append(current)
        if current == source:
            break
        current = result.predecessor.get(current)
    else:
        # source was never reached — dest is unreachable
        return []

    path.reverse()
    return path
