# Optimal Dog Walking Route

A graph-based route optimization tool that computes the most rewarding dog-walking route by balancing travel time with environmental rewards (parks, trails, rest stops) while penalizing trigger zones (construction, heavy traffic).

## Motivation

Traditional navigation apps optimize for shortest distance or time. But for dog owners, the quality of a walk depends on sensory enrichment — parks, quiet trails, sniffing spots — and on avoiding stressors like construction noise or busy intersections. This project models the "most rewarding route" as a shortest-path problem using the Bellman-Ford algorithm, where rewards are represented as negative edge weights.

## How It Works

The walking environment is modeled as a **weighted directed graph**:

- **Nodes** represent locations (home, parks, intersections, rest stops, trigger zones)
- **Edges** represent walkable paths between locations
- **Edge weights** combine travel time and rewards into a single cost:

```
edge.final_weight = time_cost - edge_reward - destination_node_reward
```

A lower (or more negative) `final_weight` means a more desirable path. The **Bellman-Ford algorithm** finds the path with the lowest total weight from a given start point, effectively maximizing the walking experience while keeping travel time reasonable.

### Reward Scale

| Score | Meaning | Examples |
|-------|---------|---------|
| -10 | Trigger zone | Construction site, heavy traffic |
| 0 | Neutral | Ordinary sidewalk |
| 1–4 | Mildly pleasant | Quiet street, shaded path |
| 5–7 | Good | Grass area, gentle trail |
| 8–10 | Excellent | Off-leash park, dog water fountain |

## Project Structure

```
optimal-dog-walking-route/
├── README.md
├── data/
│   └── sample_data.json        # Node and edge data (JSON)
├── src/
│   ├── models.py               # Node, Edge dataclasses
│   ├── graph.py                # Graph class (adjacency list, JSON loader)
│   └── bellman_ford.py         # Algorithm + path reconstruction
└── tests/
    ├── test_graph.py           # Graph construction and loading tests
    ├── test_bellman_ford.py    # Algorithm correctness tests
    └── test_integration.py     # End-to-end tests with real data
```

## Input Data Format

The system reads a JSON file with the following schema:

```json
{
  "nodes": [
    {
      "node_id": 0,
      "name": "Home",
      "node_type": "home",
      "reward": 0
    },
    {
      "node_id": 1,
      "name": "Elm Park",
      "node_type": "park",
      "reward": 8
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
```

### Node Types

`home`, `park`, `intersection`, `rest_stop`, `trigger_zone`, `trail`

## Usage

```python
from src.graph import Graph
from src.bellman_ford import bellman_ford, reconstruct_path

# Load graph from data file
g = Graph()
g.load_from_json("data/sample_data.json")

# Compute best routes from home (node 0)
result = bellman_ford(g, source=0)

# Get the optimal path to a destination
path = reconstruct_path(result, source=0, dest=4)
print(f"Best route: {path}")
print(f"Total cost: {result.dist[4]}")
```

## Running Tests

```bash
pytest tests/ -v
```

## Connection to Course Topics

This project applies graph representations and shortest-path algorithms. The walking environment is modeled as a weighted directed graph, and the Bellman-Ford algorithm computes the optimal route while handling negative edge weights (rewards) and detecting negative cycles.

## License

This project is for academic use as part of coursework.