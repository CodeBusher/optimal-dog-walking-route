# Design Specification

## Design Decisions

- **Input format:** JSON (`data/sample_data.json`)
- **Trigger zones:** Modeled as nodes with a heavy penalty (`reward = -10`)
- **Reward scale:** −10 to 10

| Score | Meaning | Examples |
|-------|---------|---------|
| -10 | Trigger zone | Construction site, heavy traffic |
| 0 | Neutral | Ordinary sidewalk |
| 1–4 | Mildly pleasant | Quiet street, shaded path |
| 5–7 | Good | Grass area, gentle trail |
| 8–10 | Excellent | Off-leash park, dog water fountain |

- **Mutability:** Phase 1 is build-once (load from JSON, run algorithm). Phase 2 will add `update_node` and `update_edge` methods with automatic `final_weight` recomputation for affected edges.
- **Weight formula:** lower = better route

```
final_weight = time_cost - edge_reward - destination_node_reward
```

---

## 1. Data Models (`src/models.py`)

```python
@dataclass
class Node:
    node_id: int
    name: str
    node_type: str          # "home", "park", "intersection",
                            # "rest_stop", "trigger_zone", "trail"
    reward: float = 0.0     # node-level reward applied to ALL edges
                            # entering this node
                            # -10 for trigger zones, 0-10 for others


@dataclass
class Edge:
    from_id: int
    to_id: int
    time_cost: float              # walking time in minutes (>= 0)
    edge_reward: float            # edge-specific reward (-10 to 10)
    final_weight: float | None = None  # computed by Graph.add_edge
```

---

## 2. Graph (`src/graph.py`)

```python
class Graph:
    """Weighted directed graph stored as an adjacency list."""

    def __init__(self):
        self.nodes: dict[int, Node] = {}
        self.edges: list[Edge] = []
        self.adj: dict[int, list[Edge]] = {}

    def add_node(self, node: Node) -> None:
        """Register a location in the graph."""
        ...

    def add_edge(self, edge: Edge) -> None:
        """
        Add a directed, weighted connection.
        Computes and sets edge.final_weight to include the
        destination node's reward:

        edge.final_weight = edge.time_cost - edge.edge_reward - dest_node.reward
        """
        ...

    def load_from_json(self, filepath: str) -> None:
        """
        Load graph from a JSON file.

        Expected schema — see data/sample_data.json:
        {
          "nodes": [
            {
              "node_id": 0,
              "name": "Home",
              "node_type": "home",
              "reward": 0
            }
          ],
          "edges": [
            {
              "from_id": 0,
              "to_id": 1,
              "time_cost": 6.0,
              "edge_reward": 1.0
            }
          ]
        }
        """
        ...

    def get_node_count(self) -> int:
        ...

    def get_edge_count(self) -> int:
        ...
```

---

## 3. Bellman-Ford Algorithm (`src/bellman_ford.py`)

```python
@dataclass
class BellmanFordResult:
    source: int
    dist: dict[int, float]              # node_id -> best distance from source
    predecessor: dict[int, int | None]  # node_id -> previous node on best path
    has_negative_cycle: bool


def bellman_ford(graph: Graph, source: int) -> BellmanFordResult:
    """
    Run Bellman-Ford from `source` using each edge's
    final_weight (which already includes node rewards).

    Returns BellmanFordResult with distances, predecessors,
    and negative-cycle flag.
    """
    ...


def reconstruct_path(
    result: BellmanFordResult, source: int, dest: int
) -> list[int]:
    """
    Trace predecessor map to build ordered path [source, ..., dest].
    Returns empty list if dest is unreachable.
    Raises ValueError if a negative cycle affects the path.
    """
    ...
```

---

## 4. Sample Test Case

```python
def _build_sample_graph() -> Graph:
    """
    A 5-node graph for hand-verified tests.

    Nodes:
      0  Home            (reward  0)
      1  Main St         (reward  0)   intersection
      2  Elm Park        (reward  8)   park — great for dogs
      3  Construction    (reward -10)  trigger zone
      4  Dog Café        (reward  2)   rest stop

    Edges (from -> to, time_cost, edge_reward):
      0 -> 1   3 min,  reward 0    net = 3 - 0 - 0  =  3
      0 -> 2   6 min,  reward 1    net = 6 - 1 - 8  = -3  (park!)
      1 -> 3   2 min,  reward 0    net = 2 - 0 -(-10)= 12  (penalty!)
      1 -> 4   5 min,  reward 0    net = 5 - 0 - 2  =  3
      2 -> 4   4 min,  reward 1    net = 4 - 1 - 2  =  1
      3 -> 4   1 min,  reward 0    net = 1 - 0 - 2  = -1

    Best path 0 → 4:
      0 → 2 → 4 :  -3 + 1 = -2  ← winner (park reward dominates)
      0 → 1 → 4 :   3 + 3 =  6
      0 → 1 → 3 → 4: 3 + 12 + (-1) = 14  (trigger zone kills it)
    """
    g = Graph()
    g.add_node(Node(0, "Home",          "home",         reward=0))
    g.add_node(Node(1, "Main St",       "intersection", reward=0))
    g.add_node(Node(2, "Elm Park",      "park",         reward=8))
    g.add_node(Node(3, "Construction",  "trigger_zone", reward=-10))
    g.add_node(Node(4, "Dog Café",      "rest_stop",    reward=2))

    g.add_edge(Edge(0, 1, time_cost=3, edge_reward=0))
    g.add_edge(Edge(0, 2, time_cost=6, edge_reward=1))
    g.add_edge(Edge(1, 3, time_cost=2, edge_reward=0))
    g.add_edge(Edge(1, 4, time_cost=5, edge_reward=0))
    g.add_edge(Edge(2, 4, time_cost=4, edge_reward=1))
    g.add_edge(Edge(3, 4, time_cost=1, edge_reward=0))
    return g
```

### Expected Results

For `_build_sample_graph()` with `source=0`, `dest=4`:

| Key | Value |
|-----|-------|
| `dist[4]` | `-2` |
| `reconstruct_path` | `[0, 2, 4]` |
| `has_negative_cycle` | `False` |
