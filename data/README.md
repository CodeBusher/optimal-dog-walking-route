# Data Guide

This folder contains all graph data for the Optimal Dog Walking Route project.

## Folder Structure

```
data/
├── sample_data.json          ← original 5-node example (default in app)
├── sample_data/              ← hand-crafted scenarios
│   ├── urban_downtown.json             20 nodes, 31 edges — dense city block
│   ├── suburban_park_district.json     20 nodes, 30 edges — quiet suburb with parks/trails
│   └── large_city_loop.json            30 nodes, 55 edges — mixed urban + suburban
└── README.md                 ← this file
```

---

## JSON Schema

Every JSON file must have two top-level arrays: `nodes` and `edges`.

### Node fields

| Field       | Type   | Required | Description                                                  |
|-------------|--------|----------|--------------------------------------------------------------|
| `node_id`   | int    | yes      | Unique identifier, sequential from 0                        |
| `name`      | string | yes      | Human-readable place name                                    |
| `node_type` | string | yes      | See node types table below                                   |
| `reward`    | float  | yes      | −10 (worst) to 10 (best). See reward scale below            |
| `x`         | float  | yes      | Spatial x-coordinate for map visualisation                  |
| `y`         | float  | yes      | Spatial y-coordinate for map visualisation                  |

### Edge fields

| Field         | Type  | Required | Description                                          |
|---------------|-------|----------|------------------------------------------------------|
| `from_id`     | int   | yes      | Source node_id                                       |
| `to_id`       | int   | yes      | Destination node_id                                  |
| `time_cost`   | float | yes      | Walking time in minutes (>= 0)                       |
| `edge_reward` | float | yes      | Path-level reward (−10 to 10)                        |

> **Do NOT include `final_weight` in JSON files.** It is computed automatically
> by `Graph.add_edge` using: `final_weight = time_cost - edge_reward - dest_node.reward`

---

## Node Types

| node_type      | Description                        | Typical reward |
|----------------|------------------------------------|----------------|
| `home`         | Starting/ending point              | 0              |
| `park`         | Green space, dog-friendly area     | 5–10           |
| `trail`        | Walking path, scenic route         | 3–8            |
| `rest_stop`    | Bench, café, water fountain        | 2–5            |
| `intersection` | Street crossing, neutral location  | 0              |
| `trigger_zone` | Construction, heavy traffic        | −10            |

## Reward Scale

| Score   | Meaning         | Examples                           |
|---------|-----------------|------------------------------------|
| −10     | Trigger zone    | Construction site, heavy traffic   |
| 0       | Neutral         | Ordinary sidewalk, intersection    |
| 1–4     | Mildly pleasant | Quiet street, shaded path, café    |
| 5–7     | Good            | Grass area, gentle trail           |
| 8–10    | Excellent       | Off-leash park, dog water fountain |

---

## How to Load a Dataset

### In the Streamlit app
Two options in the sidebar:
- **Sample data** — select from a dropdown that auto-discovers all `.json` files in `data/` and `data/sample_data/`. Default is `sample_data`.
- **Upload JSON** — upload any `.json` file that follows the schema above.

### Programmatically
```python
from src.graph import Graph

g = Graph()
g.load_from_json("data/sample_data/urban_downtown.json")

print(g.get_node_count())   # 20
print(g.get_edge_count())   # 32
```

---

## How to Add a New Dataset

1. Create a new `.json` file under `data/sample_data/`
2. Follow the schema above. Use sequential `node_id` values starting from 0.
3. Make sure every `from_id` and `to_id` in edges references a valid `node_id`.
4. Do **not** include `final_weight` — it will be computed by the code.

### Naming convention
- Use lowercase with underscores: `neighborhood_name.json`

---

## Phase 2 Notes

**1. Per-dog reward customization**
Allow users to override node/edge rewards based on their dog's individual
preferences (e.g. a dog that dislikes dog parks). Requires a new
`update_node` method in `src/graph.py` and UI inputs in `app.py`.
The JSON schema will remain unchanged.

**2. Real location graph generation**
Allow users to generate a walking graph from a real-world address using
OpenStreetMap data (`osmnx`). The app would fetch the street network and
nearby POIs (parks, cafes, trails) around the entered location and convert
them into the existing JSON schema automatically, without saving any files.
